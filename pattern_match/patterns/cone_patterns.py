from __future__ import annotations
from typing import Any, Callable, ClassVar, Collection, Dict, Mapping, Set, Tuple
from typing_extensions import Self

from collections import Counter, defaultdict
import networkx as nx
import functools

from .pattern import Pattern, Match


class ConesAggregatePattern(Pattern):
    def __new__(cls):
        # singleton
        if not hasattr(cls, '__instance'): cls.__instance = super().__new__(cls)
        return cls.__instance

    def analyze_rules(self, *_): raise Exception(f'class {type(self).__qualname__} does not allow analysing.')
    def __str__(self) -> str: return 'cones_pattern'
    def __hash__(self): return hash(str(self))
    def __eq__(self, other): return super().__eq__(other)

    _intersection_patterns: ClassVar[Dict[int, ConesIntersectionPattern]] = dict()

    @classmethod
    def _get_intersection_pattern(cls, size: int) -> ConesIntersectionPattern:
        if size not in cls._intersection_patterns: cls._intersection_patterns[size] = cls.ConesIntersectionPattern(size)
        return cls._intersection_patterns[size]

    def match(self, graph: nx.digraph.DiGraph) -> Set[Match]:
        # get outnodes
        out_nodes = [n for (n, d) in graph.out_degree if d == 0]

        # prepare cones presence container
        out_cones_per_node: Mapping[str, Set[str]] = defaultdict(set)
        for n in out_nodes: out_cones_per_node[n].add(n)

        # prepare custom dfs (stack filled with out nodes)
        stack = list(out_nodes)
        visited_succ_count = defaultdict(lambda: 0)

        # run custom dfs
        while stack:
            node = stack.pop()
            for pred in graph.predecessors(node):
                visited_succ_count[pred] += 1
                out_cones_per_node[pred].update(out_cones_per_node[node])

                if visited_succ_count[pred] == graph.out_degree(pred): stack.append(pred)

        # group by cones product
        groups: Mapping[Tuple[str, ...], set] = defaultdict(set)
        for n in graph.nodes:
            groups[tuple(sorted(out_cones_per_node[n]))].add(n)

        return set(
            self._get_intersection_pattern(len(outputs)).make_match(
                sorted(outputs),
                sorted((n for n in nodes if n not in outputs))
            )
            for outputs, nodes in groups.items()
        )

    class ConesIntersectionPattern(Pattern):
        def __init__(self, outputs_count: int):
            self.outputs_count = outputs_count

        def match(self, _): raise Exception(f'class {type(self).__qualname__} does not allow matching.')

        def analyze_rules(
                self,
                match: ConesAggregatePattern._Match,
                get_value: Callable[[Any], int],
                should_analyze: Callable[[Any], bool],
                result_container: Counter[str],
        ):
            # generate rules
            rules = [
                (f'v<min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] < min(vs[io] for io in range(self.outputs_count))),
                (f'v<=min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] <= min(vs[io] for io in range(self.outputs_count))),
                (f'v>min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] > min(vs[io] for io in range(self.outputs_count))),
                (f'v>=min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] >= min(vs[io] for io in range(self.outputs_count))),
                (f'v==min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] == min(vs[io] for io in range(self.outputs_count))),
                (f'v!=min({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] != min(vs[io] for io in range(self.outputs_count))),
                #
                (f'v<max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] < max(vs[io] for io in range(self.outputs_count))),
                (f'v<=max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] <= max(vs[io] for io in range(self.outputs_count))),
                (f'v>max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] > max(vs[io] for io in range(self.outputs_count))),
                (f'v>=max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] >= max(vs[io] for io in range(self.outputs_count))),
                (f'v==max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] == max(vs[io] for io in range(self.outputs_count))),
                (f'v!=max({self.outputs_count} outputs)', lambda iv, vs: vs[self.outputs_count + iv] != max(vs[io] for io in range(self.outputs_count))),
            ]

            # elaborate rules
            values = [get_value(n) for n in match.outputs] + [get_value(n) for n in match.nodes]
            result_container.update({
                rname: 0
                for (rname, _) in rules
            })
            result_container.update([
                name
                for (name, func) in rules
                for (iv, node) in enumerate(match.nodes)
                if should_analyze(node)
                if func(iv, values)
            ])

            return result_container

        def __str__(self) -> str: return f'intersection_pattern_with_{self.outputs_count}_outputs'
        def __hash__(self) -> int: return self.outputs_count
        def __eq__(self, other: object) -> bool: return super().__eq__(other) and self.name == other.name

        class __Match(Match['ConesIntersectionPattern']):
            def __init__(
                    self,
                    pattern: ConesAggregatePattern.ConesIntersectionPattern,
                    outputs: Collection[str],
                    nodes: Collection[str],
            ):
                """
                    :param pattern: the pattern that generated this matching.
                    :param outputs: the collection of nodes that root the cones for the intersection.
                    :param nodes:   the nodes in the cones intersection.
                """
                super().__init__(pattern)

                self.outputs = frozenset(outputs)
                self.nodes = frozenset(nodes)

            def is_match_ok(self, predicate: Callable[[Any], bool]) -> bool:
                return all(predicate(n) for n in self.outputs)

            def ok_count(self, predicate: Callable[[Any], bool]) -> int:
                return sum(predicate(n) for n in self.nodes)

            @functools.cached_property
            def __str(self) -> str:
                output_str = ','.join(self.outputs)
                nodes_str = ','.join(self.nodes)
                return f'[{str(self.pattern)}][{output_str}|{nodes_str}]'

            @functools.cached_property
            def __hash(self) -> int: return hash(str(self.pattern)) ^ hash(self.outputs) ^ hash(self.nodes)

            def __str__(self) -> str: return self.__str
            def __hash__(self) -> int: return self.__hash

            def __eq__(self, other: object) -> bool:
                return (
                    super().__eq__(other)
                    and self.outputs == other.outputs
                    and self.nodes == other.nodes
                )

        def make_match(self, outputs: Collection[str], nodes: Collection[str]) -> __Match:
            return self.__Match(self, outputs, nodes)
