from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph
from sxpat.graph.node import If, IntConstant, PlaceHolder, Sum, Xor
from sxpat.utils.collections import formatted_int_range
from sxpat.graph.components import Constraints


__all__ = ['HammingDistance']


class HammingDistance(DistanceSpecification):
    """
        Defines a distance as the Hamming distance of the wanted nodes of the circuits.

        @authors: Marco Biasion
    """

    @override
    @classmethod
    def _define(cls, _0, _1,
                wanted_a: Sequence[str], wanted_b: Sequence[str],
                ) -> Tuple[Graph, str]:

        # guard
        if len(wanted_a) != len(wanted_b):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')
        if len(_0.outputs_names) != len(_1.outputs_names):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')

        # bit flips to int
        consts = []
        flipped_bits = []
        int_bits = []
        for (i, out_a, out_b) in zip(
            formatted_int_range(len(wanted_a)),
            wanted_a,
            wanted_b,
        ):
            # create constants
            consts.extend([
                const_0 := IntConstant(f'dist_a{i}_const_0', 0),
                const_1 := IntConstant(f'dist_a{i}_const_1', 1),
            ])

            # create node reflecting if a bit is flipped
            flipped_bits.append(bit := Xor(f'dist_is_different_{i}', operands=[out_a, out_b]))

            # create node that reflects 1 if the bit is flipped, or 0
            int_bits.append(If(f'dist_value_{i}', operands=[bit, const_1, const_0]))

        # distance
        distance = Sum('dist_distance', operands=int_bits)

        graph_nodes = list((
            *(PlaceHolder(name) for name in wanted_a),
            *(PlaceHolder(name) for name in wanted_b),
            *consts,
            *flipped_bits,
            *int_bits,
            distance,
        ))

        # construct Constraints Graph
        dist_func = Graph(graph_nodes, [Constraints(graph_nodes)])

        return (dist_func, distance.name)

    @override
    @classmethod
    def minimum_distance(cls, _0,
                wanted_a: Sequence[str]
                ) -> int:
        return 1
