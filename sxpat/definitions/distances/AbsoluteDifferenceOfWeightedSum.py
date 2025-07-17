from typing import Sequence, Tuple
from typing_extensions import override

from sxpat.utils.collections import first, formatted_int_range

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph, IOGraph
from sxpat.graph import error as g_error
from sxpat.graph.node import AbsDiff, Extras, If, IntConstant, PlaceHolder, Sum


__all__ = ['AbsoluteDifferenceOfWeightedSum']


class AbsoluteDifferenceOfWeightedSum(DistanceSpecification):
    """
        Defines a distance as the absolute difference of the wanted nodes of the circuits where each node is valued using its weight.

        @authors: Marco Biasion
    """

    @override
    @classmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Sequence[str], wanted_b: Sequence[str],
                ) -> Tuple[CGraph, str]:

        # useful variables
        w_nodes_a: Sequence[Extras] = tuple(graph_a[n] for n in wanted_a)  # type: ignore
        w_nodes_b: Sequence[Extras] = tuple(graph_b[n] for n in wanted_b)  # type: ignore

        # guard
        if (broken := first(Extras.has_weight, w_nodes_a, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_a ({graph_a}) has no weight.')
        elif (broken := first(Extras.has_weight, w_nodes_b, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_b ({graph_b}) has no weight.')

        # graph_a int
        consts_a = []
        bits_a = []
        for (i, node) in zip(
            formatted_int_range(len(wanted_a)),
            w_nodes_a,
        ):
            # create constants
            val: int = node.weight  # type: ignore
            consts_a.extend([
                const_0 := IntConstant(f'dist_a{i}_const_0', 0),
                const_n := IntConstant(f'dist_a{i}_const_{val}', val),
            ])

            # create node that reflects the weight if the bit is true, or 0
            bits_a.append(If(f'dist_a{i}', operands=[node, const_n, const_0]))
        int_a = Sum('dist_int_a', operands=bits_a)

        # graph_b int
        consts_b = []
        bits_b = []
        for (i, node) in zip(
            formatted_int_range(len(wanted_b)),
            w_nodes_b,
        ):
            # create constants
            val: int = node.weight  # type: ignore
            consts_b.extend([
                const_0 := IntConstant(f'dist_b{i}_const_0', 0),
                const_n := IntConstant(f'dist_b{i}_const_{val}', val),
            ])

            # create node that reflects the weight if the bit is true, or 0
            bits_b.append(If(f'dist_b{i}', operands=[node, const_n, const_0]))
        int_b = Sum('dist_int_b', operands=bits_b)

        # distance
        distance = AbsDiff('dist_distance', operands=[int_a, int_b])

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(name) for name in wanted_a),
            *consts_a, *bits_a, int_a,
            *(PlaceHolder(name) for name in wanted_b),
            *consts_b, *bits_b, int_b,
            distance,
        ))

        return (dist_func, distance.name)
