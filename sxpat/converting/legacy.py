from typing import Type, Union

import functools
import networkx as nx

from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.graph import IOGraph, SGraph
from sxpat.graph.builder import GraphBuilder
from sxpat.graph.node import BoolVariable, BoolConstant, And, Extras, Node, Not, Identity

from sxpat.utils.functions import str_to_bool


__all__ = ['iograph_from_legacy', 'sgraph_from_legacy']


def _add_nodes_from_legacy(builder: GraphBuilder, digraph: nx.digraph.DiGraph) -> GraphBuilder:
    def get_type(label: str) -> Type[Union[Node, Extras]]:
        if label.startswith('in'): return BoolVariable
        elif label.startswith('out'): return Identity
        elif label == 'and': return And
        elif label == 'not': return Not
        elif label in ('FALSE', 'TRUE'): return functools.partial(BoolConstant, value=str_to_bool(label))
        else: raise RuntimeError(f'Unable to parse node {name} from AnnotatedGraph ({value})')

    # add all nodes (and edges)
    for (name, value) in digraph.nodes(True):
        # get features
        label = value.get('label')
        weight = value.get('weight', None)
        in_subgraph = bool(value.get('subgraph', False))
        operands = digraph.predecessors(name)

        # add node
        builder.add_node(name, get_type(label), weight=weight, in_subgraph=in_subgraph)
        if digraph.in_degree(name) > 0: builder.add_operands(operands)


def iograph_from_legacy(l_graph: AnnotatedGraph) -> IOGraph:
    return (
        GraphBuilder()
        # add nodes
        .update_with(_add_nodes_from_legacy, l_graph.graph)
        # mark inputs/outputs
        .mark_inputs(l_graph.input_dict.values())
        .mark_outputs(l_graph.output_dict.values())
        #
        .build(IOGraph)
    )


def sgraph_from_legacy(l_graph: AnnotatedGraph) -> SGraph:
    return (
        GraphBuilder()
        # add nodes
        .update_with(_add_nodes_from_legacy, l_graph.subgraph)
        # mark inputs/outputs
        .mark_inputs(l_graph.input_dict.values())
        .mark_outputs(l_graph.output_dict.values())
        #
        .build(SGraph)
    )
