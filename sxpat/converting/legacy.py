from typing import Iterable, Mapping

import networkx as nx

from sxpat.graph import IOGraph, SGraph
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity
from sxpat.utils.functions import str_to_bool


__all__ = [
    'iograph_from_digraph',
    'iograph_with_weights',
    'iograph_to_sgraph',
]


def iograph_from_digraph(clean_digraph: nx.DiGraph) -> IOGraph:
    gtypes = {'not': Not, 'and': And}

    # construct nodes and extract inputs/outputs
    nodes = list()
    inputs_names = list()
    outputs_names = list()
    for (node, attrs) in clean_digraph.nodes(True):
        ntype = attrs.get('type')

        if ntype == 'input':
            inputs_names.append(node)
            nodes.append(BoolVariable(node))
        elif ntype == 'output':
            outputs_names.append(node)
            nodes.append(Identity(
                node,
                clean_digraph.predecessors(node),  # type: ignore
            ))
        elif ntype == 'gate':
            cls = gtypes[attrs.get('label')]
            nodes.append(cls(
                node,
                clean_digraph.predecessors(node),  # type: ignore
            ))
        elif ntype == 'constant':
            nodes.append(BoolConstant(
                node,
                str_to_bool(attrs.get('label')),
            ))
        else:
            raise RuntimeError(f'Unable to parse node {node} from DiGraph (attributes={attrs})')

    # construct graph
    return IOGraph(
        nodes,
        sorted(inputs_names, key=lambda x: int(x[2:])),
        sorted(outputs_names, key=lambda x: int(x[3:])),
    )

def _my_nodes_from_inner_legacy(inner_graph):
    nodes = list()
    for (index, data) in inner_graph.nodes(True):
        # get features
        weight = data.get('weight', None)
        in_subgraph = bool(data.get('subgraph', False))
        operands = inner_graph.predecessors(index)
        node_type = data.get('type')
        # "type" -> [const, pi, gate, po]

        # create node
        if node_type[1]:  # input
            nodes.append(BoolVariable(index, weight, in_subgraph))
        elif node_type[3]:  # output
            nodes.append(Identity(index, operands, weight, in_subgraph))
        elif node_type[2] == 1:  # and
            nodes.append(And(index, operands, weight, in_subgraph))
        elif node_type[2] == 2:  # not
            nodes.append(Not(index, operands, weight, in_subgraph))
        elif node_type[0]:  # constant
            nodes.append(BoolConstant(index, True, weight, in_subgraph))
        else:
            raise RuntimeError(f'Unable to parse node {index} from AnnotatedGraph ({data})')

    return nodes


def iograph_with_weights(graph: IOGraph, weights: Mapping[str, int]) -> IOGraph:
    return graph.copy(
        node.copy(weight=weights.get(node.name, None))
        for node in graph.nodes
    )

def my_iograph_from_legacy(l_graph) -> IOGraph:
    return IOGraph(_my_nodes_from_inner_legacy(l_graph.graph),
                   l_graph.input_dict.values(),
                   l_graph.output_dict.values())

def iograph_to_sgraph(graph: IOGraph, subgraph_nodes: Iterable[str]) -> SGraph:
    subgraph_nodes = frozenset(subgraph_nodes)
    return SGraph(
        (
            node.copy(in_subgraph=node.name in subgraph_nodes)
            for node in graph.nodes
        ),
        graph.inputs_names,
        graph.outputs_names,
    )
