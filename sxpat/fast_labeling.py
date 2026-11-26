import random
from typing import Callable, Dict, Mapping, Optional, Sequence

import networkx as nx

from sxpat.graph.graph import IOGraph
from sxpat.graph.node import (
    And, BoolConstant, BoolVariable, Identity, Implies, Not, Or, Xnor, Xor,
)
from sxpat.specifications import LabelingRelativeTo, LabelingType, Specifications
from sxpat.labelling import patterns as patterns_engine
from sxpat.labelling.labelling import Labelling


def evaluate_samples(graph: IOGraph, input_masks: Mapping[str, int], n_samples: int,
                     flip_name: Optional[str] = None) -> Dict[str, int]:
    """
    Evaluate `graph` once per sample, all in parallel.

    Every node value is returned as a bitmask, where bit `s` is the value of the
    node under sample `s`; boolean operations then map to bitwise operations.
    If `flip_name` is given, that node's value is negated before being stored, so
    its whole downstream cone sees the flipped value (a broken node).
    """
    all_ones = (1 << n_samples) - 1

    values: Dict[str, int] = {}
    for node in graph.nodes:  # topological order
        if isinstance(node, BoolVariable):
            value = input_masks.get(node.name, 0)
        elif isinstance(node, BoolConstant):
            value = all_ones if node.value else 0
        elif isinstance(node, Not):
            value = ~values[node.operands[0]]
        elif isinstance(node, And):
            value = all_ones
            for operand in node.operands: value &= values[operand]
        elif isinstance(node, Or):
            value = 0
            for operand in node.operands: value |= values[operand]
        elif isinstance(node, Xor):
            value = 0
            for operand in node.operands: value ^= values[operand]
        elif isinstance(node, Xnor):
            value = all_ones
            for operand in node.operands: value ^= values[operand]
        elif isinstance(node, Implies):
            (antecedent, consequent) = node.operands
            value = ~(values[antecedent] & ~values[consequent])
        elif isinstance(node, Identity):
            value = values[node.operands[0]]
        else:
            raise ValueError(f'Cannot evaluate node of unsupported type: {type(node).__name__} ({node.name!r})')

        values[node.name] = (~value if node.name == flip_name else value) & all_ones

    return values


def sample_outputs(values: Mapping[str, int], outputs_names: Sequence[str], n_samples: int) -> list[int]:
    """Decode per-node values into the integer output value of each sample (as `ToInt` would)."""
    outputs = [0] * n_samples
    for name in outputs_names:
        bit_weight = 1 << int(name[3:])
        mask = values[name]
        for sample in range(n_samples):
            if (mask >> sample) & 1:
                outputs[sample] += bit_weight
    return outputs


class SamplingLabeler:
    """
    Label nodes by sampling.

    The weight of a node is the maximum (or minimum) absolute difference between
    the integer outputs of the reference circuit and of the current circuit with
    the node broken, over a set of input assignments.

    Mirroring the exact labelling, the minimising variant ignores the assignments
    under which the break has no effect (a zero weight carries no information),
    so it returns the smallest non-zero difference.

    The two corners (all-zero and all-one) are always evaluated; `n_samples`
    further assignments are drawn uniformly at random, without replacement. The
    sampling is deterministic for a given seed (`None` draws a non-deterministic
    seed), and exact whenever `n_samples` covers every assignment.
    """

    def __init__(self, reference_graph: IOGraph, current_graph: IOGraph,
                 n_samples: int, seed: Optional[int], minimise: bool = False) -> None:
        self.reference_graph = reference_graph
        self.current_graph = current_graph
        self.n_samples = max(1, n_samples)
        self.minimise = minimise
        self._random = random.Random(seed)
        self._weights: Dict[str, int] = {}
        # lazily computed (they only depend on the graphs, not on the node)
        self._reference_outputs: Optional[list[int]] = None
        self._input_masks: Mapping[str, int] = {}

    def label_node(self, cur_node: str) -> int:
        if cur_node not in self._weights:
            self._weights[cur_node] = self._label(cur_node)
        return self._weights[cur_node]

    def _assignments(self, n_inputs: int) -> list[int]:
        # assignments of the inputs, encoded as integers (bit `i` -> `inputs[i]`)
        total = 1 << n_inputs
        if total <= 2:
            # the corners already cover every assignment
            return list(range(total))
        if self.n_samples >= total - 2:
            # the sample budget covers every assignment: enumerate exactly
            return list(range(total))
        return [0, total - 1, *self._random.sample(range(1, total - 1), self.n_samples)]

    def _prepare(self) -> int:
        if self._reference_outputs is not None:
            return len(self._reference_outputs)

        inputs_names = self.current_graph.inputs_names
        assignments = self._assignments(len(inputs_names))
        n_samples = len(assignments)

        # transpose the assignments into a per-input bitmask (bit `s` -> sample `s`)
        input_masks = {name: 0 for name in inputs_names}
        for (sample, assignment) in enumerate(assignments):
            for (i, name) in enumerate(inputs_names):
                if (assignment >> i) & 1:
                    input_masks[name] |= 1 << sample

        self._input_masks = input_masks
        self._reference_outputs = sample_outputs(
            evaluate_samples(self.reference_graph, input_masks, n_samples),
            self.reference_graph.outputs_names, n_samples,
        )
        return n_samples

    def _label(self, cur_node: str) -> int:
        n_samples = self._prepare()

        broken = sample_outputs(
            evaluate_samples(self.current_graph, self._input_masks, n_samples, flip_name=cur_node),
            self.current_graph.outputs_names, n_samples,
        )

        errors = [abs(r - b) for (r, b) in zip(self._reference_outputs, broken)]
        if not self.minimise:
            return max(errors)
        # the minimising variant mirrors the exact labelling: the smallest non-zero error
        non_zero = [error for error in errors if error > 0]
        return min(non_zero) if non_zero else 0


