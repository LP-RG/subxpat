from abc import abstractmethod
from textwrap import dedent

import networkx as nx
import os
import shutil
import sys
import json
import argparse
import resource
from types import SimpleNamespace
from typing import Callable, ClassVar, Iterable, Literal, Mapping, MutableMapping, Protocol, Self

from sxpat.converting.legacy import iograph_with_weights
from sxpat.converting.porters import GraphVizPorter
from sxpat.graph.graph import IOGraph
from sxpat.labelling.labelling import Labelling
from sxpat.newag import load_circuit_from_verilog
from sxpat.utils.timer import Timer


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument('circuit', type=str)
    # parser.add_argument('solver', choices=['z3int', 'z3bvec', 'z3dint', 'z3dbvec', 'qbf'])
    parser.add_argument('--min', action='store_true')
    # parser.add_argument('--with-low', action='store_true')
    return parser.parse_args()


def rusage_counter() -> float:
    proc_rusage = resource.getrusage(resource.RUSAGE_SELF)
    chld_rusage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (
        + proc_rusage.ru_utime  # process user level time
        + proc_rusage.ru_stime  # process system level time
        + chld_rusage.ru_utime  # waited children user level time
        + chld_rusage.ru_stime  # waited children system level time
    )


def wrapplll(ccc): return ccc[1], label_node(ccc[0], ccc[1], ccc[2])


def label_node(c: IOGraph, n: str, specs):
    labeller = Labelling(
        c, c,
        SimpleNamespace(path=SimpleNamespace(run=SimpleNamespace(solver_scripts=f'output/scripts/{specs.min}_{specs.circuit.split('/')[-1][:-2]}')), iteration=n),  # pyright: ignore[reportArgumentType]
        minimise=specs.min,
        use_functions=True,
    )

    t = rusage_counter()
    w = labeller.label_node(n)
    t = rusage_counter() - t
    return w, t


def compute_all(c: IOGraph, specs):
    # from concurrent.futures.process import ProcessPoolExecutor
    # with ProcessPoolExecutor(12) as p:
    return dict(map(
        wrapplll,
        [
            (c, n, specs)
            for n in c._inner.nodes
            if n.startswith('g')
        ]
    ))


def first(iterable):
    return next(iter(iterable))


class Pattern(Protocol):
    preferred_direction: ClassVar[Literal['up', 'down'] | None]
    estimated_occurrences_ratio: ClassVar[float]

    @property
    @abstractmethod
    def skipped_nodes(self) -> Iterable[str]:
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def match(cls, g: nx.DiGraph, node: str) -> None | Self:
        """
        Returns an instance of the pattern if the node and neighbours follow the structure.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def match_all(cls, g: nx.DiGraph) -> Iterable[Self]:
        """
        Returns an iterable containing all the matches of this pattern on the given graph.
        """
        raise NotImplementedError()

    @abstractmethod
    def apply(self, weights: MutableMapping[str, int]) -> Literal[-1, 0, +1]:
        """
        Given the mutable mapping of weight, apply the current pattern if possible.

        Returns `True` if it has done everything it could, meaning that reapplying it in the future will do nothing.
        """
        raise NotImplementedError()

    @abstractmethod
    def verify(self, weights: Mapping[str, int]) -> bool:
        """
        Given the mapping of weights, returns if the pattern rules are respected.

        This method may not always be implemented.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def count_possible_skips(cls, g: nx.DiGraph) -> int:
        """
        Returns how many nodes this pattern could allow to skip.
        """
        raise NotImplementedError()

    @classmethod
    def count_occurrences(cls, g: nx.DiGraph) -> int:
        """
        Returns how many thimes this pattern matches on the given graph.
        """
        return sum(1 for _ in cls.match_all(g))


class SimpleNotPattern(Pattern):
    preferred_direction = 'up'
    estimated_occurrences_ratio = 0.36542349073331776  # this is the mean of actual skips, with stdev=0.04227145829403331

    @classmethod
    def match(cls, g: nx.DiGraph, node: str):
        # matches only if `node` is the succ (usually, a `not`)
        pres = g.pred[node]
        if len(pres) != 1: return None
        sucs = g.succ[first(pres)]
        if len(sucs) != 1: return None
        return cls(node, first(pres))

    @classmethod
    def match_all(cls, g: nx.DiGraph) -> Iterable[Self]:
        # TODO: can be improved (maybe delegate reordering to outside? or force topological order beforehand)
        for n in reversed(list(g.nodes)):
            _m = cls.match(g, n)
            if _m is not None: yield _m

    def __init__(self, a_not: str, b_any: str) -> None:
        """Private constructor."""
        self._a_not = a_not
        self._b_any = b_any

    @property
    def skipped_nodes(self) -> Iterable[str]:
        return [self._b_any]

    def apply(self, weights: MutableMapping[str, int]):
        a_in = self._a_not in weights
        b_in = self._b_any in weights
        if a_in and not b_in:
            weights[self._b_any] = weights[self._a_not]
            return +1
        if not a_in and b_in:
            weights[self._a_not] = weights[self._b_any]
            return +1
        return -1

    def verify(self, weights: Mapping[str, int]) -> bool:
        return weights[self._a_not] == weights[self._b_any]

    @classmethod
    def count_possible_skips(cls, g: nx.DiGraph) -> int:
        return cls.count_occurrences(g)


