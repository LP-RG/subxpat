from typing import Dict, List, Sequence, Tuple, Union

import itertools as it

# from .Template import Template

from sxpat.converting.utils import set_prefix_new
from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.specifications import ConstantsType, Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labeling']

class Labeling:

        
    @classmethod
    def define(cls, s_graph: SGraph,accs=[], min_labeling = False, ):
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in s_graph, "Node requested to label must be in the graph"
        if accs[0] not in s_graph:
            raise ValueError(f"Node '{accs[0]}' not found in graph")
        a_graph: SGraph = set_prefix_new(s_graph, 'a_', it.chain(s_graph.inputs_names))
       
        labeled_node = accs[0]
        labeled_node_name =labeled_node if  labeled_node[:2] == 'in' else 'a_' + labeled_node 
        not_node = Not(f'not_{labeled_node}', operands=(labeled_node_name,))
 
        updated_nodes: dict[str, Node] = dict()
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace(succ.operands, succ.operands.index(labeled_node_name), not_node.name)
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
                # Constraint.of(gt),
            ])

        zone_intervals = {"input_1": (0,10), "input_2": (0,20)}

        in_zone=[]
        if zone_intervals:
            input_one_value = ToInt('input_one_value', operands=s_graph.inputs_names[:len(s_graph.inputs_names)//2])
            input_two_value = ToInt('input_two_value', operands=s_graph.inputs_names[len(s_graph.inputs_names)//2:])

            if "input_1" in zone_intervals:
                min_bound, max_bound = zone_intervals["input_1"]

                min_bound_const = IntConstant('min_bound', value = min_bound)
                max_bound_const = IntConstant('max_bound', value = max_bound)

                ge_input1 = GreaterEqualThan("greater_or_equal_then_bound", operands=(input_one_value, min_bound))
                le_input1 = LessEqualThan("less_or_equal_then_bound", operands=(input_one_value, max_bound))

                final_input1_condition = And("input1_in_zone", operands=(ge_input1, le_input1))

                in_zone.extend([min_bound_const, max_bound_const, ge_input1, le_input1, final_input1_condition])
            if "input_2" in zone_intervals:
                min_bound, max_bound = zone_intervals["input_2"]

                min_bound_const = IntConstant('min_bound', value = min_bound)
                max_bound_const = IntConstant('max_bound', value = max_bound)

                ge_input2 = GreaterEqualThan("greater_or_equal_then_bound", operands=(input_two_value, min_bound))
                le_input2 = LessEqualThan("less_or_equal_then_bound", operands=(input_two_value, max_bound))

                final_input2_condition = And("input2_in_zone", operands=(ge_input2, le_input2))

                in_zone.extend([min_bound_const, max_bound_const, ge_input2, le_input2, final_input2_condition])

            final_condition = And("final_in_zone_condition", operands=(final_input1_condition, final_input2_condition))
            in_zone.append(final_condition)

       
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names,
                    nodes_to_place_hold
                )),
                in_zone,
                new_nodes,
                # [Target.of(abs_diff),]
                [Target(name="target_of_abs_diff", operands=(abs_diff.name,)),]
            )
        )
       
        return (template_graph, constraint_graph)