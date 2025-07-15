from typing import Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph, IOGraph
from sxpat.graph.node import Extras, If, IntConstant, PlaceHolder, Sum, Xor
from sxpat.utils.collections import formatted_int_range


__all__ = ['WeightedHammingDistance']


class WeightedHammingDistance(DistanceSpecification):
    """@authors: Marco Biasion"""

    @override
    @classmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance as the Hamming distance of the outputs of the circuits, where each bitflip has the value of the node being flipped.

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

        # guard
        if len(graph_a.outputs_names) != len(graph_b.outputs_names):
            raise ValueError('The two graphs have different numbers of outputs.')
        if not all(isinstance(out, Extras) and out.weight is not None for out in graph_a.outputs):
            raise ValueError('Not all graph_a outputs do have weights.')
        if not all(isinstance(out, Extras) and out.weight is not None for out in graph_b.outputs):
            raise ValueError('Not all graph_b outputs do have weights.')
        if not all(out_a.weight == out_b.weight for (out_a, out_b) in zip(graph_a.outputs, graph_b.outputs)):
            raise ValueError('The outputs of the two graphs have mismatching weights.')

        # bit flips to int
        consts = []
        flipped_bits = []
        int_bits = []
        for (i, out_a, out_b) in zip(
            formatted_int_range(len(graph_a.outputs_names)),
            graph_a.outputs,
            graph_b.outputs,
        ):
            # create constants
            val = out_a.weight
            consts.extend([
                const_0 := IntConstant(f'dist_a{i}_const_0', 0),
                const_n := IntConstant(f'dist_a{i}_const_{val}', val),
            ])

            # create node reflecting if a bit is flipped
            flipped_bits.append(bit := Xor(f'dist_is_different_{i}', operands=[out_a, out_b]))

            # create node that reflects the weight if the bit is flipped, or 0
            int_bits.append(If(f'dist_value_{i}', operands=[bit, const_n, const_0]))

        # distance
        distance = Sum('dist_distance', operands=int_bits)

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(out_name) for out_name in graph_a.outputs_names),
            *(PlaceHolder(out_name) for out_name in graph_b.outputs_names),
            *consts.values(),
            *flipped_bits,
            *int_bits,
            distance,
        ))

        return (dist_func, distance.name)
