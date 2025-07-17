from typing import Sequence, Type, Union

from sxpat.utils.decorators import make_utility_class

from sxpat.graph.graph import CGraph, IOGraph
from sxpat.graph.node import Max, Min, PlaceHolder, Target
from sxpat.definitions.distances import DistanceSpecification


__all__ = ['optimize_subgraph_distance']


@make_utility_class
class optimize_subgraph_distance:
    """@authors: Marco Biasion"""

    @classmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                distance: Type[DistanceSpecification],
                opt: Type[Union[Min, Max]]) -> Sequence[CGraph]:
        # define distance
        sub_distance, sub_distance_name = distance.define(
            graph_a, graph_b,
            graph_a.subgraph_outputs, graph_b.subgraph_outputs,
        )

        # define optimization
        optimization = CGraph([
            PlaceHolder(sub_distance_name),
            opt('v2p1_optimize', operands=[sub_distance_name]),
            Target.of(sub_distance_name),
        ])

        return (sub_distance, optimization)

    @classmethod
    def min(cls, graph_a: IOGraph, graph_b: IOGraph,
            distance: Type[DistanceSpecification]) -> Sequence[CGraph]:
        return cls._define(graph_a, graph_b, distance, Min)

    @classmethod
    def max(cls, graph_a: IOGraph, graph_b: IOGraph,
            distance: Type[DistanceSpecification]) -> Sequence[CGraph]:
        return cls._define(graph_a, graph_b, distance, Max)
