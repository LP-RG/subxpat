"""Patterns (structure) and logics (weights) for the labelling.

The two concepts are deliberately separate:

* a **pattern** answers "is this node part of shape X, and which neighbours play which roles?".
  It never looks at weights and never does arithmetic; it returns a `Match` (role -> node name)
  plus whatever structural facts the logic needs.
* a **logic** says "given the weights of the slots I read, I can fill the slots I write", optionally
  guarded by a threshold derived from `et`. It never walks the graph.

The driver (`schedule`) runs two passes: it collects every match once (structure pass, O(n) per
pattern) and then schedules the logics by *dependency* rather than topological position, so a logic
may read predecessors, successors or both. Exact logics are applied first; the remaining (bound)
ones are combined by keeping the tightest value that is still safe for the labelling column in use
(`min` labels, `max` labels).

Bounds, per column (the part that is easy to get wrong):

    breaking n makes its successor range over a subset of what breaking the successor does,
    therefore      w_max(n) <= w_max(succ)      -> the successor's weight is an *upper* bound for max
                   w_min(n) >= w_min(succ)      -> it is a *lower* bound for min

so "copy the successor's weight" is conservative for `max` and optimistic for `min`, and the same
asymmetry decides how the candidates are combined.

The structural bounds need no labels at all and are computed once per circuit in O(n):

    simple_max(n) = sum of 2**i over the outputs reachable from n   (>= any achievable error)
    simple_min(n) = min of 2**i over the outputs reachable from n   (<= the smallest achievable error)

`simple_max` is an upper bound for both columns; `simple_min` is a lower bound for both. The max
column uses `min(simple_max, sum of the successors' weights)`, the min column uses `simple_min`
only: the sum of *min* weights is not an upper bound for the min column (two successors of weight 1
around a gate whose true min is 4 give a sum of 2), so it is not offered there.
"""
from __future__ import annotations

import dataclasses as dc
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

__all__ = [
    'Match', 'PATTERNS', 'single_successor', 'output_driver', 'any_node', 'with_successors',
    'Logic', 'LOGICS', 'simple_not', 'output_driver_logic', 'single_successor_bound',
    'bound_max', 'bound_min', 'bound_sum', 'RULE_NAMES', 'RuleConfig', 'config_for_level',
    'structural_bounds', 'combine', 'schedule', 'Stats',
]

MIN = 'min'
MAX = 'max'

# kind of the value a logic produces, per labelling column
EXACT = 'exact'          # equal to the true weight
UPPER = 'upper'          # >= the true weight (safe substitute: node can only look worse)
LOWER = 'lower'          # <= the true weight (optimistic, only a last resort)


@dc.dataclass(frozen=True)
class Match:
    pattern: str
    slots: Mapping[str, str]
    data: Mapping[str, Any] = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class Context:
    """What a logic may need besides the weights: the threshold, the column, and the structural
    bounds the driver precomputes once per circuit (`simple_max` = OR of the reachable output
    bits, `simple_min` = the smallest reachable output bit)."""
    et: int
    column: str
    simple_max: Mapping[str, int] = dc.field(default_factory=dict)
    simple_min: Mapping[str, int] = dc.field(default_factory=dict)


# ---------------------------------------------------------------- patterns

def single_successor(g, n: str) -> Optional[Match]:
    """`n` feeds exactly one node.

    The interesting distinction is whether that successor is a one-input gate (NOT/Identity):
    then breaking `n` and breaking the successor free the same cone and the weights are equal
    (`SimpleNot`); otherwise only the bound relation holds.
    """
    suc = g.successors(n)
    if len(suc) != 1:
        return None
    return Match('single_successor', {'node': n, 'succ': suc[0]},
                 {'succ_is_1input': len(g.predecessors(suc[0])) == 1})


def output_driver(g, n: str) -> Optional[Match]:
    """Every consumer of `n` is an output: its weight is the sum of those output-bit weights."""
    suc = g.successors(n)
    if not suc or any(s not in g.outputs for s in suc):
        return None
    return Match('output_driver', {'node': n}, {'bits': [g.output_index(s) for s in suc]})


def any_node(g, n: str) -> Optional[Match]:
    """Every node: the structural bounds are positional, they need no neighbour."""
    return Match('any_node', {'node': n})


