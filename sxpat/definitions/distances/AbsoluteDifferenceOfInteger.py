from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph.node import AbsDiff, PlaceHolder, ToInt


__all__ = ['AbsoluteDifferenceOfInteger']


class AbsoluteDifferenceOfInteger(DistanceSpecification):
    """
        Defines a distance as the absolute difference of the wanted nodes of the circuits treated as series of bits forming unsigned integers.

        @authors: Marco Biasion, Ilia Zeller
    """

    @override
    @classmethod
    def _define(cls, _0, _1,
                wanted_a: Sequence[str], wanted_b: Sequence[str],
                ) -> Tuple[Graph, str]:

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # define outputs of a and of b as integers
        int_a = graph_builder.add_node('dist_int_a_adoi', ToInt).add_operands(list(wanted_a)).current
        int_b = graph_builder.add_node('dist_int_b_adoi', ToInt).add_operands(list(wanted_b)).current

        # distance
        distance = graph_builder.add_node('dist_distance', AbsDiff).add_operands([int_a.name, int_b.name]).current

        # construct graph
        for name in wanted_a:
            graph_builder.add_node(name, PlaceHolder)
        for name in wanted_b:
            graph_builder.add_node(name, PlaceHolder)

        dist_func = graph_builder.create()

        return (dist_func, distance.name)

    @override
    @classmethod
    def _minimum_distance(cls, _0,
                wanted_a: Sequence[str]
                ) -> int:
        return 1