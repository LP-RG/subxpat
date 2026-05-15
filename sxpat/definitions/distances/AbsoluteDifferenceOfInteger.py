from typing import Sequence, Tuple
from typing_extensions import override

from sxpat.graph.builder import GraphBuilder

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph
from sxpat.graph.node import AbsDiff, PlaceHolder, ToInt


__all__ = ['AbsoluteDifferenceOfInteger']


class AbsoluteDifferenceOfInteger(DistanceSpecification):
    """
        Defines a distance as the absolute difference of the wanted nodes of the circuits treated as series of bits forming unsigned integers.

        @authors: Marco Biasion
    """

    @override
    @classmethod
    def _define(cls, _0, _1,
                  wanted_a: Sequence[str], wanted_b: Sequence[str],
                  ) -> Tuple[CGraph, str]:
        # prepare builder
        builder = GraphBuilder()

        # add placeholders
        builder.add_placeholders(wanted_a).add_placeholders(wanted_b)

        # define outputs of a and of b as integers
        builder.push_recording()
        builder.add_node('dist_int_a_adoi', ToInt, operands=wanted_a)
        builder.add_node('dist_int_b_adoi', ToInt, operands=wanted_b)

        # distance
        distance_name = 'dist_distance'
        builder.add_node(distance_name, AbsDiff, operands=builder.pop_recording())

        return (builder.build(CGraph), distance_name)

    @override
    @classmethod
    def _minimum_distance(cls, _0,
                          wanted_a: Sequence[str]
                          ) -> int:
        return 1
