from typing import Callable, Mapping

from collections import defaultdict
import operator
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

        :param graph:          The graph on which to propagate the values.
        :param combiner:       The function that given the current value of a node and the arriving
                               value from a child, compute the new value for the node.
        :param initial_values: The mapping with initial/default value for each node.
        :return:               The mapping with all propagated values.

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


def simple_add(graph: IOGraph) -> dict[str, int]:
    """
    Computes an upper bound for the weight of each node by adding up the weight of its children.

    It is guaranteed that the exact weight of each node is always smaller or equal to this bound.

    **DEPENDS ON THE CIRCUIT HAVING ONLY ONE SEMANTIC OUTPUT (all bits are part of the same number).**

    :authors: Lorenzo Spada, Marco Biasion
    """

    initial_values = defaultdict(lambda: 0)
    for (i, node) in enumerate(graph.outputs):
        initial_values[node.name] = 2 ** i

    return propagate_values(graph._inner, operator.add, initial_values)


def simple_or(graph: IOGraph) -> dict[str, int]:
    """
    Computes an upper bound for the weight of each node by or-ing the weight of its children.  
    This is equivalent to computing the sum of the weights of the outputs reachable from the node.

    It is guaranteed that the exact weight of each node is always smaller or equal to this bound.

    **DEPENDS ON THE CIRCUIT HAVING ONLY ONE SEMANTIC OUTPUT (all bits are part of the same number).**

    :authors: Lorenzo Spada, Marco Biasion
    """

    initial_values = defaultdict(lambda: 0)
    for (i, node) in enumerate(graph.outputs):
        initial_values[node.name] = 2 ** i

    return propagate_values(graph._inner, operator.or_, initial_values)


def simple_min(graph: IOGraph) -> dict[str, int]:
    """
    Computes a lower bound for the weight of each node by keeping the minimum weight of its children.  
    This is equivalent to using as weight the weight of the smallest output reachable from the node.

    It is guaranteed that the exact weight of each node is always greater or equal to this bound.

    **DEPENDS ON THE CIRCUIT HAVING ONLY ONE SEMANTIC OUTPUT (all bits are part of the same number).**

    :authors: Lorenzo Spada, Marco Biasion
    """

    initial_values = defaultdict(lambda: 2 ** len(graph.outputs))
    for (i, node) in enumerate(graph.outputs):
        initial_values[node.name] = 2 ** i

    return propagate_values(graph._inner, min, initial_values)
