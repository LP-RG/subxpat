from aiger.my_graph.node import BoolVariable, BoolConstant, And, Not, Identity
from aiger.my_graph.graph import IOGraph


__all__ = ['my_iograph_from_legacy']

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

def my_iograph_from_legacy(l_graph) -> IOGraph:
    return IOGraph(_my_nodes_from_inner_legacy(l_graph.graph))
