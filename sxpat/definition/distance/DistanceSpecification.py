from typing import Tuple

from sxpat.graph import CGraph, IOGraph
from sxpat.utils.decorators import make_utility_class


@make_utility_class
class DistanceSpecification:
    """@authors: Marco Biasion"""

    @classmethod
    def define(cls, graph_a: IOGraph, graph_b: IOGraph) -> Tuple[CGraph, str]:
        """
            Defines a distance given two circuits (given as graphs).

            @returns: the `CGraph` containing the definition and the name of the node representing the distance
        """
        raise NotImplementedError(f'{cls.__qualname__}.define(...) is abstract.')
