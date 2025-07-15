from typing import Sequence

import itertools as it

from sxpat.definitions.distances.DistanceSpecification import DistanceSpecification
from sxpat.graph.graph import CGraph, IOGraph, PGraph
from sxpat.graph.node import Constraint, ForAll, IntConstant, LessEqualThan, Target


def exists_parameters_under_et(
        reference_circuit: IOGraph,
        parametric_circuit: PGraph,
        distance_definition: DistanceSpecification,
        error_threshold: int,
) -> Sequence[CGraph]:
    """
        Given a reference and a parametric circuit, a distance definition, and an error threshold,
        generate the question for the standard SubXPAT problem.

        @authors: Marco Biasion
    """

    # define distance
    (dist_function, dist_name) = distance_definition.define(reference_circuit, parametric_circuit)

    # add parameters as targets
    targets = [
        Target.of(param)
        for param in parametric_circuit.parameters_names
    ]

    # define error condition
    error_condition = [
        et := IntConstant('que_error_threshold', value=error_threshold),
        err_check := LessEqualThan('que_error_condition', operands=[dist_name, et]),
        Constraint('que_constraint_error_condition', operands=[err_check]),
    ]

    # define other specifics
    specifics = [
        ForAll('que_quantifier', operands=reference_circuit.inputs_names),
    ]

    return (
        dist_function,
        CGraph(it.chain(
            targets,
            error_condition,
            specifics,
        ))
    )
