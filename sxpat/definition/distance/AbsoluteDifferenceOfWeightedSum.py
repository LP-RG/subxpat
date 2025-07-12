from typing import Tuple
from typing_extensions import override

from sxpat.utils.collections import formatted_int_range

from .DistanceSpecification import DistanceSpecification

from sxpat.graph.Graph import CGraph, IOGraph
from sxpat.graph.Node import AbsDiff, Extras, If, IntConstant, PlaceHolder, Sum


__all__ = ['AbsoluteDifferenceOfWeightedSum']


class AbsoluteDifferenceOfWeightedSum(DistanceSpecification):
    """@authors: Marco Biasion"""

    @override
    @classmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance as the absolute difference of the outputs of the circuits treated as series of bits forming unsigned integers

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

        # guard
        if not all(isinstance(out, Extras) and out.weight is not None for out in graph_a.outputs):
            raise ValueError('Not all graph_a outputs do have weights.')
        if not all(isinstance(out, Extras) and out.weight is not None for out in graph_b.outputs):
            raise ValueError('Not all graph_b outputs do have weights.')

        # graph_a int
        consts_a = []
        bits_a = []
        for (i, out) in zip(
            formatted_int_range(len(graph_a.outputs_names)),
            graph_a.outputs,
        ):
            val = out.weight
            consts_a.extend([
                const_0 := IntConstant(f'dist_a{i}_const_0', 0),
                const_n := IntConstant(f'dist_a{i}_const_{val}', val),
            ])
            bits_a.append(If(f'dist_a{i}', operands=[out, const_n, const_0]))
        int_a = Sum('dist_int_a', operands=bits_a)

        # graph_b int
        consts_b = []
        bits_b = []
        for (i, out) in zip(
            formatted_int_range(len(graph_b.outputs_names)),
            graph_b.outputs,
        ):
            val = out.weight
            consts_b.extend([
                const_0 := IntConstant(f'dist_b{i}_const_0', 0),
                const_n := IntConstant(f'dist_b{i}_const_{val}', val),
            ])
            bits_b.append(If(f'dist_b{i}', operands=[out, const_n, const_0]))
        int_b = Sum('dist_int_b', operands=bits_b)

        # distance
        distance = AbsDiff('dist_distance', operands=[int_a, int_b]),

        # construct CGraph
        dist_func = CGraph((
            *(PlaceHolder(out_name) for out_name in graph_a.outputs_names),
            *consts_a, *bits_a, int_a,
            *(PlaceHolder(out_name) for out_name in graph_b.outputs_names),
            *consts_b, *bits_b, int_b,
            distance,
        ))

        return (dist_func, distance.name)
