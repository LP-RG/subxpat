import sys
from typing import Any, Iterator, Literal, Sequence, SupportsIndex, Union, overload
from abc import ABCMeta, abstractmethod

from sxpat.graph import SGraph, PGraph, CGraph
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class


__all__ = ['Template']


class TemplateBundle(Sequence):
    def __init__(self, templated_circuit: PGraph, constraints_graphs: Sequence[CGraph] = ()) -> None:
        self._data = (templated_circuit, *constraints_graphs)

    def __getitem__(self, key: int) -> Union[PGraph, CGraph]: return self._data.__getitem__(key)
    def __len__(self) -> int: return self._data.__len__()

    def __contains__(self, obj: Union[PGraph, CGraph]) -> bool: return self._data.__contains__(obj)
    def __iter__(self) -> Iterator[Union[PGraph, CGraph]]: return self._data.__iter__()
    def __reversed__(self) -> Iterator[Union[PGraph, CGraph]]: return self._data.__reversed__()
    def count(self, value: Any) -> int: return self._data.count(value)

    def index(self, value: Any, start: SupportsIndex = 0, stop: SupportsIndex = sys.maxsize) -> int:
        return self._data.index(value, start, stop)

    @property
    def template_circuit(self): return self._data[0]
    @property
    def constraints_graphs(self): return self._data[1:]

    @overload
    def __getitem__(self, key: Literal[0]) -> PGraph: ...
    @overload
    def __getitem__(self, key: int) -> CGraph: ...


@make_utility_class
class Template(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def define(cls, graph: SGraph, specs: Specifications) -> TemplateBundle:
        """
            Given a graph with subgraph informations and the specifications,
            returns the parametric graph with the subgraph replaced with the template 
            and a sequence of graph containing all the constraints required to achieve the wanted behaviour.
        """
        raise NotImplementedError(f'{cls.__qualname__}.define() is abstract')
