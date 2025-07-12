from typing import Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph.Graph import CGraph, IOGraph
from sxpat.graph.Node import AbsDiff, PlaceHolder, ToInt


__all__ = ['AbsoluteDifferenceOfInteger']


class AbsoluteDifferenceOfInteger(DistanceSpecification):
    """@authors: Marco Biasion"""

    @override
    @classmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance as the absolute difference of the outputs of the circuits treated as series of bits forming unsigned integers

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

        # define outputs of a and of b as integers
        int_a = ToInt('dist_int_a', operands=graph_a.outputs_names),
        int_b = ToInt('dist_int_b', operands=graph_b.outputs_names),

        # distance
        distance = AbsDiff('dist_distance', operands=[int_a, int_b]),

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(out_name) for out_name in graph_a.outputs_names),
            int_a,
            *(PlaceHolder(out_name) for out_name in graph_b.outputs_names),
            int_b,
            distance,
        ))

        return (dist_func, distance.name)
