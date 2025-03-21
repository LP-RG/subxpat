from typing import Any, Mapping, Optional, Tuple
from abc import abstractmethod

from sxpat.graph import CGraph, SGraph, PGraph


__all__ = ['Solver']


class Solver:
    @classmethod
    @abstractmethod
    def solve(cls, s_graph: SGraph, t_graph: PGraph, c_graph: CGraph) -> Tuple[str, Optional[Mapping[str, Any]]]:
        """
            Solve the required problem defined with the graph, the graph with the template and the graph with constraints.

            Returns the model evaluated from the Target nodes of None if unsat.
        """
        raise NotImplementedError(f'{cls.__qualname__}.solve() is abstract')
