from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph, IOGraph
from sxpat.graph.node import RightShift, AbsDiff, Sum, GreaterThan, PlaceHolder, ToInt


__all__ = ['AbsoluteDifferenceOfInteger']


class RelativeDifferenceOfIntegerBinary(DistanceSpecification):
    """
        Defines a distance as the relative difference of the wanted nodes of the circuits treated as series of bits forming unsigned integers.
        Order matters i.e. relative error = |a - b| / a
    """

    binary_part = None

    @override
    @classmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
               wanted_a: Sequence[str], wanted_b: Sequence[str],
               ) -> Tuple[CGraph, str]:
        
        if not cls.binary_part:
            raise ValueError("binary_part must be set via factory")

        # define outputs of a and of b as integers
        int_a = ToInt('dist_int_a', operands=wanted_a)
        int_b = ToInt('dist_int_b', operands=wanted_b)


        addends = []
        # distance
        for num_shift in range(1, len(cls.binary_part) + 1):
            if cls.binary_part[num_shift - 1] == '1':
                addends.append(RightShift(f'right_shift_{50/num_shift}%', operands=(int_a,), value=num_shift))
        
        total = Sum('binary', operands=addends)
        abs_diff = AbsDiff('abs_diff_distance', operands=[int_a, int_b])

        distance_under_treshold = GreaterThan('distance_under_treshold', operands=(abs_diff, total))
        integer_distance = ToInt('1_or_0', operands=(distance_under_treshold,))

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(name) for name in wanted_a),
            int_a,
            *(PlaceHolder(name) for name in wanted_b),
            int_b,
            *addends,
            total,
            abs_diff,
            distance_under_treshold,
            integer_distance,
        ))

        return (dist_func, integer_distance.name)

    @override
    @classmethod
    def _minimum_distance(cls, _0,
                wanted_a: Sequence[str]
                ) -> int:
        return 1
    
def make_relative_distance(binary_part: str):
    class CustomRelativeDifference(RelativeDifferenceOfIntegerBinary):
        pass

    CustomRelativeDifference.binary_part = binary_part
    return CustomRelativeDifference