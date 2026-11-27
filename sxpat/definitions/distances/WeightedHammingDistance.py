from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import Graph, GraphBuilder
from sxpat.graph import error as g_error
from sxpat.graph.node import If, IntConstant, PlaceHolder, Sum, Xor, Node
from sxpat.utils.collections import first, formatted_int_range


__all__ = ['WeightedHammingDistance']


class WeightedHammingDistance(DistanceSpecification):
    """
        Defines a distance as the Hamming distance of the wanted nodes of the circuits, where each bitflip has the value of the node being flipped.

        @authors: Marco Biasion, Ilia Zeller
    """

    @override
    @classmethod
    def _define(cls, graph_a: Graph, graph_b: Graph,
                wanted_a: Sequence[str], wanted_b: Sequence[str]
                ) -> Tuple[Graph, str]:

        # useful variables
        w_nodes_a: Sequence[Node] = tuple(graph_a[n] for n in wanted_a)  # type: ignore
        w_nodes_b: Sequence[Node] = tuple(graph_b[n] for n in wanted_b)  # type: ignore

        # guard
        graph_a_weights = graph_a.base_components['Weight']
        graph_b_weights = graph_b.base_components['Weight']
        if len(graph_a.base_components['IO'].outputs_names) != len(graph_b.base_components['IO'].outputs_names):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')
        if (broken := first(lambda x: not graph_a_weights.has_weight(x), w_nodes_a, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_a ({graph_a}) has no weight.')
        elif (broken := first(lambda x: not graph_b_weights.has_weight(x), w_nodes_b, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_b ({graph_b}) has no weight.')
        if (mismatch := first(lambda ns: graph_a_weights.get(ns[0].name) != graph_b_weights.get(ns[1].name), zip(w_nodes_a, w_nodes_b), None)) is not None:
            raise ValueError(f'The wanted nodes of the two graphs ({mismatch[0]}, {mismatch[1]}) have mismatching weights.')

        graph_builder = GraphBuilder()
        graph_builder.add_autofill_component('Constraints')

        # bit flips to int
        int_bits = []
        for (i, node_a, node_b) in zip(
            formatted_int_range(len(wanted_a)),
            w_nodes_a,
            w_nodes_b,
        ):
            # create constants
            val: int = graph_a_weights.get(node_a.name)  # type: ignore
            const_0 = graph_builder.add_node(f'dist_a{i}_const_0', IntConstant).add_extras(value=0).current
            const_n = graph_builder.add_node(f'dist_a{i}_const_{val}', IntConstant).add_extras(value=val).current

            # create node reflecting if a bit is flipped
            bit = graph_builder.add_node(f'dist_is_different_{i}', Xor).add_operands([node_a.name, node_b.name]).current

            # create node that reflects the weight if the bit is flipped, or 0
            int_bits.append(graph_builder.add_node(f'dist_value_{i}', If).add_operands([bit.name, const_n.name, const_0.name]).current)

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
    def _minimum_distance(cls, graph_a,
                wanted_a: Sequence[str]
                ) -> int:

        return min(graph_a.base_components['Weight'].get(graph_a[n].name) for n in wanted_a)