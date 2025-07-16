from typing import Sequence, Type, Union

import itertools as it

from sxpat.definitions.distances.DistanceSpecification import DistanceSpecification
from sxpat.graph.graph import CGraph, IOGraph, PGraph
from sxpat.graph.node import Constraint, ForAll, GreaterEqualThan, GreaterThan, IntConstant, LessEqualThan, LessThan, PlaceHolder, Target
from sxpat.utils.decorators import make_utility_class


__all__ = ['exists_parameters']


@make_utility_class
class exists_parameters:

    @classmethod
    def _create_question(cls,
                         reference_circuit: IOGraph,
                         parametric_circuit: PGraph,
                         distance_definition: DistanceSpecification,
                         threshold: int,
                         comparison_type: Type[Union[LessThan, LessEqualThan, GreaterThan, GreaterEqualThan]],
                         do_forall: bool,
                         ) -> Sequence[CGraph]:
        """@authors: Marco Biasion"""

        # define distance
        (dist_function, dist_name) = distance_definition.define(reference_circuit, parametric_circuit)

        # generate all other question components
        components = list()

        # add parameters as targets (and relative placeholders)
        components.extend(it.chain.from_iterable(
            (PlaceHolder(param), Target.of(param))
            for param in parametric_circuit.parameters_names
        ))

        # define error condition (and relative placeholders)
        components.extend((
            PlaceHolder(dist_name),
            et := IntConstant('que_threshold', value=threshold),
            err_check := comparison_type('que_condition', operands=[dist_name, et]),
            Constraint('que_condition_constraint', operands=[err_check]),
        ))

        # define forall quantifier (and relative placeholders) if required
        if do_forall:
            components.extend([
                *(PlaceHolder(inp) for inp in reference_circuit.inputs_names),
                ForAll('que_quantifier', operands=reference_circuit.inputs_names),
            ])

        return (dist_function, CGraph(components))

    @classmethod
    def forall_inputs_not_above_threshold(cls,
                                          reference_circuit: IOGraph,
                                          parametric_circuit: PGraph,
                                          distance_definition: DistanceSpecification,
                                          threshold: int,) -> Sequence[CGraph]:
        return cls._create_question(
            reference_circuit, parametric_circuit,
            distance_definition, threshold, LessEqualThan,
            True
        )

    @classmethod
    def above_threshold(cls,
                        reference_circuit: IOGraph,
                        parametric_circuit: PGraph,
                        distance_definition: DistanceSpecification,
                        threshold: int,) -> Sequence[CGraph]:
        return cls._create_question(
            reference_circuit, parametric_circuit,
            distance_definition, threshold, GreaterThan,
            False
        )

    # @classmethod
    # def inside_treshold(cls,
    #                     reference_circuit: IOGraph,
    #                     parametric_circuit: PGraph,
    #                     distance_definition: DistanceSpecification,
    #                     threshold: int,
    #                     ) -> Sequence[CGraph]:
    #     """
    #         Given a reference and a parametric circuit, a distance definition, and an error threshold,
    #         generate the question for the standard SubXPAT problem.

    #         @authors: Marco Biasion
    #     """

    #     # define distance
    #     (dist_function, dist_name) = distance_definition.define(reference_circuit, parametric_circuit)

    #     # add parameters as targets (and relative placeholders)
    #     targets = cls._create_targets(parametric_circuit.parameters_names)

    #     # define error condition (and relative placeholders)
    #     error_condition = cls._create_threshold_condition(dist_name, threshold, LessEqualThan)

    #     # define other specifics  (and relative placeholders)
    #     specifics = [
    #         *(PlaceHolder(inp) for inp in reference_circuit.inputs_names),
    #         ForAll('que_quantifier', operands=reference_circuit.inputs_names),
    #     ]

    #     return (
    #         dist_function,
    #         CGraph(it.chain(
    #             targets,
    #             error_condition,
    #             specifics,
    #         ))
    #     )
