from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph
from sxpat.graph.node import AbsDiff, PlaceHolder, ToInt
from sxpat.graph.components import Constraints


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
                ) -> Tuple[Graph, str]:

        # define outputs of a and of b as integers
        int_a = ToInt('dist_int_a_adoi', operands=wanted_a)
        int_b = ToInt('dist_int_b_adoi', operands=wanted_b)

        # distance
        distance = AbsDiff('dist_distance', operands=[int_a, int_b])

        # construct Constraints Graph
        graph_nodes = [
            *(PlaceHolder(name) for name in wanted_a),
            int_a,
            *(PlaceHolder(name) for name in wanted_b),
            int_b,
            distance,
        ]
        dist_func = Graph(graph_nodes, [Constraints(graph_nodes)])

        return (dist_func, distance.name)

    @override
    @classmethod
    def _minimum_distance(cls, _0,
                wanted_a: Sequence[str]
                ) -> int:
        return 1