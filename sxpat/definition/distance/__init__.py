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
