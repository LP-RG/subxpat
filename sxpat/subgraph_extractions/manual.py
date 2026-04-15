from typing import Iterable, Sequence

import os.path
import networkx as nx
from sxpat.utils.graph import is_selection_convex

from sxpat.specifications import Specifications


def extract(graph: nx.DiGraph, specs: Specifications) -> Sequence[str]:
    before_path = os.path.join(specs.path.run.graphviz, 'manual_subgraph_extraction.gv')
    after_path = os.path.join(specs.path.run.graphviz, 'manual_subgraph_extraction_confirmation.gv')

    # show graph
    export(graph, before_path)
    print(f'please open file "{before_path}" to view the graph.')

    while True:
        # parse selected nodes
        selected_nodes = input('what nodes should be in the subgraph? write the names separated by spaces\n').split()

        # check nodes existance
        if not all(n in graph.nodes for n in selected_nodes):
            print('some of the selected nodes are not present in the graph')
            continue

        # check convexity
        if not is_selection_convex(graph, selected_nodes):
            print('the selected nodes do not form a convex subgraph')
            continue

        # show resulting subgraph
        export(graph, after_path, selected_nodes)
        print(f'please open file "{after_path}" to view the selection.')

        # ask for confirmation
        while True:
            choice = input(f'is the selection correct? [y/n] ').upper()
            if choice in 'YN': break
        if choice == 'N': continue

        return selected_nodes


def export(graph: nx.DiGraph, path: str, colored: Iterable[str] = ()):
    colored = frozenset(colored)
    with open(path, 'w') as f:
        f.write('digraph manual_extraction {\n')
        for n in graph.nodes:
            if n in colored:
                f.write(f'"{n}" [label="{n}", fillcolor=red, style=filled];\n')
            else:
                f.write(f'"{n}" [label="{n}"];\n')
        for u, v in graph.edges: f.write(f'"{u}" -> "{v}";\n')
        f.write('}')
