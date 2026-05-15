from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph
from sxpat.graph.builder import GraphBuilder
from sxpat.graph.node import If, IntConstant, Sum, Xor
from sxpat.utils.collections import formatted_int_range


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
                ) -> Tuple[CGraph, str]:
        # guards
        if len(wanted_a) != len(wanted_b):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')
        if len(_0.outputs_names) != len(_1.outputs_names):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')

        # prepare builder
        builder = GraphBuilder()

        # add placeholders
        builder.add_placeholders(wanted_a).add_placeholders(wanted_b)

        # bit flips to int
        builder.push_recording()
        for (i, out_a, out_b) in zip(
            formatted_int_range(len(wanted_a)),
            wanted_a,
            wanted_b,
        ):
            builder.push_recording()

            # create node reflecting if a bit is flipped
            builder.add_node(f'dist_is_different_{i}', Xor, operands=[out_a, out_b])
            # create constants
            builder \
                .add_node(f'dist_a{i}_const_1', IntConstant, value=1) \
                .add_node(f'dist_a{i}_const_0', IntConstant, value=0)

            # create node that reflects 1 if the bit is flipped, or 0
            builder.add_node(f'dist_value_{i}', If, operands=builder.pop_recording())

        # distance
        distance_name = 'dist_distance'
        builder.add_node(distance_name, Sum, operands=builder.pop_recording())

        return (builder.build(CGraph), distance_name)

    @override
    @classmethod
    def minimum_distance(cls, _0,
                         wanted_a: Sequence[str]
                         ) -> int:
        return 1
