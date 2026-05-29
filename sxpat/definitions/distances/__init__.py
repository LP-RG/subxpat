"""
    ### Distance definitions

    This module contains all the distance (error) functions we have implemented.

    Some functions may have specific requirements (weights, number of outputs, ...)
    but all of them share the same interface: `cls.define(IOGraph, IOGraph) -> Tuple[CGraph, str]`

    @authors: Marco Biasion
"""
from sxpat.specifications import Specifications, DistanceType
from typing import Type

# interface
from .DistanceSpecification import DistanceSpecification
# implementations
from .AbsoluteDifferenceOfInteger import AbsoluteDifferenceOfInteger
from .RelativeDifferenceOfIntegerBinary import make_relative_distance
from .AbsoluteDifferenceOfWeightedSum import AbsoluteDifferenceOfWeightedSum
from .HammingDistance import HammingDistance
from .WeightedHammingDistance import WeightedHammingDistance


def get_specialized(specs: Specifications) -> Type[DistanceType]:
    return {
        DistanceType.ABSOLUTE_DIFFERENCE_OF_INTEGERS: AbsoluteDifferenceOfInteger,
        DistanceType.ABSOLUTE_DIFFERENCE_OF_WEIGHTED_SUM: AbsoluteDifferenceOfWeightedSum,
        DistanceType.HAMMING_DISTANCE: HammingDistance,
        DistanceType.WEIGHTED_HAMMING_DISTANCE: WeightedHammingDistance,
        DistanceType.RELATIVE_DIFFERENCE_OF_INTEGERS_BINARY: make_relative_distance(specs.binary_part),
    }[specs.distance]


def get_threshold(specs: Specifications) -> int:
    return {
        DistanceType.ABSOLUTE_DIFFERENCE_OF_INTEGERS: specs.et,
        DistanceType.ABSOLUTE_DIFFERENCE_OF_WEIGHTED_SUM: specs.et,
        DistanceType.HAMMING_DISTANCE: specs.et,
        DistanceType.WEIGHTED_HAMMING_DISTANCE: specs.et,
        DistanceType.RELATIVE_DIFFERENCE_OF_INTEGERS_BINARY: 0,
    }[specs.distance]