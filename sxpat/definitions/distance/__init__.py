"""
    ### Distance definitions

    This module contains all the distance (error) functions we have implemented.

    Some functions may have specific requirements (weights, number of outputs, ...)
    but all of them share the same interface: `cls.define(IOGraph, IOGraph) -> Tuple[CGraph, str]`

    @authors: Marco Biasion
"""

from .DistanceSpecification import DistanceSpecification
from .AbsoluteDifferenceOfInteger import AbsoluteDifferenceOfInteger
from .AbsoluteDifferenceOfWeightedSum import AbsoluteDifferenceOfWeightedSum
from .HammingDistance import HammingDistance
from .WeightedHammingDistance import WeightedHammingDistance

__all__ = [
    # interface
    'DistanceSpecification',
    # implementations
    'AbsoluteDifferenceOfInteger',
    'AbsoluteDifferenceOfWeightedSum',
    'HammingDistance',
    'WeightedHammingDistance',
]
