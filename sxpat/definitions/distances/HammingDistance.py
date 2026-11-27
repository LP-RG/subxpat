from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph.node import If, IntConstant, PlaceHolder, Sum, Xor
from sxpat.utils.collections import formatted_int_range


__all__ = ['HammingDistance']


class HammingDistance(DistanceSpecification):
    """
        Defines a distance as the Hamming distance of the wanted nodes of the circuits.

        @authors: Marco Biasion, Ilia Zeller
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

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # bit flips to int
        int_bits = []
        for (i, out_a, out_b) in zip(
            formatted_int_range(len(wanted_a)),
            wanted_a,
            wanted_b,
        ):
            # create constants
            const_0 = graph_builder.add_node(f'dist_a{i}_const_0', IntConstant).add_extras(value=0).current
            const_1 = graph_builder.add_node(f'dist_a{i}_const_1', IntConstant).add_extras(value=1).current

            # create node reflecting if a bit is flipped
            bit = graph_builder.add_node(f'dist_is_different_{i}', Xor).add_operands([out_a, out_b]).current

            # create node that reflects 1 if the bit is flipped, or 0
            int_bits.append(
                graph_builder.add_node(
                    f'dist_value_{i}', 
                    If).add_operands([bit.name, const_1.name, const_0.name]).current
            )

        # distance
        distance = graph_builder.add_node('dist_distance', Sum).add_operands([n.name for n in int_bits]).current

        # placeholders 
        for name in wanted_a:
            graph_builder.add_node(name, PlaceHolder)
        for name in wanted_b:
            graph_builder.add_node(name, PlaceHolder)

        # construct Constraints Graph
        dist_func = graph_builder.create()

        return (dist_func, distance.name)

    @override
    @classmethod
    def minimum_distance(cls, _0,
                wanted_a: Sequence[str]
                ) -> int:
        return 1