def with_successors(g, n: str) -> Optional[Match]:
    """`n` has at least one consumer; leaves the whole successor list to the logic."""
    suc = g.successors(n)
    if not suc:
        return None
    return Match('with_successors', {'node': n, 'succ': suc[0]}, {'succs': suc})


PATTERNS: Mapping[str, Callable] = {
    'single_successor': single_successor,
    'output_driver': output_driver,
    'any_node': any_node,
    'with_successors': with_successors,
}


# ---------------------------------------------------------------- logics

@dc.dataclass(frozen=True)
class Logic:
    name: str
    pattern: str
    reads: Tuple[str, ...]
    writes: Tuple[str, ...]
    kinds: Mapping[str, str]                      # column -> EXACT | UPPER | LOWER
    divisor: Optional[int] = None                 # None = ungated, 0 = disabled, N = value*N <= et
    requires: Optional[str] = None                # extra structural predicate on the match data
    reads_list: Optional[str] = None              # match-data key holding every slot that must be known
    value: Optional[Callable[[Match, Mapping[str, int], Context], int]] = None

    def candidate(self, m: Match, weights: Mapping[str, int], ctx: Context) -> Optional[int]:
        """The value this logic would write, or None if it cannot apply here.

        Covers everything that can stop it: a structural predicate, a missing weight among the
        nodes it reads, a structural bound that does not exist for this node (it reaches no
        output), and the threshold gate `value * divisor <= et`.
        """
        if self.requires is not None and not m.data.get(self.requires):
            return None
        if any(m.slots[r] not in weights for r in self.reads):
            return None
        if self.reads_list is not None and any(x not in weights for x in m.data[self.reads_list]):
            return None
        try:
            value = self.evaluate(m, weights, ctx)
        except KeyError:                       # structural bound absent (node reaches no output)
            return None
        if self.divisor and value * self.divisor > ctx.et:
            return None
        return value

    def evaluate(self, m: Match, weights: Mapping[str, int], ctx: Context) -> int:
        if self.value is not None:
            return self.value(m, weights, ctx)
        assert len(self.reads) == 1, f'{self.name}: give it an explicit value function'
        return weights[m.slots[self.reads[0]]]

    def fill(self, m: Match, weights: Mapping[str, int], ctx: Context) -> Dict[str, int]:
        v = self.evaluate(m, weights, ctx)
        return {m.slots[w]: v for w in self.writes}


simple_not = Logic(
    name='simple_not', pattern='single_successor',
    reads=('succ',), writes=('node',),
    kinds={MIN: EXACT, MAX: EXACT},
    requires='succ_is_1input',
)

output_driver_logic = Logic(
    name='output_driver', pattern='output_driver',
    reads=(), writes=('node',),
    # exact: the node's error is the error of the output(s) it drives, and the output's own
    # weight is known (2**i relative to the current circuit, computed relative to the origin)
    kinds={MIN: EXACT, MAX: EXACT},
    value=lambda m, w, c: sum(1 << b for b in m.data['bits']),
)

single_successor_bound = Logic(
    name='single_successor', pattern='single_successor',
    reads=('succ',), writes=('node',),
    kinds={MIN: LOWER, MAX: UPPER},
    divisor=0,                                   # gated: set per level / per flag
)

bound_max = Logic(
    name='bound_max', pattern='any_node',
    reads=(), writes=('node',),
    kinds={MIN: UPPER, MAX: UPPER},
    divisor=0,
    value=lambda m, w, c: c.simple_max[m.slots['node']],
)

bound_min = Logic(
    name='bound_min', pattern='any_node',
    reads=(), writes=('node',),
    # a lower bound in BOTH columns, and the only structural rule the min column uses: the true
    # min is at least the smallest reachable bit, so keeping it is exactly `simple_min`'s optimism
    kinds={MIN: LOWER, MAX: LOWER},
    divisor=0,
    value=lambda m, w, c: c.simple_min[m.slots['node']],
)

bound_sum = Logic(
    name='bound_sum', pattern='with_successors',
    reads=(), writes=('node',),
    kinds={MIN: UPPER, MAX: UPPER},
    divisor=0,
    reads_list='succs',
    value=lambda m, w, c: sum(w[s] for s in m.data['succs']),
)

LOGICS: Mapping[str, Logic] = {
    lg.name: lg for lg in (simple_not, output_driver_logic, single_successor_bound,
                           bound_max, bound_min, bound_sum)
}


# ---------------------------------------------------------------- structural bounds