def fast_labeling(
    exact_graph: IOGraph, current_graph: IOGraph, et: int, specs_obj: Specifications,
    skip_at_output: bool = True,
    threshold_for_max_imprecision: int = 10,
    skip_input: bool = True,
    weights: Optional[Mapping[str, int]] = None,
    labeller: Optional[Labelling] = None,
    sampler: Optional['SamplingLabeler'] = None,
) -> Dict[str, int]:
    """
    Compute the weights of the `current_graph` nodes, in relation to the `exact_graph`.

    Nodes are visited starting from the outputs and moving upwards; a node is only
    labelled when its own weight is needed, which is the case when its weight can
    still influence the error threshold `et`.

    :param skip_at_output: if `True`, nodes driving an output are not labelled, as
        their weight is exactly the output's weight.
    :param threshold_for_max_imprecision: controls the imprecise shortcut used to
        skip labelling. When a node's weight `w` satisfies `w <= et / threshold`,
        its ancestors that have it as their only child are assumed to have the same
        weight. This is an over-approximation, so a lower threshold is more accurate
        but slower; set to `0` to disable the shortcut entirely.
    :param skip_input: if `True`, input nodes are not labelled.
    :param weights: pre-computed weights to seed the labelling with.
    :param labeller: if given, weights are computed through this `Labelling`
        instead of an exact QBF query.
    :param sampler: if given, weights are computed by sampling instead of an exact
        QBF query (takes precedence over `labeller`).
    """
    weights = dict(weights) if weights is not None else {}
    stack: list[str] = []
    visited: set[str] = set()

    def propagate_imprecise_cases(start_node: str, value: int) -> None:
        # propagate `value` up through single-child ancestors, either because the
        # current weight is already negligible w.r.t. `et`, or because the ancestor
        # has no other children to influence it.
        st = [start_node]
        while len(st):
            cur_node = st.pop()
            imprecise = (
                threshold_for_max_imprecision != 0
                and value <= et / threshold_for_max_imprecision
            )
            single_child = (
                len(current_graph.predecessors(cur_node)) == 1
                and len(current_graph.successors(current_graph.predecessors(cur_node)[0])) == 1
            )
            if imprecise or single_child:
                for pred in current_graph.predecessors(cur_node):
                    if len(current_graph.successors(pred.name)) == 1:
                        weights[pred.name] = value
                        st.append(pred.name)

    minimum_found = 2 ** len(current_graph.outputs)

    # seed the exploration with the ancestors of the outputs that can affect `et`
    for node in reversed(current_graph.outputs):
        value = 2 ** int(node.name[3:])

        for x in current_graph.predecessors(node):
            if (value <= et) or specs_obj.labeling_relative_to == LabelingRelativeTo.ORIGIN:
                stack.append(x.name)
                visited.add(x.name)

    while len(stack):
        cur_node = stack.pop()
        if cur_node[:2] == 'in' and skip_input:
            continue
        # a constant is not a label: it has no weight of its own, and letting it into the map
        # poisons the running minimum below (a constant attached to an output used to read as 1)
        if isinstance(current_graph[cur_node], (BoolConstant, BoolVariable)):
            continue
        # a simple-min node driving an output alone cannot improve the minimum
        if (
            specs_obj.labeling == LabelingType.SIMPLE_MIN
            and current_graph.successors(cur_node)[0].name[:3] == 'out'
        ):
            output = current_graph.successors(cur_node)[0].name
            value = 2 ** int(output[3:])
            if value > minimum_found:
                return weights

        if cur_node in weights:
            for succ in current_graph.predecessors(cur_node):
                if succ.name not in visited:
                    stack.append(succ.name)
                    visited.add(succ.name)
            continue

        if (
            len(current_graph.successors(cur_node)) == 1
            and current_graph.successors(cur_node)[0] in current_graph.outputs
            and skip_at_output
        ):
            value = 2 ** int(current_graph.successors(cur_node)[0].name[3:])
        else:
            if sampler is not None:
                value = sampler.label_node(cur_node)
            else:
                assert labeller is not None
                value = labeller.label_node(cur_node)

        if not isinstance(current_graph[cur_node], (BoolConstant, BoolVariable)):
            minimum_found = min(minimum_found, value)
        weights[cur_node] = value

        propagate_imprecise_cases(cur_node, value)

        for succ in current_graph.predecessors(cur_node):
            if succ.name not in visited:
                stack.append(succ.name)
                visited.add(succ.name)


    return weights


