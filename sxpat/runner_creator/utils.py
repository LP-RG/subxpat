# typing
from __future__ import annotations
from typing import Iterable

# libs
import networkx as nx

# Z3Log libs
from Z3Log.config.config import TAB

# sxpat libs
from sxpat.annotatedGraph import AnnotatedGraph


def indent_lines(lines: Iterable[str], indent_amount: int = 1) -> Iterable[str]:
    """Indent the lines by the wanted amound."""
    return (TAB * indent_amount + line for line in lines)


def format_lines(lines: Iterable[str], indent_amount: int = 0, extra_newlines: int = 0) -> str:
    """Join lines into a single string, indenting each line by the wanted amount and adding extra newlines at the end if needed."""
    return "\n".join(indent_lines(lines, indent_amount)) + "\n" * (1 + extra_newlines)


def unzip(it: Iterable) -> Iterable:
    return zip(*it)


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