class AndPattern(Pattern):
    preferred_direction = 'down'
    estimated_occurrences_ratio = 0.09499698908308332  # this is the mean of raw matches, with stdev=0.025869471647911205

    @classmethod
    def match(cls, g: nx.DiGraph, node: str) -> None | Self:
        # matches only if `node` is the succ (usually, an `and`)
        pres = g.pred[node]
        if len(pres) != 2: return None
        for p in pres:
            sucs = g.succ[p]
            if len(sucs) != 1: return None
        return cls(node, *pres)

    @classmethod
    def match_all(cls, g: nx.DiGraph) -> Iterable[Self]:
        # TODO: can be improved (maybe delegate reordering to outside? or force topological order beforehand)
        for n in g.nodes:
            _m = cls.match(g, n)
            if _m is not None: yield _m

    def __init__(self, a_and: str, b_any: str, c_any: str) -> None:
        """Private constructor."""
        self._a_and = a_and
        self._b_any = b_any
        self._c_any = c_any

    @property
    def skipped_nodes(self) -> Iterable[str]:
        return [self._a_and]

    def apply(self, weights: MutableMapping[str, int]):
        a_in = self._a_and in weights
        bc_in = self._b_any in weights and self._c_any in weights
        if bc_in and not a_in:
            b_w = weights[self._b_any]
            c_w = weights[self._c_any]
            if b_w == c_w:
                weights[self._a_and] = weights[self._b_any]
                return 1
            else:
                return 0
        return -1

    def verify(self, weights: Mapping[str, int]) -> bool:
        return (
            (weights[self._b_any] == weights[self._c_any])
            and (weights[self._b_any] == weights[self._a_and])
        )

    @classmethod
    def count_possible_skips(cls, g: nx.DiGraph) -> int:
        # each match has 3 nodes, if the 2 operands are equal, the third sometimes can be skipped (not a guarantee for now!)
        return cls.count_occurrences(g)


class MiddlePattern(Pattern):
    """
    DOES NOT HOLD
    """

    preferred_direction = None
    estimated_occurrences_ratio = 0.09499698908308332  # this is the mean of raw matches, with stdev=0.025869471647911205

    @classmethod
    def match(cls, g: nx.DiGraph, node: str) -> None | Self:
        # matches only if `node` is the middle (usually, a `not`)
        pres = g.pred[node]
        sucs = g.succ[node]
        if len(pres) == 1 and len(sucs) == 1:
            return cls(node, first(pres), first(sucs))
        return None

    @classmethod
    def match_all(cls, g: nx.DiGraph) -> Iterable[Self]:
        # TODO: can be improved (maybe delegate reordering to outside? or force topological order beforehand)
        for n in g.nodes:
            _m = cls.match(g, n)
            if _m is not None: yield _m

    def __init__(self, a_mid: str, b_prev: str, c_succ: str) -> None:
        """Private constructor."""
        self._a_mid = a_mid
        self._b_prev = b_prev
        self._c_succ = c_succ

    @property
    def skipped_nodes(self) -> Iterable[str]:
        return [self._a_mid]

    def apply(self, weights: MutableMapping[str, int]):
        a_in = self._a_mid in weights
        bc_in = self._b_prev in weights and self._c_succ in weights
        if bc_in and not a_in:
            b_w = weights[self._b_prev]
            c_w = weights[self._c_succ]
            if b_w == c_w:
                weights[self._a_mid] = weights[self._b_prev]
                return 1
            else:
                return 0
        return -1

    def verify(self, weights: Mapping[str, int]) -> bool:
        return (
            (weights[self._b_prev] == weights[self._c_succ])
            and (weights[self._b_prev] == weights[self._a_mid])
        )

    @classmethod
    def count_possible_skips(cls, g: nx.DiGraph) -> int:
        # each match has 3 nodes, if the 2 operands are equal, the third sometimes can be skipped (not a guarantee for now!)
        return cls.count_occurrences(g)