def structural_bounds(graph, nodes: Sequence[str]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """`(simple_max, simple_min)` for every node, in one reverse-topological pass, no labels.

    An output `i` has both bounds `2**i`; every other node takes the union (sum) of its successors
    for `simple_max` and the minimum of them for `simple_min`.
    """
    # `reach` is a MASK over output indices (bit i set = output i is reachable), so shared cones are
    # counted once: summing the successors' already-summed weights would count an output once per
    # path and inflate the bound (measured: 2826 against a true 15 on sad_i10_o4).
    reach: Dict[str, int] = {}
    simple_max: Dict[str, int] = {}
    simple_min: Dict[str, int] = {}
    for n in nodes:                    # successors first, as passed in
        mask = 0
        for s in graph.successors(n):
            mask |= reach.get(s, 0)
        if n in graph.outputs:
            mask |= 1 << graph.output_index(n)
        if not mask:
            continue
        reach[n] = mask
        simple_max[n] = sum(1 << i for i in range(mask.bit_length()) if mask >> i & 1)
        simple_min[n] = 1 << (mask & -mask).bit_length() - 1
    return simple_max, simple_min


# ---------------------------------------------------------------- levels

#: one divisor per rule, each independently settable: None = ungated, 0 = disabled,
#: N = the rule may fire when `value * N <= et`. The level only fills in defaults.
RULE_NAMES = ('simple_not', 'output_driver', 'single_successor', 'bound_max', 'bound_min', 'bound_sum')


@dc.dataclass(frozen=True)
class RuleConfig:
    simple_not: Optional[int] = 0
    output_driver: Optional[int] = 0
    single_successor: Optional[int] = 0
    bound_max: Optional[int] = 0
    bound_min: Optional[int] = 0
    bound_sum: Optional[int] = 0

    def items(self) -> Iterable[Logic]:
        for name in RULE_NAMES:
            divisor = getattr(self, name)
            if divisor != 0:
                # The per-run divisor must reach the logic instance: `Logic.divisor` is 0 on the
                # shared definition, so without this copy every rule comes out ungated.
                yield dc.replace(LOGICS[name], divisor=divisor)

    def with_overrides(self, **overrides) -> 'RuleConfig':
        known = {k: v for (k, v) in overrides.items() if k in RULE_NAMES}
        unknown = set(overrides) - set(known)
        if unknown:
            raise ValueError(f'unknown labelling rule(s): {sorted(unknown)}')
        return dc.replace(self, **known)


#: the preset ladder, shared by both columns except for the bound rung: the max column bounds with
#: `min(simple_max, sum of successors)`, the min column with `simple_min` only.
_BOUND_RUNG = {MAX: ('bound_max', 'bound_sum'), MIN: ('bound_min',)}

_LADDER = {
    10: {},
    20: {'simple_not': None},
    30: {'simple_not': None, 'output_driver': None},
    40: {'single_successor': 1000},
    50: {'single_successor': 1000, 'bound': 1000},
    60: {'single_successor': 100, 'bound': 1000},
    70: {'single_successor': 10, 'bound': 100},
    80: {'single_successor': 2, 'bound': 10},
    90: {'single_successor': 1, 'bound': 2},
    100: {},                                     # simple_min / simple_max: no solving, no logics
}


def config_for_level(level: int, column: str = MAX) -> RuleConfig:
    """The preset ladder for one column, as a `RuleConfig`."""
    if level not in _LADDER:
        raise ValueError(f'unknown labelling level {level!r}; known: {sorted(_LADDER)}')
    if column not in _BOUND_RUNG:
        raise ValueError(f'unknown labelling column {column!r}; expected {MIN!r} or {MAX!r}')
    rules: Dict[str, Optional[int]] = {}
    for name, divisor in _LADDER[level].items():
        if name == 'bound':
            for real in _BOUND_RUNG[column]:
                rules[real] = divisor
        else:
            rules[name] = divisor
    return RuleConfig(**rules)


def logics_for_level(level: int, column: str = MAX) -> List[Logic]:
    """The logics a preset enables, exact ones first."""
    return list(config_for_level(level, column).items())


# ---------------------------------------------------------------- combining

def combine(candidates: Sequence[Logic], matches: Mapping[str, Match], column: str,
            weights: Mapping[str, int], ctx: Context) -> Tuple[Optional[int], str, Optional[str]]:
    """Pick the value for one node out of its applicable candidates.

    Exact candidates win (first one, in the fixed order of `candidates`). Otherwise take the
    tightest candidate that is *safe* for this column -- for an upper bound that is the minimum;
    a lower-bound candidate is only used when no upper-bound one applies, and the caller should
    record that the node's weight is optimistic.

    Returns (value, kind, rule name) where kind is EXACT / UPPER / LOWER / 'none'.
    """
    applicable = [(lg, lg.candidate(matches[lg.name], weights, ctx)) for lg in candidates]
    applicable = [(lg, value) for (lg, value) in applicable if value is not None]
    for (lg, value) in applicable:
        if lg.kinds[column] == EXACT:
            return value, EXACT, lg.name
    uppers = [(value, lg.name) for (lg, value) in applicable if lg.kinds[column] == UPPER]
    if uppers:
        value, name = min(uppers)
        return value, UPPER, name
    # A lower bound is a substitute that sits BELOW the truth, so the tightest one is the largest:
    # picking the smallest would just be the most optimistic of them.
    lowers = [(value, lg.name) for (lg, value) in applicable if lg.kinds[column] == LOWER]
    if lowers:
        value, name = max(lowers)
        return value, LOWER, name
    return None, 'none', None


# ---------------------------------------------------------------- driver

@dc.dataclass
class Stats:
    derived: Dict[str, int] = dc.field(default_factory=dict)
    solved: int = 0
    by_rule: Dict[str, int] = dc.field(default_factory=dict)

    def record(self, kind: str, rule: Optional[str] = None) -> None:
        self.derived[kind] = self.derived.get(kind, 0) + 1
        if rule is not None:
            self.by_rule[rule] = self.by_rule.get(rule, 0) + 1

    def summary(self) -> str:
        parts = [f'{k}={v}' for (k, v) in sorted(self.derived.items())]
        rules = ', '.join(f'{k}:{v}' for (k, v) in sorted(self.by_rule.items()))
        return (f'derived[{", ".join(parts)}] solved={self.solved}'
                + (f' by_rule[{rules}]' if rules else ''))


def schedule(nodes: Sequence[str], match, *, column: str, et: int, config: RuleConfig,
             simple_max: Mapping[str, int], simple_min: Mapping[str, int],
             seeds: Mapping[str, int], solve: Callable[[str], int],
             relevant: Optional[set] = None) -> Tuple[Dict[str, int], Stats]:
    """Two passes: collect every match once, then schedule the logics and the solver calls.

    :param nodes: node names in REVERSE topological order (successors first).
    :param match: `match(pattern_name, node) -> Match | None`, already bound to the graph.
    :param seeds: weights known before labelling (the outputs, `2**i` relative to the current circuit).
    :param solve: called for a node that no logic can fill; it must return the exact weight.
    :param relevant: if given, only these nodes are labelled (the `et` reachability pruning).
    """
    ctx = Context(et=et, column=column, simple_max=simple_max, simple_min=simple_min)
    logics = list(config.items())

    # --- structure pass: every match, once, indexed by the node it would write
    by_write: Dict[str, List[Logic]] = {}
    matches: Dict[Tuple[str, str], Match] = {}
    for node in nodes:
        for lg in logics:
            key = (lg.name, node)
            m = match(lg.pattern, node)
            if m is None:
                continue
            matches[key] = m
            by_write.setdefault(m.slots[lg.writes[0]], []).append(lg)

    weights: Dict[str, int] = dict(seeds)
    stats = Stats()
    pending = [n for n in nodes if n not in weights and (relevant is None or n in relevant)]

    def candidates_of(node: str) -> List[Logic]:
        order = {lg.name: i for (i, lg) in enumerate(logics)}
        return sorted(by_write.get(node, ()), key=lambda lg: order[lg.name])

    def derive_round() -> bool:
        progressed = False
        for node in pending:
            if node in weights:
                continue
            cands = candidates_of(node)
            if not cands:
                continue
            value, kind, rule = combine(
                cands, {lg.name: matches[(lg.name, node)] for lg in cands},
                column, weights, ctx)
            if value is None:
                continue
            weights[node] = value
            stats.record(kind, rule)
            progressed = True
        return progressed

    # --- weight pass: derive what the logics allow, solve the rest (in the canonical order)
    while derive_round():
        pass
    for node in pending:
        if node in weights:
            continue
        weights[node] = solve(node)
        stats.solved += 1
        while derive_round():      # a new weight can unlock derivations in either direction
            pass
    return weights, stats