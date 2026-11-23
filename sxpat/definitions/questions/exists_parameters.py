from typing import List, Sequence, Type, Union

import itertools as it
from sxpat.utils.decorators import make_utility_class

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph.node import AnyNode, Constraint, ForAll, GreaterEqualThan, GreaterThan, IntConstant, LessEqualThan, LessThan, PlaceHolder, Target
from sxpat.definitions.distances.DistanceSpecification import DistanceSpecification
from sxpat.graph.components import Constraints


__all__ = ['exists_parameters']


@make_utility_class
class exists_parameters:
    @classmethod
    def _define(cls,
                reference_circuit: Graph,
                parametric_circuit: Graph,
                distance_definition: DistanceSpecification,
                threshold: int,
                comparison_type: Type[Union[LessThan, LessEqualThan, GreaterThan, GreaterEqualThan]],
                do_forall: bool,
                ) -> Sequence[Graph]:
        """@authors: Marco Biasion"""

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # define distance
        (dist_function, dist_name) = distance_definition.define(reference_circuit, parametric_circuit)

        # generate all other question components

        # add parameters as targets (and relative placeholders)
        for param in parametric_circuit.base_components['Parameter'].parameters_names:
            graph_builder.add_node(param, PlaceHolder)
            target_name, operands = Target.of(param)
            graph_builder.add_node(target_name, Target).add_operands(operands)

        # define error condition (and relative placeholders)
        graph_builder.add_node(dist_name, PlaceHolder)
        et = graph_builder.add_node('que_threshold', IntConstant).add_extras(value=threshold).current
        err_check = graph_builder.add_node('que_condition', comparison_type).add_operands([dist_name, et.name]).current
        graph_builder.add_node('que_condition_constraint', Constraint).add_operands([err_check.name])

        # define forall quantifier (and relative placeholders) if required
        if do_forall:
            for inp in reference_circuit.base_components['IO'].inputs_names:
                graph_builder.add_node(inp, PlaceHolder)
            graph_builder.add_node('que_quantifier', ForAll).add_operands(list(reference_circuit.base_components['IO'].inputs_names))
        
        return (dist_function, graph_builder.create())

    @classmethod
    def not_above_threshold_forall_inputs(cls,
                                          reference_circuit: Graph,
                                          parametric_circuit: Graph,
                                          distance_definition: DistanceSpecification,
                                          threshold: int,) -> Sequence[Graph]:
        return cls._define(
            reference_circuit, parametric_circuit,
            distance_definition, threshold, LessEqualThan,
            True
        )

    @classmethod
    def above_threshold(cls,
                        reference_circuit: Graph,
                        parametric_circuit: Graph,
                        distance_definition: DistanceSpecification,
                        threshold: int,) -> Sequence[Graph]:
        return cls._define(
            reference_circuit, parametric_circuit,
            distance_definition, threshold, GreaterThan,
            False
        )
