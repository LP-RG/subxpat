from typing import Any, Mapping, Optional, Tuple
from abc import abstractmethod

from sxpat.graph import CGraph, SGraph, PGraph


__all__ = ['Solver']


class Solver:
    @classmethod
    @abstractmethod
    def solve(cls, s_graph: SGraph, p_graph: PGraph, c_graph: CGraph) -> Tuple[str, Optional[Mapping[str, Any]]]:
        """
            Solve the required problem defined with the graph, the graph with the template and the graph with constraints.

            Returns the status of the resolution (`sat`, `unsat`, `unknown`) and the model evaluated from the Target nodes if `sat`.
        """
        raise NotImplementedError(f'{cls.__qualname__}.solve() is abstract')
