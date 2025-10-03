from typing import Sequence, Tuple
from typing_extensions import override

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph, IOGraph
from sxpat.graph import error as g_error
from sxpat.graph.node import Extras, If, IntConstant, PlaceHolder, Sum, Xor
from sxpat.utils.collections import first, formatted_int_range


__all__ = ['WeightedHammingDistance']


class WeightedHammingDistance(DistanceSpecification):
    """
        Defines a distance as the Hamming distance of the wanted nodes of the circuits, where each bitflip has the value of the node being flipped.

        @authors: Marco Biasion
    """

    @override
    @classmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Sequence[str], wanted_b: Sequence[str]
                ) -> Tuple[CGraph, str]:

        # useful variables
        w_nodes_a: Sequence[Extras] = tuple(graph_a[n] for n in wanted_a)  # type: ignore
        w_nodes_b: Sequence[Extras] = tuple(graph_b[n] for n in wanted_b)  # type: ignore

        # guard
        if len(graph_a.outputs_names) != len(graph_b.outputs_names):
            raise ValueError('The sequences of wanted nodes have different lengths (or the graphs have different number of outputs).')
        if (broken := first(lambda x: not Extras.has_weight(x), w_nodes_a, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_a ({graph_a}) has no weight.')
        elif (broken := first(lambda x: not Extras.has_weight(x), w_nodes_b, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_b ({graph_b}) has no weight.')
        if (mismatch := first(lambda ns: ns[0].weight != ns[1].weight, zip(w_nodes_a, w_nodes_b), None)) is not None:
            raise ValueError(f'The wanted nodes of the two graphs ({mismatch[0]}, {mismatch[1]}) have mismatching weights.')

        # bit flips to int
        consts = []
        flipped_bits = []
        int_bits = []
        for (i, node_a, node_b) in zip(
            formatted_int_range(len(wanted_a)),
            w_nodes_a,
            w_nodes_b,
        ):
            # create constants
            val: int = node_a.weight  # type: ignore
            consts.extend([
                const_0 := IntConstant(f'dist_a{i}_const_0', 0),
                const_n := IntConstant(f'dist_a{i}_const_{val}', val),
            ])

            # create node reflecting if a bit is flipped
            flipped_bits.append(bit := Xor(f'dist_is_different_{i}', operands=[node_a, node_b]))

            # create node that reflects the weight if the bit is flipped, or 0
            int_bits.append(If(f'dist_value_{i}', operands=[bit, const_n, const_0]))

        # distance
        distance = Sum('dist_distance', operands=int_bits)

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(name) for name in wanted_a),
            *(PlaceHolder(name) for name in wanted_b),
            *consts,
            *flipped_bits,
            *int_bits,
            distance,
        ))

        return (dist_func, distance.name)
