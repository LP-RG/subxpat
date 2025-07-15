from typing import Tuple
from abc import abstractmethod

from sxpat.graph import SGraph, PGraph, CGraph
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class


__all__ = ['Template']


@make_utility_class
class Template:
    @classmethod
    @abstractmethod
    def define(cls, graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:
        """
            Given a graph with subgraph informations and the specifications,
            returns the graph with the subgraph replaced with the template 
            and a graph containing all the constraints required to achieve the wanted behaviour.
        """
        raise NotImplementedError(f'{cls.__qualname__}.define() is abstract')
