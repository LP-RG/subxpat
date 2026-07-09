from typing import ClassVar, Mapping

import itertools as it

from sxpat.graph import *
from sxpat.graph.node import *

from sxpat.converting.utils import set_prefix_new
from sxpat.solvers.Z3Solver import Z3DirectIntSolver
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labelling']


class Labelling:
    """
        :authors: Marco Biasion, Lorenzo Spada
    """

    __slots__ = [
        'reference', 'to_be_labelled',
        '_minimise', '_specs',
    ]

    def __init__(
        self,
        reference: IOGraph, to_be_labelled: IOGraph,
        *,
        specs: Specifications,
    ):
        # store
        self.reference = set_prefix_new(reference, 'ref_', it.chain(reference.inputs_names))
        self.to_be_labelled = to_be_labelled
        #
        self._minimise = specs.min_labeling
        self._specs = specs

    #splitting the input space into zones
    def zone_generator(self, input1_interval, input2_interval, beta:int):
        l_bound1, u_bound1 = input1_interval
        l_bound2, u_bound2 = input2_interval
        all_zones=[]
        num_steps = 256 // beta

        for start1 in range(l_bound1, u_bound1+1, num_steps):
            end1 = min(start1 + beta - 1, u_bound1)

            for start2 in range(l_bound2, u_bound2+1, num_steps):
                end2= min(start2 + beta - 1, u_bound2)

                all_zones.append({
                    "input_1": (start1, end1),
                    "input_2": (start2, end2)
                })
        return all_zones

    def label_node(self, node_to_label: str, zone_intervals:dict = None) -> int:

        if zone_intervals == None:
            zone_intervals = {}

        # define question
        question = [
            self.reference,
            *self._define_question(node_to_label, zone_intervals)
        ]

        # run solver
        status, model = Z3DirectIntSolver.solve(question, self._specs)
      
        assert status == 'sat'
     

        # extract node weight
        return model['weight']

    #iterating through all the zones

    def label_all_zones(self, node_to_label:str, input1_zone, input2_zone, beta):


        zone_weights={}
        for zone in self.zone_generator(input1_zone, input2_zone, beta):
            weight = self.label_node(node_to_label, zone)

            if weight is not None:
                zone_weights[(zone["input_1"], zone["input_2"])] = weight
        return zone_weights

    def label_graph(self) -> Mapping[str, int]:
        raise NotImplementedError('To be done later')

    def _define_question(self, node_to_label: str, zone_intervals: dict):
        # > guards
        if node_to_label not in self.to_be_labelled:
            raise ValueError(f'Node {node_to_label} not found in circuit')

        # > define "broken" circuit (the behaviour)
        # define target node
        not_node = Not(f'not_{node_to_label}', operands=[node_to_label])
        # update successors of target node
        updated_nodes: dict[str, Node] = dict()
        for succ in self.to_be_labelled.successors(node_to_label):
            new_operands = iterable_replace(succ.operands, node_to_label, not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        # construct circuit
        broken_circuit = PGraph(
            it.chain(
                (
                    n
                    for n in self.to_be_labelled.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
            ),
            self.to_be_labelled.inputs_names,
            self.to_be_labelled.outputs_names,
            ()
        )

        # > define the constraints (error and rules)
        # define error function (and optimisation)
        new_nodes = [
            cur_int := ToInt('cur_int', operands=self.reference.outputs_names),
            tem_int := ToInt('tem_int', operands=broken_circuit.outputs_names),
            abs_diff := AbsDiff('weight', operands=[cur_int.name, tem_int.name]),
            {
                True: Min('minimise_error', operands=[abs_diff.name]),
                False: Max('maximise_error', operands=[abs_diff.name])
            }[self._minimise]
        ]
        if self._minimise:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=[abs_diff.name, zero.name]),
                Constraint.of(gt),
            ])

        #zone constraint

        in_zone=[]
        in_zone_constraints =[]
        if zone_intervals:
            input_one_value = ToInt('input_one_value', operands=self.to_be_labelled.inputs_names[:len(self.to_be_labelled.inputs_names)//2])
            input_two_value = ToInt('input_two_value', operands=self.to_be_labelled.inputs_names[len(self.to_be_labelled.inputs_names)//2:])

            in_zone.extend([input_one_value, input_two_value])
            
            active_conditions=[]

            if "input_1" in zone_intervals:
                int1_min_bound, int1_max_bound = zone_intervals["input_1"]

                min_bound_const = IntConstant('int1_min_bound', value = int1_min_bound)
                max_bound_const = IntConstant('int1_max_bound', value = int1_max_bound)

                ge_input1 = GreaterEqualThan("greater_or_equal_then_bound1", operands=(input_one_value.name, min_bound_const.name))
                le_input1 = LessEqualThan("less_or_equal_then_bound1", operands=(input_one_value.name, max_bound_const.name))

                final_input1_condition = And("input1_in_zone", operands=(ge_input1, le_input1))

                in_zone.extend([min_bound_const, max_bound_const, ge_input1, le_input1, final_input1_condition])
                active_conditions.append(final_input1_condition)
            if "input_2" in zone_intervals:
                int2_min_bound, int2_max_bound = zone_intervals["input_2"]

                min_bound_const = IntConstant('int2_min_bound', value = int2_min_bound)
                max_bound_const = IntConstant('int2_max_bound', value = int2_max_bound)

                ge_input2 = GreaterEqualThan("greater_or_equal_then_bound2", operands=(input_two_value.name, min_bound_const.name))
                le_input2 = LessEqualThan("less_or_equal_then_bound2", operands=(input_two_value.name, max_bound_const.name))

                final_input2_condition = And("input2_in_zone", operands=(ge_input2, le_input2))

                in_zone.extend([min_bound_const, max_bound_const, ge_input2, le_input2, final_input2_condition])
                active_conditions.append(final_input2_condition)

            if len(active_conditions) > 1:
                final_condition = And("final_in_zone_condition", operands=(final_input1_condition, final_input2_condition))
                in_zone.append(final_condition)
                in_zone_constraints.append(Constraint.of(final_condition))
            in_zone_constraints.append(Constraint.of(active_conditions[0]))
        



        # construct structure
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    self.reference.outputs_names,
                    broken_circuit.outputs_names,
                    self.to_be_labelled.inputs_names
                )),
                in_zone,
                in_zone_constraints,
                new_nodes,
                [Target.of(abs_diff)]
            )
        )

        return (broken_circuit, constraint_graph)
