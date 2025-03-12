from typing import Tuple
from abc import abstractmethod

from sxpat.graph import SGraph, TGraph, CGraph
from sxpat.specifications import Specifications


__all__ = ['Template']


class Template:
    @classmethod
    @abstractmethod
    def define(cls, graph: SGraph, specs: Specifications) -> Tuple[TGraph, CGraph]:
        """
            Given a graph with subgraph informations and the specifications,
            returns the graph with the subgraph replaced with the template 
            and a graph containing all the constraints required for the behaviour of the parameters.
        """
        raise NotImplementedError(f'{cls.__qualname__}.define() is abstract')
