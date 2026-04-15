from typing import Iterable

import networkx as nx


def is_selection_convex(graph: nx.DiGraph, selected_nodes: Iterable[str]) -> bool:
    """
        Given a DiGraph and the nodes in the selection, returns if the selection is convex or not.

        A selection is convex if all paths between selected nodes only traverse other selected nodes.

        @authors: Marco Biasion
    """

    selected_nodes = frozenset(selected_nodes)

    # we run dfs for each selected node as source
    for source in selected_nodes:
        visited = set()
        # we start from the source, marking the traversal as not exited from the selection
        stack = [(source, False)]

        while stack:
            node, exited = state = stack.pop()

            # skip if a node has already been visited with the same exited status
            if state in visited: continue
            visited.add(state)

            for neighbor in graph.successors(node):
                # if the destination is a selected node
                if neighbor in selected_nodes:
                    # terminate if the selection is not convex
                    # meaning that a non selected node was traversed before re-entering in the selection
                    if exited: return False
                    # continue to next neighbour
                    # we do not care of paths beyond that as they will be managed in their own dfs runs
                    else: continue

                # if the destination is outside the selection
                else:
                    # remember that we exited and continue
                    stack.append((neighbor, True))

    return True
