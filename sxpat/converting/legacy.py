from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.graph import IOGraph, SGraph
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity
from sxpat.utils.functions import str_to_bool


__all__ = ['iograph_from_legacy', 'sgraph_from_legacy', 'my_iograph_from_legacy']


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


def iograph_from_legacy(l_graph: AnnotatedGraph) -> IOGraph:
    return IOGraph(_nodes_from_inner_legacy(l_graph.graph),
                   l_graph.input_dict.values(),
                   l_graph.output_dict.values())

def my_iograph_from_legacy(l_graph, inputs_names, outputs_names) -> IOGraph:
    return IOGraph(_my_nodes_from_inner_legacy(l_graph.graph),
                   inputs_names,
                   outputs_names)

def sgraph_from_legacy(l_graph: AnnotatedGraph) -> SGraph:
    return SGraph(_nodes_from_inner_legacy(l_graph.subgraph),
                  l_graph.input_dict.values(),
                  l_graph.output_dict.values())
