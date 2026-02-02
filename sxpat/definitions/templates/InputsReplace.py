from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

# from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace

class InputsReplace:

        
    @classmethod
    def define(cls, current: IOGraph, specs_obj: Specifications, selected_nodes, replace_output=True, replace_with_constant=None):
        for selected_node in selected_nodes:
            assert selected_node in current, "Nodes requested to change must be in subgraph"
            if not isinstance(current[selected_node], BoolVariable):
                raise ValueError(f"Node '{selected_node}' isn't an input")
        a_graph: SGraph = set_prefix_new(current, 'a_', it.chain(current.inputs_names) if replace_output else it.chain(current.inputs_names, current.outputs_names))
       
        if replace_with_constant is not None:
            identity_node = BoolConstant(f'constant_ID', value=replace_with_constant)
        elif not specs_obj.slash_inputs_false:
            identity_node = BoolVariable(f'constant_ID')
        else:
            identity_node = BoolConstant(f'constant_ID',value=False)
 
        updated_nodes: dict[str, Node] = dict()
        for selected_node in selected_nodes:
            selected_node_name = 'ID' + selected_node 
            for succ in a_graph.successors(selected_node):
                if succ.name in updated_nodes:
                    succ = updated_nodes[succ.name]
                new_operands = iterable_replace(succ.operands, succ.operands.index(selected_node), identity_node.name)
                updated_nodes[succ.name] = succ.copy(operands=new_operands)
       
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (identity_node,),
                updated_nodes.values(),
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            [x for x in selected_nodes] if replace_with_constant is None and not specs_obj.slash_inputs_false else [],
        )
       
        new_nodes = [
            cur_int := ToInt('cur_int', operands=current.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            et := IntConstant('et_const', value=specs_obj.error_for_slash),
            less_than := LessEqualThan('less_than', operands=(abs_diff.name, et.name)),
            Constraint.of(less_than),
        ]

        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    current.outputs_names,
                    current.inputs_names,
                    template_graph.outputs_names,
                    (identity_node.name,),
                )),
                new_nodes,
                (Target.of(identity_node),) if not specs_obj.slash_inputs_false else (),
                (Target.of(abs_diff),),
                [ForAll('forall_inputs', operands=current.inputs_names)],
            )
        )
       
        return (template_graph, constraint_graph)