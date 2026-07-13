from typing import ClassVar, Mapping, Dict, List, Tuple
from dataclasses import dataclass, fields

import itertools as it

from sxpat.graph import *
from sxpat.graph.node import *

from sxpat.converting.utils import set_prefix_new
from sxpat.solvers.Z3Solver import Z3DirectIntSolver
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace


__all__ = ['Labelling']

#Interval data class
@dataclass
class Interval:
    l_bound: int
    u_bound: int

#zone data class
@dataclass
class Zone:
    input_1 : Interval
    input_2 : Interval


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





  
    def zone_generator(self, input1_interval:Tuple[int, int], input2_interval:Tuple[int, int], beta:int)-> List[Zone]:
        """
           Splits the total input space into a grid of smaller zones.
           The density and number of generated zones depend on the beta step size.
           It outputs A list containing the generated zone dataclasses mapping out the grid.
        """
    
        # MARCO:REVIEW:
        #   - to add a docstring (similar to what you did in pyret) you can use a string at the beginning of the function (e.g., "some description blabla")
        #   - a more extensive usage of type annotations would be better, that allows other people (or future you) to more easily understand and use your functions
        #     - you can take a look at other functions, or at the documentation for python (https://docs.python.org/3/library/typing.html)
        #     - you could also improve the understandability of your code by using custom classes (e.g., for the zone), I suggest looking at dataclasses (https://docs.python.org/3/library/dataclasses.html)
        #   - a few more comments in the code would be helpful
        
        #defines the lower and upper bounds of whole input space
        l_bound1, u_bound1 = input1_interval
        l_bound2, u_bound2 = input2_interval

        #spilting of the input space
        num_steps = 256 // beta
        
        #cration of intervals of inputs
        all_zones=[]
        

        #iterating the whole input space and creating a grid
        for start1 in range(l_bound1, u_bound1+1, num_steps):
            end1 = min(start1 + beta - 1, u_bound1)

            for start2 in range(l_bound2, u_bound2+1, num_steps):
                end2= min(start2 + beta - 1, u_bound2)

                all_zones.append(
                    Zone(Interval(start1, end1), Interval(start2, end2))
                )
        return all_zones

    def label_node(self, node_to_label: str, zone_intervals:Zone = None) -> int:
        """
        Evaluates a specific node within an input zone to calculate its weight.
        """
        # MARCO:REVIEW:
        #   - if you want to simplify the default value for zone_intervals, you can directly replace the None with the empty dictionary in the signature
        #     there are situations where your approach is needed, but for most situations the simpler alternative is better

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

    def label_all_zones(self, node_to_label:str, input1_zone:Tuple[int, int], input2_zone:Tuple[int,int], beta:int) -> Dict[str, int]:
        """
        Iterates over the entire partitioned input space to calculate the error weight of a node in every zone.

        Generates a grid of input zones based on the beta step size and evaluates the target 
        node within each specific boundary using the Z3 solver. Zones that return a valid 
        weight are recorded.
        """
        zone_weights={}

        #for every zone the node is labelled with a weight 
        for zone in self.zone_generator(input1_zone, input2_zone, beta):
            weight = self.label_node(node_to_label, zone)

            if weight is not None:
               zone_weights[str(zone)] = weight
        return zone_weights

    def label_graph(self) -> Mapping[str, int]:
        raise NotImplementedError('To be done later')

    def _define_question(self, node_to_label: str, zone_intervals: Zone):
        # > guards
        if node_to_label not in self.to_be_labelled:
            raise ValueError(f'Node {node_to_label} not found in circuit')

        # > define "broken" circuit (the behaviour)
        # define target node
        not_node = Not(f'not_{node_to_label}', operands=[node_to_label])
        # update successors of target node
        updated_nodes: Dict[str, Node] = dict()
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

        # MARCO:REVIEW:
        #   - the code is correct, I have left a few comments next to where it is relevant
        #   - a suggestion I give you is to implement this logic (the logic of creating all nodes for the zone constraints) in a new function (this will help in the future, so it is not required that you do it now)

        #zone constraint

        in_zone=[]
        in_zone_constraints =[]
        final_zone_conditions=[]
        if zone_intervals:

            input_nodes = {
                "input_1": ToInt('input_one_value', operands=self.to_be_labelled.inputs_names[:len(self.to_be_labelled.inputs_names)//2]),
                "input_2": ToInt('input_two_value', operands=self.to_be_labelled.inputs_names[len(self.to_be_labelled.inputs_names)//2:])
            }
            in_zone.extend(input_nodes.values())
        
            for field_obj in fields(zone_intervals):

                field = getattr(zone_intervals, field_obj.name)

                curr_input_node = input_nodes[field_obj.name]

                int_min_bound = field.l_bound
                int_max_bound = field.u_bound

                min_bound_const = IntConstant(f'{field_obj.name}_min_bound', value = int_min_bound)
                max_bound_const = IntConstant(f'{field_obj.name}_max_bound', value = int_max_bound)

                ge_input = GreaterEqualThan(f"greater_or_equal_then_bound_{field_obj.name}", operands=(curr_input_node.name, min_bound_const.name))
                le_input = LessEqualThan(f"less_or_equal_then_bound{field_obj.name}", operands=(curr_input_node.name, max_bound_const.name))

                final_input_condition = And(f"{field_obj.name}_in_zone", operands=(ge_input, le_input))

                in_zone.extend([min_bound_const, max_bound_const, ge_input, le_input, final_input_condition])

                final_zone_conditions.append(final_input_condition)

            # MARCO:COMMENT: as the core logic for the two zones is the same, it may be beneficial to generalize a bit the implementation, such that you can then generate both constraints with the same code
            # MARCO:COMMENT: if you want to implement the approach of a custom type (as described in the review of zone_generator), the implementation might slightly change

            
               

            # MARCO:COMMENT: as the "square" zones are always defined by two ranges (one for each input), you can simplify a bit your implementation by removing a few checks (both here and above)
            final_condition = And("final_in_zone_condition", operands=(final_zone_conditions[0].name, final_zone_conditions[1].name))
            in_zone.append(final_condition)
            in_zone_constraints.append(Constraint.of(final_condition))
            # MARCO:COMMENT: is this statement redundant, in the situation where the execution entered in the previous `if`?
          
        



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
