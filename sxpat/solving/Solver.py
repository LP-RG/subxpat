from typing import Any, Mapping, NoReturn, Optional, Tuple
from abc import abstractmethod

from sxpat.graph import IOGraph, PGraph, CGraph
from sxpat.specifications import Specifications


__all__ = ['Solver']


class Solver:
    def __new__(cls) -> NoReturn: raise NotImplementedError(f'{cls.__qualname__} is a utility class and as such cannot be instantiated')

    @classmethod
    @abstractmethod
    def solve(cls, reference_graph: IOGraph, parametric_graph: PGraph,
              constraints_graph: CGraph,
              specifications: Specifications) -> Tuple[str, Optional[Mapping[str, Any]]]:
        """
            Solve the required problem defined with the graph, the graph with the template and the graph with constraints.

            Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the Target nodes if `sat`.
        """
        raise NotImplementedError(f'{cls.__qualname__}.solve(...) is abstract')