def draw_gv(g: IOGraph, stuff, skipped_nodes) -> str:
    @staticmethod
    def shade_compute(g, n, key):
        sub = 0
        # sub = min((getattr(n, 'weight', 0) or 100000000) for n in g.nodes)

        ratio = max((stuff.get(n, (0, 0))[key] - sub), 0) / max(stuff.get(n0.name, (0, 0))[key] for n0 in g.nodes)
        # ratio
        xxx = int(ratio * 255)
        return f'"#FF{255 - xxx:2X}{255 - xxx:2X}"'

    def node(n):
        name = n.name
        s = f'"{name}" [label="{name}\\n{stuff.get(name, (0, 0))[0]}", fillcolor={shade_compute(g, name, 1)}'
        if name in skipped_nodes: s += ', penwidth=10, color=blue'
        s += '];'
        return s

    return (f"""
strict digraph _ShadeGraph {{
    node [style=filled, shape=circle];
    {'\n    '.join(node(n) for n in g.nodes)}
    {'\n    '.join(f'"{p}" -> "{s.name}";' for s in g.nodes if hasattr(s, 'operands') for p in s.operands)}
}}
""")


if __name__ == '__main__':
    specs = args()

    shutil.rmtree(f'output/scripts/{specs.min}_{specs.circuit.split('/')[-1][:-2]}', ignore_errors=True)
    shutil.rmtree(f'output/tmp/{specs.min}_{specs.circuit.split('/')[-1][:-2]}', ignore_errors=True)
    os.makedirs(f'output/scripts/{specs.min}_{specs.circuit.split('/')[-1][:-2]}', exist_ok=True)
    os.makedirs(f'output/tmp/{specs.min}_{specs.circuit.split('/')[-1][:-2]}', exist_ok=True)

    c = load_circuit_from_verilog(specs.circuit, SimpleNamespace(temporary=f'output/tmp/{specs.min}_{specs.circuit.split('/')[-1][:-2]}'))
    ii = c._inner

    res = compute_all(c, specs)
    res.update((n, (2**i, 0)) for i, n in enumerate(c.outputs_names))
    res.update((n, (-1, 0)) for n in c.inputs_names)
    # c = iograph_with_weights(c, {n: w for (n, (w, t)) in res.items()})
    # c = ShadeGraph(c.nodes, c.inputs_names, c.outputs_names)

    skipped_nodes = set()
    failures = []
    _weights: dict[str, int] = {k: v[0] for k, v in res.items()}

    def do_patt(pattern):
        for patt in pattern.match_all(c._inner):
            if patt.verify(_weights):
                skipped_nodes.update(patt.skipped_nodes)
            else:
                failures.append(f'failed pattern {pattern.__qualname__} for nodes {patt.skipped_nodes}')
    # do_patt(SimpleNotPattern)
    # do_patt(AndPattern)
    do_patt(MiddlePattern)

    folder = f'ZZ_output/{'mini' if specs.min else 'maxi'}'
    os.makedirs(folder, exist_ok=True)
    with open(f'{folder}/{specs.circuit.split('/')[-1][:-2]}.err', 'w') as f: f.write('\n'.join(failures))
    # GraphVizPorter.to_file(c, f'{folder}/{specs.circuit.split('/')[-1][:-2]}.gv')
    with open(f'{folder}/{specs.circuit.split('/')[-1][:-2]}.gv', 'w') as f: f.write(draw_gv(c, res, skipped_nodes))
    with open(f'{folder}/{specs.circuit.split('/')[-1][:-2]}.json', 'w') as _f: json.dump(res, _f, indent='\t')

    # c = iograph_with_weights(c, dict.fromkeys([
    #     n for n in ii.nodes
    #     if ii.in_degree[n] == 1 and ii.out_degree[list(ii.predecessors(n))[0]] == 1
    # ], 1))

    # GraphVizPorter.to_file(ShadeGraph(c.nodes, c.inputs_names, c.outputs_names), 'aaa.gv')

    # x = len([
    #     n for n in ii.nodes
    #     if ii.in_degree[n] == 1 and ii.out_degree[list(ii.predecessors(n))[0]] == 1
    # ])
    # print(x)

    # y = len(ii.nodes) - len(c.inputs_names) - len(c.outputs_names)
    # print(y)

    # print(AndPattern.count_possible_skips(ii) / y)

    # for n in c._inner.nodes:
    #     print(n)
    #     if n.startswith('g'): print('^^^')
