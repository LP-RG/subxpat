from abc import abstractmethod, ABCMeta
from typing import Optional, Sequence, Tuple, overload

from sxpat.graph import CGraph, IOGraph
from sxpat.graph import error as g_error
from sxpat.utils.collections import first
from sxpat.utils.decorators import make_utility_class


@make_utility_class
class DistanceSpecification(metaclass=ABCMeta):
    """@authors: Marco Biasion"""

    @classmethod
    @overload
    def define(cls, graph_a: IOGraph, graph_b: IOGraph,
               wanted_a: Sequence[str], wanted_b: Optional[Sequence[str]] = None
               ) -> Tuple[CGraph, str]:
        """
            Defines a distance between two circuits (given as graph), given a specific sequence (or one per circuit) of nodes to use.

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

    @classmethod
    @overload
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance between the outputs of two circuits (given as graphs).

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """

    @classmethod
    @abstractmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph,
               wanted_a: Optional[Sequence[str]] = None, wanted_b: Optional[Sequence[str]] = None,
               ) -> Tuple[CGraph, str]:

        # no wanted names given
        if wanted_a is None and wanted_b is None:
            # delegate computation
            return cls._define(
                graph_a, graph_b,
                graph_a.outputs_names, graph_b.outputs_names,
            )

        elif wanted_a is not None:
            # default
            if wanted_b is None: wanted_b = wanted_a

            # guard
            if (missing := first(lambda n: n not in graph_a, wanted_a, None)) is not None:
                raise g_error.MissingNodeError(f'Node {missing} is not in graph_a ({graph_a}).')
            if (missing := first(lambda n: n not in graph_b, wanted_b, None)) is not None:
                raise g_error.MissingNodeError(f'Node {missing} is not in graph_b ({graph_b}).')

            # delegate computation
            return cls._define(
                graph_a, graph_b,
                wanted_a, wanted_b,
            )

        else: raise

    @classmethod
    @abstractmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Sequence[str], wanted_b: Sequence[str]
                ) -> Tuple[CGraph, str]: ...

    @classmethod
    @abstractmethod
    def minimum_distance(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Sequence[str], wanted_b: Sequence[str]
                ) -> int: ...