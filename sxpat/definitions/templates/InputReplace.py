from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

# from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labeling']

class InputReplace:

        
    @classmethod
    def define(cls, current: IOGraph,specs_obj: Specifications, selected_node, replace_output=True):
        assert selected_node in current, "Node requested to label must be in the graph"
        if not isinstance(current[selected_node], BoolVariable):
            raise ValueError(f"Node '{selected_node}' isn't an input")
        a_graph: SGraph = set_prefix_new(current, 'a_', it.chain(current.inputs_names) if replace_output else it.chain(current.inputs_names, current.outputs_names))
       
        selected_node_name = 'ID' + selected_node 
        if not specs_obj.slash_inputs_false:
            identity_node = BoolVariable(f'ID_{selected_node}')
        else:
            identity_node = BoolConstant(f'ID_{selected_node}',value=False)
 
        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(selected_node):
            new_operands = iterable_replace(succ.operands, succ.operands.index(selected_node), identity_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        constraint_nodes = []
        nodes_to_place_hold = []

        constants_parameters = []

        for const in a_graph.constants:
            # if the constants is at the graph output
            if len(succs := a_graph.successors(const)) == 1 and (out_i := a_graph.output_index_of(succ := succs[0])) >= 0:
                constants_parameters.append(const_rew := BoolVariable(f'p_c{out_i}'))
                updated_nodes[succ.name] = succ.copy(operands=(const_rew,))  # by definition, the output node has no other operand
       
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (identity_node,),
                updated_nodes.values(),
                constraint_nodes,
                constants_parameters,
            ),
            a_graph.inputs_names,
            a_graph.outputs_names,
            it.chain(
                constants_parameters,
                (selected_node_name,) if not specs_obj.slash_inputs_false else (),
            )
        )
       
        new_nodes = [
            cur_int := ToInt('cur_int', operands=current.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            et := IntConstant('et_const', value=specs_obj.et),
            less_than := LessEqualThan('less_than', operands=(abs_diff.name, et.name)),
            Constraint.of(less_than),
        ]

        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    current.outputs_names,
                    current.inputs_names,
                    template_graph.outputs_names,
                    nodes_to_place_hold,
                    (identity_node.name,),
                    [x.name for x in constants_parameters]
                )),
                new_nodes,
                (Target.of(identity_node),) if not specs_obj.slash_inputs_false else (),
                [Target.of(x) for x in constants_parameters],
                [ForAll('forall_inputs', operands=current.inputs_names)],
            )
        )
       
        return (template_graph, constraint_graph)