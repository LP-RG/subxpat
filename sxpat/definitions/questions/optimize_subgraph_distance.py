# type annotations
from typing import (
    Sequence,
    Tuple,
    Type,
    Union,
)

# utilities
from sxpat.utils.decorators import (
    make_utility_class
)

#
from sxpat.graph.graph import (
    CGraph,
    SGraph,
)
from sxpat.graph.node import (
    PlaceHolder,
    Max,
    Min,
    Target,
)
from sxpat.definitions.distances import (
    DistanceSpecification,
)


__all__ = ['optimize_subgraph_distance']


@make_utility_class
class optimize_subgraph_distance:
    """@authors: Marco Biasion"""

    @classmethod
    def _define(cls, graph_a: SGraph, graph_b: SGraph,
                distance: Type[DistanceSpecification],
                opt: Type[Union[Min, Max]]) -> Tuple[str, Sequence[CGraph]]:
        # define distance
        sub_distance, sub_distance_name = distance.define(
            graph_a, graph_b,
            tuple(n.name for n in graph_a.subgraph_outputs),
            tuple(n.name for n in graph_b.subgraph_outputs),
        )

        # define optimization
        optimization = CGraph([
            PlaceHolder(sub_distance_name),
            opt('v2p1_optimize', operands=[sub_distance_name]),
            Target.of(sub_distance_name),
        ])

        return (sub_distance_name, (sub_distance, optimization))

    @classmethod
    def min(cls, graph_a: SGraph, graph_b: SGraph,
            distance: Type[DistanceSpecification]) -> Tuple[str, Sequence[CGraph]]:
        """
            Given two graphs and a distance function, returns the graphs representing
            the minimization question and the name of the target.
        """
        return cls._define(graph_a, graph_b, distance, Min)

    @classmethod
    def max(cls, graph_a: SGraph, graph_b: SGraph,
            distance: Type[DistanceSpecification]) -> Tuple[str, Sequence[CGraph]]:
        """
            Given two graphs and a distance function, returns the graphs representing
            the maximization question and the name of the target.
        """
        return cls._define(graph_a, graph_b, distance, Max)
