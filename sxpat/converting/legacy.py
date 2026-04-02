from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.graph import IOGraph, SGraph
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity
from sxpat.utils.functions import str_to_bool


__all__ = ['iograph_from_legacy', 'sgraph_from_legacy']


def _nodes_from_inner_legacy(inner_graph):
    nodes = list()
    for (name, value) in inner_graph.nodes(True):
        # get features
        label = value.get('label')
        weight = value.get('weight', None)
        in_subgraph = bool(value.get('subgraph', False))
        operands = inner_graph.predecessors(name)

        # create node
        if label.startswith('in'):  # input
            nodes.append(BoolVariable(name, weight, in_subgraph))
        elif label.startswith('out'):  # output
            nodes.append(Identity(name, operands, weight, in_subgraph))
        elif label in ('and', 'not'):  # and/not
            cls = {'not': Not, 'and': And}[label]
            nodes.append(cls(name, operands, weight, in_subgraph))
        elif label in ('FALSE', 'TRUE'):  # constant
            nodes.append(BoolConstant(name, str_to_bool(label), weight, in_subgraph))
        else:
            raise RuntimeError(f'Unable to parse node {name} from AnnotatedGraph ({value})')

    return nodes


def iograph_from_legacy(l_graph: AnnotatedGraph) -> IOGraph:
    return IOGraph(_nodes_from_inner_legacy(l_graph.graph),
                   l_graph.input_dict.values(),
                   l_graph.output_dict.values())


def sgraph_from_legacy(l_graph: AnnotatedGraph) -> SGraph:
    return SGraph(_nodes_from_inner_legacy(l_graph.subgraph),
                  l_graph.input_dict.values(),
                  l_graph.output_dict.values())
