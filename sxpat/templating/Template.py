from typing import NoReturn, Tuple
from abc import abstractmethod

from sxpat.graph import SGraph, PGraph, CGraph
from sxpat.specifications import Specifications


__all__ = ['Template']


class Template:
    def __new__(cls) -> NoReturn: raise NotImplementedError(f'{cls.__qualname__} is a utility class and as such cannot be instantiated')

    @classmethod
    @abstractmethod
    def define(cls, graph: SGraph, specs: Specifications) -> Tuple[PGraph, CGraph]:
        """
            Given a graph with subgraph informations and the specifications,
            returns the graph with the subgraph replaced with the template 
            and a graph containing all the constraints required for the behaviour of the parameters.
        """
        raise NotImplementedError(f'{cls.__qualname__}.define() is abstract')
