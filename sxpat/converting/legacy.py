import networkx as nx

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity
from sxpat.utils.functions import str_to_bool
from sxpat.graph.components import IO


__all__ = [
    'graph_from_digraph',
]

def graph_from_digraph(clean_digraph: nx.DiGraph) -> Graph:
    """
        @authors: Ilia Zeller
    """
    gtypes = {'not': Not, 'and': And}

    # construct nodes and extract inputs/outputs
    graph_builder = GraphBuilder()
    inputs_names = list()
    outputs_names = list()
    for (node, attrs) in clean_digraph.nodes(True):
        ntype = attrs.get('type')

        if ntype == 'input':
            inputs_names.append(node)
            graph_builder.add_node(node, BoolVariable)
        elif ntype == 'output':
            outputs_names.append(node)
            graph_builder.add_node(node, Identity).add_operands(list(clean_digraph.predecessors(node)))
        elif ntype == 'gate':
            cls = gtypes[attrs.get('label')]
            graph_builder.add_node(node, cls).add_operands(list(clean_digraph.predecessors(node)))
        elif ntype == 'constant':
            graph_builder.add_node(node, BoolConstant).add_extras(value=str_to_bool(attrs.get('label')))
        else:
            raise RuntimeError(f'Unable to parse node {node} from DiGraph (attributes={attrs})')

    # construct graph
    graph_builder.add_base_component(IO({'inputs_names': sorted(inputs_names, key=lambda x: int(x[2:])),
                                         'outputs_names': sorted(outputs_names, key=lambda x: int(x[3:]))}))
    return graph_builder.create()

def graph_from_digraph_testing(clean_digraph: nx.DiGraph, info: list) -> Graph:
    """
        Version of graph_from_digraph used for performance testing

        @authors: Ilia Zeller
    """
    gtypes = {'not': Not, 'and': And}

    num_inputs = 0
    num_outputs = 0 
    num_gates = 0
    num_constants = 0
    
    # construct nodes and extract inputs/outputs
    graph_builder = GraphBuilder()
    inputs_names = list()
    outputs_names = list()
    for (node, attrs) in clean_digraph.nodes(True):
        ntype = attrs.get('type')

        if ntype == 'input':
            num_inputs += 1
            inputs_names.append(node)
            graph_builder.add_node(node, BoolVariable)
        elif ntype == 'output':
            num_outputs += 1
            outputs_names.append(node)
            graph_builder.add_node(node, Identity).add_operands(list(clean_digraph.predecessors(node)))
        elif ntype == 'gate':
            num_gates += 1
            cls = gtypes[attrs.get('label')]
            graph_builder.add_node(node, cls).add_operands(list(clean_digraph.predecessors(node)))
        elif ntype == 'constant':
            num_constants += 1
            graph_builder.add_node(node, BoolConstant).add_extras(value=str_to_bool(attrs.get('label')))
        else:
            raise RuntimeError(f'Unable to parse node {node} from DiGraph (attributes={attrs})')

    info.extend([str(num_inputs), str(num_outputs), str(num_gates), str(num_constants)])
    
    # construct graph
    graph_builder.add_base_component(IO({'inputs_names': sorted(inputs_names, key=lambda x: int(x[2:])),
                                            'outputs_names': sorted(outputs_names, key=lambda x: int(x[3:]))}))
    return graph_builder.create()

# COMMENT:from-MARCO: good to leave these commented out for now, we will remove it at the end

# def _my_nodes_from_inner_legacy(inner_graph):
#     nodes = list()
#     for (index, data) in inner_graph.nodes(True):
#         # get features
#         weight = data.get('weight', None)
#         in_subgraph = bool(data.get('subgraph', False))
#         operands = inner_graph.predecessors(index)
#         node_type = data.get('type')
#         # "type" -> [const, pi, gate, po]

#         # create node
#         if node_type[1]:  # input
#             nodes.append(BoolVariable(index, weight, in_subgraph))
#         elif node_type[3]:  # output
#             nodes.append(Identity(index, operands, weight, in_subgraph))
#         elif node_type[2] == 1:  # and
#             nodes.append(And(index, operands, weight, in_subgraph))
#         elif node_type[2] == 2:  # not
#             nodes.append(Not(index, operands, weight, in_subgraph))
#         elif node_type[0]:  # constant
#             nodes.append(BoolConstant(index, True, weight, in_subgraph))
#         else:
#             raise RuntimeError(f'Unable to parse node {index} from AnnotatedGraph ({data})')

#     return nodes


# def iograph_with_weights(graph: IOGraph, weights: Mapping[str, int]) -> IOGraph:
#     return graph.copy(
#         node.copy(weight=weights.get(node.name, None))
#         for node in graph.nodes
#     )

# def my_iograph_from_legacy(l_graph) -> IOGraph:
#     return IOGraph(_my_nodes_from_inner_legacy(l_graph.graph),
#                    l_graph.input_dict.values(),
#                    l_graph.output_dict.values())

# def iograph_to_sgraph(graph: IOGraph, subgraph_nodes: Iterable[str]) -> SGraph:
#     subgraph_nodes = frozenset(subgraph_nodes)
#     return SGraph(
#         (
#             node.copy(in_subgraph=node.name in subgraph_nodes)
#             for node in graph.nodes
#         ),
#         graph.inputs_names,
#         graph.outputs_names,
#     )
