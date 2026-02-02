from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

# from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace_index


__all__ = ['Labeling']

class Labeling:

        
    @classmethod
    def define(cls, s_graph: SGraph,accs=[], min_labeling = False):
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in s_graph, "Node requested to label must be in the graph"
        if accs[0] not in s_graph:
            raise ValueError(f"Node '{accs[0]}' not found in graph")
        a_graph: SGraph = set_prefix_new(s_graph, 'a_', it.chain(s_graph.inputs_names))
       
        labeled_node = accs[0]
        labeled_node_name =labeled_node if  labeled_node[:2] == 'in' else 'a_' + labeled_node 
        not_node = BoolVariable(f'not_{labeled_node}', operands=(labeled_node_name,))

        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace_index(succ.operands, succ.operands.index(labeled_node_name), not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        constraint_nodes = []
        nodes_to_place_hold = []
       
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
                constraint_nodes
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            ()
        )
       
        new_nodes = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            {
            True: Min('minimize_error', operands=(abs_diff.name,)),
            False: Max('maximize_error', operands=(abs_diff.name,))
            }[min_labeling]
        ]
       
        if min_labeling:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=(abs_diff.name, zero.name)),
                Constraint.of(gt),
            ])
       
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names,
                    nodes_to_place_hold
                )),
                new_nodes,
                [Target.of(abs_diff),]
            )
        )
       
        return (template_graph, constraint_graph)