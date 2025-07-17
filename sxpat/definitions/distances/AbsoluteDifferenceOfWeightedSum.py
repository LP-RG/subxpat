from typing import Collection, Iterable, Optional, Sequence, Tuple, Union
from typing_extensions import override

import itertools as it
from sxpat.utils.collections import first, formatted_int_range

from .DistanceSpecification import DistanceSpecification

from sxpat.graph import CGraph, IOGraph
from sxpat.graph import error as g_error
from sxpat.graph.node import AbsDiff, AnyExtras, Extras, If, IntConstant, PlaceHolder, Sum


__all__ = ['AbsoluteDifferenceOfWeightedSum']


class AbsoluteDifferenceOfWeightedSum(DistanceSpecification):
    """
        Defines a distance as the absolute difference of the wanted nodes of the circuits where each node is valued using its weight.

        @authors: Marco Biasion
    """

    @override
    @classmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Collection[str], wanted_b: Collection[str],
                ) -> Tuple[CGraph, str]:

        # useful variables
        w_nodes_a: Collection[Extras] = tuple(graph_a[n] for n in wanted_a)  # type: ignore
        w_nodes_b: Collection[Extras] = tuple(graph_b[n] for n in wanted_b)  # type: ignore

        # guard
        if (broken := first(Extras.has_weight, w_nodes_a, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_a ({graph_a}) has no weight.')
        elif (broken := first(Extras.has_weight, w_nodes_b, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph_b ({graph_b}) has no weight.')

        # values
        (a_nodes, a_name) = cls._define_value(w_nodes_a, 'a')
        (b_nodes, b_name) = cls._define_value(w_nodes_b, 'b')

        # distance
        distance = AbsDiff('dist_distance', operands=[a_name, b_name])

        # construct CGraph
        dist_func = CGraph(it.chain(
            a_nodes,
            b_nodes,
            [distance],
        ))

        return (dist_func, distance.name)

    @classmethod
    def define_value(cls, graph: IOGraph, wanted: Optional[Collection[str]] = None
                     ) -> Tuple[CGraph, str]:
        """
            Define an individual weighted sum given the graph and an optional specific collection of nodes to use.

            @notes: if it becomes standard to generate simple expressions (eg. a weighted sum) could make sense to move this logic (and all others like this one) to their own module
        """

        # default
        if wanted is None: wanted = graph.outputs_names

        # useful variables
        w_nodes: Sequence[Extras] = tuple(graph[n] for n in wanted)  # type: ignore

        # guard
        if (broken := first(Extras.has_weight, w_nodes, None)) is not None:
            raise g_error.MissingAttributeInNodeError(f'{broken} in graph ({graph}) has no weight.')

        (value_nodes, value_name) = cls._define_value(w_nodes, 'v')

        # construct CGraph
        value_func = CGraph(value_nodes)

        return (value_func, value_name)

    @classmethod
    def _define_value(cls, wanted_nodes: Sequence[AnyExtras], value_id: str
                      ) -> Tuple[Iterable[Union[PlaceHolder, IntConstant, If, Sum]], str]:

        # graph int
        consts_n = []
        bits_n = []
        for (i, node) in zip(
            formatted_int_range(len(wanted_nodes)),
            wanted_nodes,
        ):
            # create constants
            val: int = node.weight  # type: ignore
            consts_n.extend([
                const_0 := IntConstant(f'dist_{value_id}{i}_const_0', 0),
                const_n := IntConstant(f'dist_{value_id}{i}_const_{val}', val),
            ])

            # create node that reflects the weight if the bit is true, or 0
            bits_n.append(If(f'dist_{value_id}{i}', operands=[node, const_n, const_0]))
        int_n = Sum(f'dist_int_{value_id}', operands=bits_n)

        return (
            it.chain(
                (PlaceHolder(node.name) for node in wanted_nodes),
                consts_n,
                bits_n,
                [int_n],
            ),
            int_n.name,
        )