def compute_bound(current_graph: IOGraph, combine: Callable[[int, int], int], init_value: int) -> Dict[str, int]:
    """
    Propagate a weight from the outputs towards the inputs, combining the values
    of every successor of a node with `combine`.
    """
    stack: list[str] = []
    weights: Dict[str, int] = {}
    # number of successors that have already reached each node; once it equals the
    # node's number of successors, the node itself can be processed
    count: Dict[str, int] = {}

    # initialize
    for x in current_graph.nodes:
        weights[x.name] = init_value
        count[x.name] = 0

    for node in current_graph.outputs:
        value = 2 ** int(node.name[3:])

        for x in current_graph.predecessors(node):
            count[x.name] += 1
            weights[x.name] = combine(value, weights[x.name])
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)

    while stack:
        cur_node = stack.pop()
        value = weights[cur_node]
        for x in current_graph.predecessors(cur_node):
            count[x.name] += 1
            weights[x.name] = combine(value, weights[x.name])
            if count[x.name] == len(current_graph.successors(x.name)):
                stack.append(x.name)

    return weights


def upper_bound(current_graph: IOGraph) -> Dict[str, int]:
    return compute_bound(current_graph, combine=lambda v, w: v | w, init_value=0)


def lower_bound(current_graph: IOGraph) -> Dict[str, int]:
    return compute_bound(current_graph, combine=min, init_value=2 ** len(current_graph.outputs))

class _GraphView:
    """What the pattern/logic engine needs from an `IOGraph`: names, neighbours, output index."""

    def __init__(self, graph: IOGraph):
        self._graph = graph
        self.outputs = {node.name for node in graph.outputs}

    def successors(self, name: str) -> Sequence[str]:
        return [node.name for node in self._graph.successors(name)]

    def predecessors(self, name: str) -> Sequence[str]:
        return [node.name for node in self._graph.predecessors(name)]

    def output_index(self, name: str) -> int:
        return int(name[3:])


