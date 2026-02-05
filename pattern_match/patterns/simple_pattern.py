from __future__ import annotations
from collections import Counter
from typing import Any, Callable, Collection, Container, Dict, List, Mapping, MutableMapping, Sequence, Set, Tuple

import functools
import itertools
import operator
import networkx as nx

from .pattern import Pattern, Match


class SimplePattern(Pattern):
    def __init__(
            self,
            nodes_count: Collection[int],
            edges: Collection[Tuple[int, int]],
            any_indegree: Container[int],
            any_outdegree: Container[int],
            symmetry: Collection[Sequence[int]] = ()
    ):
        """
            :param nodes_count:   the number of nodes that make the pattern.
            :param edges:         the edges between the nodes (from 0 to `nodes_count` excluded).
            :param any_indegree:  which nodes can have any input degree.
            :param any_outdegree: which nodes can have any output degree.
            :param symmetry:      the symmetry (if any), composed of a set of interchangable sequences of nodes
                                  (the nodes inside a sequence are not interchangable).
        """
        assert all((0 <= e[0] < nodes_count) and (0 <= e[1] < nodes_count) for e in edges), 'edges with missing nodes'
        assert all((0 <= n < nodes_count) for n in any_indegree), 'referencing missing node'
        assert all((0 <= n < nodes_count) for n in any_outdegree), 'referencing missing node'
        assert all(all((0 <= n < nodes_count) for n in seq) for seq in symmetry), 'referencing missing node'

        self.dig = nx.digraph.DiGraph()
        self.dig.add_nodes_from(range(nodes_count))
        self.dig.add_edges_from(edges)
        self.any_inputs_ok = frozenset(any_indegree)
        self.any_outputs_ok = frozenset(any_outdegree)
        self.symmetry = frozenset(tuple(seq) for seq in symmetry)

    @functools.cached_property
    def __str(self) -> str:
        patt_edges = ','.join(f'{a}-{b}' for (a, b) in self.dig.edges)
        patt_any_in = ','.join(map(str, sorted(self.any_inputs_ok)))
        patt_any_out = ','.join(map(str, sorted(self.any_outputs_ok)))
        patt_sym = '/'.join('-'.join(map(str, seq)) for seq in self.symmetry)
        return f'{len(self.dig)}|{patt_edges}|{patt_any_in}|{patt_any_out}|{patt_sym}'

    @functools.cached_property
    def __hash(self) -> int:
        return (
            super().__hash__()
            ^ hash(self.dig)
            ^ hash(self.any_inputs_ok)
            ^ hash(self.any_outputs_ok)
            ^ hash(self.symmetry)
        )

    def __str__(self) -> str: return self.__str
    def __hash__(self) -> int: return self.__hash
    def __eq__(self, other: object) -> bool: return super().__eq__(other) and str(self) == str(other)

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

        # 3) collapse the symmetry to the normal form and create Match records
        matches_3 = set()
        for m in matches_2:
            # invert to have pattern_node->graph_node
            nodes = dict((b, a) for (a, b) in m.items())

            # group sequences (a symmetry has at least two sequences)
            match_seqs = tuple(tuple(nodes[n] for n in seq) for seq in self.symmetry)
            # sort by first node alphabetically
            sorted_seqs = sorted(match_seqs, key=lambda ns: ns[0])
            # update nodes with sorted sequences
            for (snodes, mnodes) in zip(self.symmetry, sorted_seqs):
                for (sn, mn) in zip(snodes, mnodes):
                    nodes[sn] = mn

            matches_3.add(self.__Match(self, nodes))

        return matches_3

    def analyze_rules(
            self,
            match: __Match,
            get_value: Callable[[Any], int],
            should_analyze: Callable[[Any], bool],
            result_container: Counter[str],
    ):
        # generate rules
        rules = []

        # size 3+
        others = lambda ia, inodes: [ib for ib in inodes if ib != ia]
        operators_n = [
            ('{ia}<min({ios})', lambda ia, ios: lambda vs: vs[ia] < min(vs[ib] for ib in ios)),
            ('{ia}<=min({ios})', lambda ia, ios: lambda vs: vs[ia] <= min(vs[ib] for ib in ios)),
            ('{ia}>min({ios})', lambda ia, ios: lambda vs: vs[ia] > min(vs[ib] for ib in ios)),
            ('{ia}>=min({ios})', lambda ia, ios: lambda vs: vs[ia] >= min(vs[ib] for ib in ios)),
            ('{ia}==min({ios})', lambda ia, ios: lambda vs: vs[ia] == min(vs[ib] for ib in ios)),
            # ('{ia}!=min({ios})', lambda ia, ios: lambda vs: vs[ia] != min(vs[ib] for ib in ios)),
            ('{ia}<max({ios})', lambda ia, ios: lambda vs: vs[ia] < max(vs[ib] for ib in ios)),
            ('{ia}<=max({ios})', lambda ia, ios: lambda vs: vs[ia] <= max(vs[ib] for ib in ios)),
            ('{ia}>max({ios})', lambda ia, ios: lambda vs: vs[ia] > max(vs[ib] for ib in ios)),
            ('{ia}>=max({ios})', lambda ia, ios: lambda vs: vs[ia] >= max(vs[ib] for ib in ios)),
            ('{ia}==max({ios})', lambda ia, ios: lambda vs: vs[ia] == max(vs[ib] for ib in ios)),
            # ('{ia}!=max({ios})', lambda ia, ios: lambda vs: vs[ia] != max(vs[ib] for ib in ios)),
        ]
        rules.extend([
            ([ia, *(ios := others(ia, inodes))], op_t[0].format(ia=ia, ios=ios), op_t[1](ia, ios))
            for size in range(3, len(self.dig) + 1)
            for (inodes) in itertools.combinations(range(len(self.dig)), size)
            for ia in inodes
            for op_t in operators_n
        ])

        # size 2
        operators_2 = [
            ('{ia}<{ib}', lambda ia, ib: lambda vs: vs[ia] < vs[ib]),
            ('{ia}<={ib}', lambda ia, ib: lambda vs: vs[ia] <= vs[ib]),
            # ('{ia}>{ib}', lambda ia, ib: lambda vs: vs[ia] > vs[ib]),
            # ('{ia}>={ib}', lambda ia, ib: lambda vs: vs[ia] >= vs[ib]),
            ('{ia}=={ib}', lambda ia, ib: lambda vs: vs[ia] == vs[ib]),
            # ('{ia}!={ib}', lambda ia, ib: lambda vs: vs[ia] != vs[ib]),
        ]
        rules.extend([
            ([ia, ib], op[0].format(ia=ia, ib=ib), op[1](ia, ib))
            for (ia, ib) in itertools.permutations(range(len(self.dig)), 2)
            for op in operators_2
        ])

        # elaborate rules
        values = [get_value(n) for n in match.nodes.values()]
        result_container.update({
            name: func(values)
            for (inodes, name, func) in rules
            if all(should_analyze(match.nodes[i]) for i in inodes)

        })

        return result_container

    class __Match(Match['SimplePattern']):
        def __init__(self, pattern: SimplePattern, nodes: Mapping[str, str]):
            """
                :param pattern: the pattern that generated this matching.
                :param nodes:   the mapping pattern_node->graph_node for all nodes in the matching.
            """
            super().__init__(pattern)

            # force pattern node order and freeze (TODO: freeze)
            self.nodes = dict(nodes)
        
        def is_match_ok(self, predicate: Callable[[Any], bool]) -> bool:
            return all(predicate(n) for n in self.nodes.values())

        def ok_count(self, predicate: Callable[[Any], bool]) -> int:
            return int(self.is_match_ok(predicate))

        @functools.cached_property
        def __str(self) -> str:
            match_nodes = ','.join(self.nodes[pn] for pn in self.pattern.dig.nodes)
            return f'[{str(self.pattern)}][{match_nodes}]'

        @functools.cached_property
        def __hash(self) -> int:
            # assume nodes never change
            return hash(self.pattern) ^ hash(','.join(self.nodes.values()))

        def __str__(self) -> str: return self.__str
        def __hash__(self) -> int: return self.__hash

        def __eq__(self, other: object):
            return (
                super().__eq__(other)
                and self.nodes == other.nodes
            )
