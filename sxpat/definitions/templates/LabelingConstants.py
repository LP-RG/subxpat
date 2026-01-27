from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

# from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labeling']

class Labeling:

        
    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications, accs=[], direction: int = 0):
        """
        direction is 1 if you want the positive error, -1 if you want the negative
        and 0 if you want the maximum of the two
        """
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in s_graph, "Node requested to label must be in the graph"

        prefix = 'a_'
        a_graph: SGraph = set_prefix_new(s_graph, prefix, it.chain(s_graph.inputs_names))

        labeled_node = accs[0]
        labeled_node_name = labeled_node if labeled_node[:2] == 'in' else prefix + labeled_node 
        not_node = BoolVariable(f'variable_{labeled_node}')
 
        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace(succ.operands, succ.operands.index(labeled_node_name), not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        


        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            (node.name for node in updated_nodes.values() if isinstance(node, BoolVariable))
        )
       
        new_nodes = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            Min('minimize_error', operands=(abs_diff.name,)),
        ]
       
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    s_graph.inputs_names,
                    s_graph.outputs_names,
                    template_graph.outputs_names,
                    (node.name for node in updated_nodes.values() if isinstance(node, BoolVariable)),
                )),
                (ForAll('for_all_inputs', operands=a_graph.inputs_names),),
                new_nodes,
                it.chain(
                    (Target.of(abs_diff),),
                    (Target.of(node) for node in updated_nodes.values() if isinstance(node, BoolVariable))
                )
            )
        )
       
        return (template_graph, constraint_graph)