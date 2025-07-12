from typing import Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph.Graph import CGraph, IOGraph
from sxpat.graph.Node import If, IntConstant, PlaceHolder, Sum, Xor
from sxpat.utils.collections import formatted_int_range


__all__ = ['HammingDistance']


class HammingDistance(DistanceSpecification):
    """@authors: Marco Biasion"""

    @override
    @classmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance as the Hamming distance of the outputs of the circuits.

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

        # guard
        if len(graph_a.outputs_names) != len(graph_b.outputs_names):
            raise ValueError('The two graphs have different numbers of outputs.')

        # constants
        const_0 = IntConstant('dist_const_0', value=0)
        const_1 = IntConstant('dist_const_1', value=1)

        # bit flips to int
        flipped_bits = []
        int_bits = []
        for (i, out_a, out_b) in zip(
            formatted_int_range(len(graph_a.outputs_names)),
            graph_a.outputs_names,
            graph_b.outputs_names,
        ):
            flipped_bits.append(bit := Xor(f'dist_is_different_{i}', operands=[out_a, out_b]))
            int_bits.append(If(f'dist_value_{i}', operands=[bit, const_1, const_0]))

        # distance
        distance = Sum('dist_distance', operands=int_bits)

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(out_name) for out_name in graph_a.outputs_names),
            *(PlaceHolder(out_name) for out_name in graph_b.outputs_names),
            const_0, const_1,
            *flipped_bits,
            *int_bits,
            distance,
        ))

        return (dist_func, distance.name)
