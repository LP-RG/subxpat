"""
    ### Distance definitions

    This module contains all the distance (error) functions we have implemented.

    Some functions may have specific requirements (weights, number of outputs, ...)
    but all of them share the same interface: `cls.define(IOGraph, IOGraph) -> Tuple[CGraph, str]`

    @authors: Marco Biasion
"""

# interface
from .DistanceSpecification import DistanceSpecification
# implementations
from .AbsoluteDifferenceOfInteger import AbsoluteDifferenceOfInteger
from .AbsoluteDifferenceOfWeightedSum import AbsoluteDifferenceOfWeightedSum
from .HammingDistance import HammingDistance
from .WeightedHammingDistance import WeightedHammingDistance
