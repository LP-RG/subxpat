from typing import Dict, List, Tuple
from dataclasses import dataclass, fields
import itertools as it

from sxpat.graph import *
from sxpat.graph.node import *
from sxpat.converting.utils import set_prefix_new
from sxpat.solvers import QbfSolver
from sxpat.specifications import Specifications
from sxpat.utils.collections import iterable_replace


@dataclass(frozen=True)
class Interval:
    l_bound: int
    u_bound: int

@dataclass(frozen=True)
class Zone:
    input_1: Interval
    input_2: Interval


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
        self.reference = set_prefix_new(reference, 'ref_', it.chain(reference.inputs_names))
        self.to_be_labelled = to_be_labelled
        self._minimise = specs.min_labeling
        self._specs = specs

    def label_node(self, node_to_label: str, zone_intervals: Zone = None, fixed_bits_dict: Dict[str, BoolConstant] = None) -> int:
        question = [
            *self._define_question(node_to_label, zone_intervals, fixed_bits_dict)
        ]
        status, model = QbfSolver.solve(question, self._specs)
        if status == 'unsat':
            return 0
        return model['weight']

    def label_all_zones(self, node_to_label: str, zones_with_fixed_bits: List[Tuple[Zone, Dict[str, BoolConstant]]]) -> Dict[Zone, int]:
        zone_weights = {}
        for zone, fixed_bits_dict in zones_with_fixed_bits:
            weight = self.label_node(node_to_label, zone, fixed_bits_dict)
            if weight is not None:
                zone_weights[zone] = weight
        return zone_weights

    def label_graph(self, **kwargs) -> Dict[str, int]:
        raise NotImplementedError('To be done later')

    def _define_question(self, node_to_label: str, zone_intervals: Zone, fixed_bits_dict: Dict[str, BoolConstant] = None):
        if node_to_label not in self.to_be_labelled:
            raise ValueError(f'Node {node_to_label} not found in circuit')

        unrelevant_input_dict = fixed_bits_dict if fixed_bits_dict is not None else {}

        # Lista di BoolConstant congelati
        unrelevant_input = list(unrelevant_input_dict.values())
        unrelevant_input_names = tuple(unrelevant_input_dict.keys())

        # Gli input rilevanti per il solver sono solo quelli NON congelati
        relevant_inputs = tuple(
            inp.name for inp in self.to_be_labelled.inputs 
            if inp.name not in unrelevant_input_dict
        )

        # > define "broken" circuit
        not_node = Not(f'not_{node_to_label}', operands=[node_to_label])
        
        updated_nodes: Dict[str, Node] = dict()
        for succ in self.to_be_labelled.successors(node_to_label):
            new_operands = iterable_replace(succ.operands, node_to_label, not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)

        # Costruzione dei circuiti
        ref_circuit = IOGraph(
            it.chain(
                unrelevant_input,
                (n for n in self.reference.nodes if n.name not in unrelevant_input_names)
            ),
            relevant_inputs,
            self.reference.outputs_names,
            ()
        )
        
        broken_circuit = PGraph(
            it.chain(
                unrelevant_input,
                (
                    n for n in self.to_be_labelled.nodes
                    if n.name not in updated_nodes and n.name not in unrelevant_input_names
                ),
                (not_node,),
                updated_nodes.values(),
            ),
            relevant_inputs,
            self.to_be_labelled.outputs_names,
            ()
        )

        # > define the constraints (error and rules)
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

        # > zone constraints
        in_zone = []
        in_zone_constraints = []
        final_zone_conditions = []
        
        if zone_intervals:
            num_inputs = len(self.to_be_labelled.inputs_names)
            half_inputs = num_inputs // 2
            
            input_nodes = {
                "input_1": ToInt('input_one_value', operands=self.to_be_labelled.inputs_names[:half_inputs]),
                "input_2": ToInt('input_two_value', operands=self.to_be_labelled.inputs_names[half_inputs:])
            }
            in_zone.extend(input_nodes.values())
        
            for field_obj in fields(zone_intervals):
                field = getattr(zone_intervals, field_obj.name)
                curr_input_node = input_nodes[field_obj.name]

                min_bound_const = IntConstant(f'{field_obj.name}_min_bound', value=field.l_bound)
                max_bound_const = IntConstant(f'{field_obj.name}_max_bound', value=field.u_bound)

                ge_input = GreaterEqualThan(f"greater_or_equal_then_bound_{field_obj.name}", operands=(curr_input_node.name, min_bound_const.name))
                le_input = LessEqualThan(f"less_or_equal_then_bound_{field_obj.name}", operands=(curr_input_node.name, max_bound_const.name))

                final_input_condition = And(f"{field_obj.name}_in_zone", operands=(ge_input, le_input))

                in_zone.extend([min_bound_const, max_bound_const, ge_input, le_input, final_input_condition])
                final_zone_conditions.append(final_input_condition)

            final_condition = And("final_in_zone_condition", operands=(final_zone_conditions[0].name, final_zone_conditions[1].name))
            in_zone.append(final_condition)
            in_zone_constraints.append(Constraint.of(final_condition))

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

        return (ref_circuit, broken_circuit, constraint_graph)