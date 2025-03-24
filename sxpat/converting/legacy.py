from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.graph import SGraph
from sxpat.graph import BoolVariable, BoolConstant, And, Not, Copy
from sxpat.utils.functions import str_to_bool


__all__ = ['sgraph_from_legacy']


def sgraph_from_legacy(l_graph: AnnotatedGraph) -> SGraph:
    # get inner networkx graph with subgraph data
    inner_graph = l_graph.subgraph

    # convert nodes
    nodes = list()
    for (name, value) in inner_graph.nodes(True):
        # get features
        label = value.get('label')
        weight = value.get('weight', None)
        in_subgraph = bool(value.get('subgraph', False))
        items = inner_graph.predecessors(name)

        # create node
        if label.startswith('in'):  # input
            nodes.append(BoolVariable(name, weight, in_subgraph))
        elif label.startswith('out'):  # output
            nodes.append(Copy(name, weight, in_subgraph, items))
        elif label in ('and', 'not'):  # and/not
            cls = {'not': Not, 'and': And}[label]
            nodes.append(cls(name, weight, in_subgraph, items))
        elif label in ('FALSE', 'TRUE'):  # constant
            nodes.append(BoolConstant(name, weight, in_subgraph, str_to_bool(label)))
        else:
            raise RuntimeError(f'Unable to parse node {name} from AnnotatedGraph ({value})')

    return SGraph(nodes,
                  l_graph.input_dict.values(),
                  l_graph.output_dict.values())
