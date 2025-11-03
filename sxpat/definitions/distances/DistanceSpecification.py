from abc import abstractmethod, ABCMeta
from typing import Optional, Sequence, Tuple, final, overload

from sxpat.graph import CGraph, IOGraph, SGraph
from sxpat.graph import error as g_error

from sxpat.utils.collections import first
from sxpat.utils.decorators import make_utility_class
import itertools as it
from sxpat.converting.utils import get_rolling_code, set_prefix_new


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
    @final
    def define(cls, graph_a: IOGraph, graph_b: IOGraph,
               wanted_a: Optional[Sequence[str]] = None, wanted_b: Optional[Sequence[str]] = None,
               ) -> Tuple[CGraph, str]:

        # > generate distance function graph

        # no wanted names given
        if wanted_a is None and wanted_b is None:
            # delegate computation
            dist_func, root_name = cls._define(
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
            dist_func, root_name = cls._define(
                graph_a, graph_b,
                wanted_a, wanted_b,
            )

        else: raise ValueError(f'Illegal call with `wanted_b` without `wanted_a`.')

        # > assign rolling prefix
        prefix = get_rolling_code() + '_'
        dist_func = set_prefix_new(dist_func, prefix, it.chain(wanted_a, wanted_b))
        root_name = prefix + root_name

        return (dist_func, root_name)

    @classmethod
    @abstractmethod
    def _define(cls, graph_a: IOGraph, graph_b: IOGraph,
                wanted_a: Sequence[str], wanted_b: Sequence[str]
                ) -> Tuple[CGraph, str]: ...

    @classmethod
    def minimum_distance(cls, graph_a: SGraph,
                wanted_a: Optional[Sequence[str]] = None
                ) -> int:
        
        if wanted_a is None:
            wanted_a = (n.name for n in graph_a.subgraph_outputs)
        
        return cls._minimum_distance(graph_a, wanted_a)
        
    @classmethod
    @abstractmethod
    def _minimum_distance(cls, graph_a: SGraph,
                wanted_a: Sequence[str]
                ) -> int: ...