from __future__ import annotations
from abc import ABC, ABCMeta, abstractmethod
from collections import UserList
import functools
from typing import AbstractSet, Collection, Container, Dict, List, Mapping, Sequence, Set, Tuple

from sxpat.graph import Graph
import networkx as nx

import os
import time


class Match:
    def __init__(self, pattern: Pattern, nodes: Mapping[str, str]):
        """
            :param pattern: the pattern that generated this matching.
            :param nodes:   the mapping pattern_node->graph_node for all nodes in the matching.
        """
        # reference the pattern
        self.pattern = pattern

        # sort the symmetries and store the nodes
        self.nodes = dict(nodes)

        # compute hash (assuming nodes never change)
        self.hash = hash(self.pattern.name) ^ hash(','.join(self.nodes.values()))

    @functools.cached_property
    def id(self) -> str:
        match_nodes = ','.join(self.nodes[pn] for pn in self.pattern.dig.nodes)
        return f'[{self.pattern.name}][{match_nodes}]'

    def __hash__(self) -> int: return self.hash
    def __str__(self) -> str: return self.id

    def __eq__(self, other: object):
        return (
            type(self) == type(other)
            and self.pattern == other.pattern
            and self.nodes == other.nodes
        )


class Pattern(ABC):
    name: str

    @abstractmethod
    def match(self, graph: nx.digraph.DiGraph) -> Set[Match]:
        """
            Search and return all occurrences of the pattern in the given graph.
        """
        raise NotImplementedError()

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        return type(self) == type(other)


class SimplePattern(Pattern):
    def __init__(
            self,
            nodes: Collection[str],
            edges: Collection[Tuple[str, str]],
            any_inputs: Container[str],
            any_outputs: Container[str],
            symmetries: Collection[Collection[Sequence[str]]] = ()
    ):
        assert all(e[0] in nodes and e[1] in nodes for e in edges), 'edges with missing nodes'

        self.dig = nx.digraph.DiGraph()
        self.dig.add_nodes_from(nodes)
        self.dig.add_edges_from(edges)
        self.any_inputs_ok = frozenset(any_inputs)
        self.any_outputs_ok = frozenset(any_outputs)
        self.symmetries = tuple(tuple(tuple(ns) for ns in sym) for sym in symmetries)

    @functools.cached_property
    def name(self) -> str:
        patt_nodes = ','.join(self.dig.nodes)
        patt_edges = ','.join(f'{a}-{b}' for (a, b) in self.dig.edges)
        patt_any_in = ','.join(self.any_inputs_ok)
        patt_any_out = ','.join(self.any_outputs_ok)
        patt_sym = ','.join('/'.join('-'.join(alt) for alt in alts) for alts in self.symmetries)
        return f'{patt_nodes}|{patt_edges}|{patt_any_in}|{patt_any_out}|{patt_sym}'

    def __eq__(self, other: object) -> bool:
        return super().__eq__(other) and self.name == other.name

    def match(self, graph: nx.digraph.DiGraph) -> Set[Match]:
        """
            Search and return all occurrences of the pattern in the given graph.
        """

        # 1) get isomorphic matches
        matches_1 = tuple(
            nx.algorithms.isomorphism
            .DiGraphMatcher(graph, self.dig)
            .subgraph_isomorphisms_iter()
        )

        # 2) filter for matching in/out degrees
        matches_2: List[Dict[str, str]] = list()
        for m in matches_1:
            valid = True
            for gn, pn in m.items():
                # in
                if pn in self.any_inputs_ok:
                    # - in any_..._ok, so we expect a minimum degree
                    if graph.in_degree(gn) < self.dig.in_degree(pn):
                        valid = False
                        break
                else:
                    # - not in any_..._ok, so we expect exact matching
                    if graph.in_degree(gn) != self.dig.in_degree(pn):
                        valid = False
                        break
                # out
                if pn in self.any_outputs_ok:
                    # - in any_..._ok, so we expect a minimum degree
                    if graph.out_degree(gn) < self.dig.out_degree(pn):
                        valid = False
                        break
                else:
                    # - not in any_..._ok, so we expect exact matching
                    if graph.out_degree(gn) != self.dig.out_degree(pn):
                        valid = False
                        break

            if valid: matches_2.append(m)

        # 3) uniform symmetries and create Match records
        matches_3 = set()
        for m in matches_2:
            # invert to have pattern_node->graph_node
            nodes = dict((b, a) for (a, b) in m.items())

            # for all symmetries
            for alts in self.symmetries:
                # group alternatives (a symmetry has at least two alternatives)
                match_alternatives = tuple(tuple(nodes[n] for n in alt) for alt in alts)
                # sort by first node alphabetically
                sorted_alternatives = sorted(match_alternatives, key=lambda ns: ns[0])
                # update nodes with sorted alternatives
                for (anodes, mnodes) in zip(alts, sorted_alternatives):
                    for (sn, mn) in zip(anodes, mnodes):
                        nodes[sn] = mn

            matches_3.add(Match(self, nodes))

        return matches_3


patterns = {
    # 1 to 1 (simple not)
    'pattern1': SimplePattern('AB', ['AB'], 'A', 'B'),
    # 2 to 1 (simple and)
    'pattern2': SimplePattern('ABC', ['AC', 'BC'], 'AB', 'C', ['AB']),
    #
    'pattern3': SimplePattern('ABCD', ['AB', 'AC', 'DC'], 'AD', 'BC'),
    #
    'pattern4': SimplePattern('ABCDE', ['AB', 'AC', 'DC', 'DE'], 'AD', 'BCE', [['AB', 'DE']]),
}


def load_graph(filename: str) -> Graph:
    # imports
    from sxpat.converting.legacy import iograph_from_legacy
    from pickle import load

    # deserialize
    with open(filename, 'rb') as f: annotated_graph = load(f)
    # convert
    return iograph_from_legacy(annotated_graph)


def elaborate(filename: str) -> dict:
    g = load_graph(filename)

    results = dict()
    for (pname, pattern) in patterns.items():
        t = time.perf_counter()
        matches = pattern.match(g._inner)
        print(*matches, sep='\n')
        t = time.perf_counter() - t
        results[pname] = (matches, t)

        print(f'{filename} X {pname}: found {len(matches)} matches in {t:.4f}s ({len(g._inner)} nodes)')

    return results


def main():
    folder = 'labelled_graphs'
    results = dict()

    files = os.listdir(folder)
    for (i, filename) in enumerate(files):
        print(f'{i+1 / len(files) * 100:>3.0f}% ({i+1} / {len(files)})')

        filename = f'{folder}/{filename}'
        results[filename] = elaborate(filename)

    return results


def benchmark():
    # setings
    filename = 'labelled_graphs/adder_i256_o129.pkl'
    patterns_name = ['pattern1', 'pattern2']
    N = 20

    # setup
    g = load_graph(filename)._inner
    ps = tuple(patterns[pname] for pname in patterns_name)

    t = time.perf_counter()
    for i in range(N):
        for p in ps:
            p.match(g)
    t = time.perf_counter() - t

    print(t)


if __name__ == '__main__':
    # benchmark()
    # at = time.perf_counter()
    # main()
    # at = time.perf_counter() - at
    # print(f'total took {at:.4f}s')
    elaborate('labelled_graphs/adder_i176_o89_DEL3K3O5ZZCY_i2_0.pkl')
