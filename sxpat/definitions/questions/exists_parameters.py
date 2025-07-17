from typing import List, Sequence, Type, Union

import itertools as it
from sxpat.utils.decorators import make_utility_class

from sxpat.graph import CGraph, IOGraph, PGraph
from sxpat.graph.node import AnyNode, Constraint, ForAll, GreaterEqualThan, GreaterThan, IntConstant, LessEqualThan, LessThan, PlaceHolder, Target
from sxpat.definitions.distances.DistanceSpecification import DistanceSpecification


__all__ = ['exists_parameters']


@make_utility_class
class exists_parameters:
    @classmethod
    def _define(cls,
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
        components: List[AnyNode] = list()

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
    def not_above_threshold_forall_inputs(cls,
                                          reference_circuit: IOGraph,
                                          parametric_circuit: PGraph,
                                          distance_definition: DistanceSpecification,
                                          threshold: int,) -> Sequence[CGraph]:
        return cls._define(
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
        return cls._define(
            reference_circuit, parametric_circuit,
            distance_definition, threshold, GreaterThan,
            False
        )
