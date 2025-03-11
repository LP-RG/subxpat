from typing import Any, Mapping, Optional
from sxpat.newGraph import CGraph, SGraph, TGraph


__all__ = ['Solver']


class Solver:
    @classmethod
    def solve(cls, s_graph: SGraph, t_graph: TGraph, c_graph: CGraph) -> Optional[Mapping[str, Any]]:
        raise NotImplementedError(f'{cls.__qualname__}.solve() is abstract')
