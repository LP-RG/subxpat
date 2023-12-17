# typing
from __future__ import annotations

# libs
import networkx as nx

# sxpat libs
from sxpat.annotatedGraph import AnnotatedGraph


def exctract_subgraph(graph: AnnotatedGraph) -> nx.DiGraph:
    gg: nx.DiGraph = graph.graph
    new_graph = nx.DiGraph()

    # add inputs
    inputs = [
        # (name, {**gg.nodes[name], "shape": "circle", "label": ""})
        (name, {**gg.nodes[name], "shape": "circle", "label": name})
        for name in graph.subgraph_input_dict.values()
    ]
    new_graph.add_nodes_from(inputs)

    # add inner gates
    gates = [
        (name, {**gg.nodes[name], "label": f"{name}\\n{gg.nodes[name]['label']}"})
        # (name, {**gg.nodes[name]})
        for name in graph.subgraph_gate_dict.values()
    ]
    new_graph.add_nodes_from(gates)

    # add outputs
    outputs_names = list(graph.subgraph_output_dict.values())
    new_graph.add_nodes_from(
        (f"ref_{name}", {"label": f"ref_{name}", "shape": "doublecircle"})
        for name in outputs_names
    )

    # add normal edges
    subgraph_gates = set(graph.subgraph_gate_dict.values())
    for src, dst in gg.edges:
        if (src in subgraph_gates or dst in subgraph_gates) and (src not in outputs_names):
            new_graph.add_edge(src, dst)
    # add output edges
    for out_name in outputs_names:
        new_graph.add_edge(out_name, f"ref_{out_name}")

    return new_graph
