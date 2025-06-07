from typing import Mapping, Optional, Sequence, Tuple, Union, TypeVar
from abc import abstractmethod

from sxpat.graph import IOGraph, PGraph, CGraph
from sxpat.specifications import Specifications
from sxpat.utils.decorators import make_utility_class


__all__ = ['Solver']


@make_utility_class
class Solver:

    _Graphs = TypeVar('_Graphs', bound=Sequence[Union[IOGraph, PGraph, CGraph]])

    @classmethod
    @abstractmethod
    def solve(cls, graphs: _Graphs, specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Union[bool, int]]]]:
        """
            Solve the required problem defined by the given graphs.

            The supported graphs are:
            - IOGraph (and subclasses): for input variables (and local behaviour)
            - PGraph (and subclasses): for parameter variables (and local behaviour)
            - CGraph (and subclasses): for applicable constraints

            Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the Target nodes if `sat`.
        """
        raise NotImplementedError(f'{cls.__qualname__}.solve(...) is abstract')