def label_with_patterns(
    exact_graph: IOGraph,
    current_graph: IOGraph,
    et: int,
    specs_obj: Specifications,
    config: 'patterns_engine.RuleConfig',
    labeller: Optional[Labelling] = None,
    sampler: Optional['SamplingLabeler'] = None,
    skip_at_output: bool = True,
    skip_input: bool = True,
) -> Dict[str, int]:
    """Same contract as :func:`fast_labeling`, but the rules come from the pattern engine.

    A pattern recognises structure and a logic produces the weight; the engine collects every
    match once and then schedules the logics by dependency, so a solution that no logic can fill
    is the only one that reaches the solver (or the sampler). Which rules run, and at which
    threshold, is entirely `config` -- see :mod:`sxpat.labelling.patterns` for the ladder.
    """
    column = 'min' if specs_obj.labeling in (LabelingType.MIN, LabelingType.SAMPLE_MIN) else 'max'
    relative_to_origin = specs_obj.labeling_relative_to == LabelingRelativeTo.ORIGIN
    view = _GraphView(current_graph)

    order = list(nx.topological_sort(current_graph._inner))
    simple_max, simple_min = patterns_engine.structural_bounds(view, list(reversed(order)))
    seeds = {name: 2 ** int(name[3:]) for name in view.outputs}

    # the same pruning `fast_labeling` does: only the ancestors of the outputs that can still
    # matter for `et` are labelled at all
    relevant = set(seeds)
    for name in view.outputs:
        if relative_to_origin or 2 ** int(name[3:]) <= et:
            relevant |= nx.ancestors(current_graph._inner, name)
    # gates only. Inputs, outputs AND constants are not labelled: mode 6's own threshold excludes
    # all three when it takes `min_weight`, so a constant (or input) label of 1 would otherwise
    # become the running minimum the prune compares against and drop every gate above the smallest
    # bit -- which is what collapsed the labelled set to a single node at iteration 2.
    excluded = (
        set(current_graph.outputs_names)
        | set(current_graph.inputs_names)
        | {node.name for node in current_graph.constants}
    )
    relevant = {n for n in relevant if n not in excluded}

    # what inverting an output costs: `2**i` relative to the current circuit; relative to the
    # origin it has to be computed, and that is exactly the "invert this node's output" fault
    # Every label in the map is the FREE label, outputs included: the output becomes a fresh
    # boolean (its driver is ignored), which is exactly the freedom a cut gives it. The inverted
    # value is a different quantity -- one of the two values the free choice can take -- and using
    # it here is what made the copy across an output edge over-estimate the minimum.
    output_weights: Dict[int, int] = {}
    # relative to the previous circuit freeing an output costs exactly its bit (closed form);
    # relative to the origin it has to be labelled, and the answer is not `2**i` because the
    # deviation already present in the current circuit is part of it
    if labeller is not None and relative_to_origin:
        free_outputs = Labelling(
            exact_graph, current_graph, specs_obj,
            minimise=column == 'min', use_functions=True, fault=Labelling.FREE_OUTPUT_FAULT,
        )
        for name in view.outputs:
            output_weights[int(name[3:])] = free_outputs.label_node(name)
    else:
        output_weights = {int(name[3:]): 2 ** int(name[3:]) for name in view.outputs}
    specs_obj.outputs_weights = ({name: output_weights[int(name[3:])] for name in view.outputs}
                                 if relative_to_origin else None)
    # the seeds must agree with those weights: a rule copying from an output (SimpleNot on a node
    # whose only consumer is an output) would otherwise read the closed-form `2**i` and lose the
    # deviation the current circuit already carries relative to the origin
    seeds = {name: output_weights.get(int(name[3:]), 2 ** int(name[3:])) for name in view.outputs}

    def solve(name: str) -> int:
        # a node driving one output alone is exactly that output's bit, no query needed
        if skip_at_output:
            successors = view.successors(name)
            if len(successors) == 1 and successors[0] in view.outputs:
                return 2 ** int(successors[0][3:])
        if sampler is not None:
            return sampler.label_node(name)
        assert labeller is not None
        return labeller.label_node(name)

    weights, _ = patterns_engine.schedule(
        list(reversed(order)),
        lambda pattern, name: patterns_engine.PATTERNS[pattern](view, name),
        column=column, et=et, config=config,
        simple_max=simple_max, simple_min=simple_min,
        seeds=seeds, solve=solve, relevant=relevant, output_weights=output_weights,
    )
    # the same contract as `fast_labeling`: the map holds the labelled GATES -- inputs are skipped
    # and the outputs are only seeds here, never part of the result (an extraction mode reading the
    # output weights would otherwise see keys that the old path never produced: measured on
    # `--extraction-mode=100`, which changed its answer for that reason alone)
    # ...and in the graph's own order, so the dict keeps a deterministic, topology-derived insertion
    # order instead of the order the logics happened to fill it in
    return {name: weights[name] for name in order
            if name in weights
            and name not in view.outputs
            and not (skip_input and name[:2] == 'in')}
