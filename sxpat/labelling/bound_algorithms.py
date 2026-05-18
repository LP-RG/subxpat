
from typing import Callable, Dict, Iterable

from sxpat.graph.graph import IOGraph

import networkx as nx
import operator as op


def _compute_bound(
    graph: nx.DiGraph,
    outputs: Iterable[str],
    combine: Callable[[int, int], int],
    init_value: int
) -> Dict[str, int]:

    # initialize structures
    weights = dict.fromkeys(graph.nodes, init_value)
    count = dict.fromkeys(graph.nodes, 0)  # counts the completed children of each node
    stack = []

    # prepare stack with outputs
    for node_name in outputs:
        value = 2 ** int(node_name[3:])
        for x in graph.predecessors(node_name):
            weights[x] = combine(value, weights[x])
            count[x] += 1
            if count[x] == graph.out_degree(x):
                stack.append(x)

    # run custom dfs
    while stack:
        cur_node = stack.pop()
        value = weights[cur_node]
        for x in graph.predecessors(cur_node):
            # update weights of predecessors
            weights[x] = combine(value, weights[x])
            # mark predecessor as having one more child completed
            count[x] += 1
            # add predecessor to stack if all children are completed
            if count[x] == graph.out_degree(x):
                stack.append(x)

    return weights


def simple_sum(current_graph: IOGraph):
    return _compute_bound(
        current_graph._inner,
        (on.name for on in current_graph.outputs),
        combine=op.add,
        init_value=0
    )


def simple_max(current_graph: IOGraph):
    return _compute_bound(
        current_graph._inner,
        (on.name for on in current_graph.outputs),
        combine=op.or_,
        init_value=0
    )


def simple_min(current_graph: IOGraph):
    return _compute_bound(
        current_graph._inner,
        (on.name for on in current_graph.outputs),
        combine=min,
        init_value=2**len(current_graph.outputs)
    )
