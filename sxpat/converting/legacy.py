from typing import Type, Union

import functools
import networkx as nx

from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.graph import IOGraph, SGraph
from sxpat.graph.graph import GraphBuilder
from sxpat.graph.node import BoolVariable, BoolConstant, And, Extras, Node, Not, Identity

from sxpat.utils.functions import str_to_bool


__all__ = ['iograph_from_legacy', 'sgraph_from_legacy']


# def _nodes_from_inner_legacy(inner_graph: nx.digraph.DiGraph) -> List[Union[BoolVariable, BoolConstant, And, Not, Identity]]:
#     nodes = list()
#     for (name, value) in inner_graph.nodes(True):
#         # get features
#         label = value.get('label')
#         weight = value.get('weight', None)
#         in_subgraph = bool(value.get('subgraph', False))
#         operands = inner_graph.predecessors(name)

#         # create node
#         if label.startswith('in'):  # input
#             nodes.append(BoolVariable(name, weight, in_subgraph))
#         elif label.startswith('out'):  # output
#             nodes.append(Identity(name, operands, weight, in_subgraph))
#         elif label == 'and':  # and
#             nodes.append(And(name, operands, weight, in_subgraph))
#         elif label == 'not':  # not
#             nodes.append(Not(name, operands, weight, in_subgraph))
#         elif label in ('FALSE', 'TRUE'):  # constant
#             nodes.append(BoolConstant(name, str_to_bool(label), weight, in_subgraph))
#         else:
#             raise RuntimeError(f'Unable to parse node {name} from AnnotatedGraph ({value})')

#     return nodes


def _builder_from_legacy(legacy_graph: AnnotatedGraph) -> GraphBuilder:
    def get_type(label: str) -> Type[Union[Node, Extras]]:
        if label.startswith('in'): return BoolVariable
        elif label.startswith('out'): return Identity
        elif label == 'and': return And
        elif label == 'not': return Not
        elif label in ('FALSE', 'TRUE'): return functools.partial(BoolConstant, value=str_to_bool(label))
        else: raise RuntimeError(f'Unable to parse node {name} from AnnotatedGraph ({value})')

    # prepare
    builder = GraphBuilder()
    inner_digraph: nx.digraph.DiGraph = legacy_graph.graph

    # add all nodes (and edges)
    for (name, value) in inner_digraph.nodes(True):
        # get features
        label = value.get('label')
        weight = value.get('weight', None)
        in_subgraph = bool(value.get('subgraph', False))
        operands = inner_digraph.predecessors(name)

        # add node
        builder.add_node(name, get_type(label), weight=weight, in_subgraph=in_subgraph)
        if inner_digraph.in_degree(name) > 0: builder.add_operands(operands)

        operands = inner_digraph.predecessors(name)

    # mark inputs/outputs
    builder.mark_inputs(legacy_graph.input_dict.values())
    builder.mark_outputs(legacy_graph.output_dict.values())

    return builder


def iograph_from_legacy(l_graph: AnnotatedGraph) -> IOGraph:
    # return = IOGraph(_nodes_from_inner_legacy(l_graph.graph),
    #                   l_graph.input_dict.values(),
    #                   l_graph.output_dict.values())

    return _builder_from_legacy(l_graph).build(IOGraph)


def sgraph_from_legacy(l_graph: AnnotatedGraph) -> SGraph:
    # return SGraph(_nodes_from_inner_legacy(l_graph.subgraph),
    #               l_graph.input_dict.values(),
    #               l_graph.output_dict.values())
    return _builder_from_legacy(l_graph).build(SGraph)
