from __future__ import annotations
from typing import Callable, Mapping

from collections import defaultdict
import networkx as nx

from sxpat.graph import IOGraph


def propagate_values(
        graph: nx.digraph.DiGraph,
        combiner: Callable[[int, int], int],
        initial_values: Mapping[str, int],
):
    """
        Given a graph, a function to combine values, and an initial/default value for each node, 
        propagate the values from bottom to top.

        :note: The function may give wrong results if the graph is cyclic.

        :param graph: The graph on which to propagate the values.
        :param combiner: The function that given the current value of a node and the arriving
                         value from a child, compute the new value for the node.
        :param initial_values: The mapping with initial/default value for each node.
        :return: The mapping with all propagated values.

        :authors: Lorenzo Spada, Marco Biasion
    """

    # prepare state for custom dfs
    succ_not_done_count = {n: d for (n, d) in graph.out_degree}
    stack = list(n for (n, d) in graph.out_degree if d == 0)  # initally with all outputs

    values = dict(initial_values)
    def value_of(n: str) -> int: return values[n] if n in values else initial_values[n]

    while stack:
        node = stack.pop()
        value = value_of(node)

        for pred in graph.predecessors(node):
            # update
            succ_not_done_count[pred] -= 1
            values[pred] = combiner(value, value_of(pred))

            # push predecessor if all children are done
            if succ_not_done_count[pred] == 0: stack.append(pred)

    return values


def upper_bound(graph: IOGraph) -> Mapping[str, int]:
    initial_values = defaultdict(lambda: 0)
    # TODO:marco to lorenzo: is this always safe?
    for (i, node) in enumerate(graph.outputs):
        initial_values[node.name] = 2 ** i
        # initial_values[node.name] = 2 ** int(node.name[3:])

    # TODO:marco to lorenzo: should this be +?
    return propagate_values(graph._inner, lambda v, w: v | w, initial_values)


def lower_bound(graph: IOGraph) -> Mapping[str, int]:
    initial_values = defaultdict(lambda: 2 ** len(graph.outputs))
    # TODO:marco to lorenzo: is this always safe?
    for (i, node) in enumerate(graph.outputs):
        initial_values[node.name] = 2 ** i
        # initial_values[node.name] = 2 ** int(node.name[3:])

    return propagate_values(graph._inner, min, initial_values)
