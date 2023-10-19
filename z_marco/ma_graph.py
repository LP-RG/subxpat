from __future__ import annotations
from enum import Enum
from functools import cached_property, lru_cache
from typing import FrozenSet, List, Optional, Set, Tuple

import dataclasses as dc

import networkx as nx

from Z3Log.graph import Graph


# class Operation(Enum):
#     OR = 'or'
#     NOT = 'not'
#     AND = 'and'
#     INPUT = 'input'
#     OUTPUT = 'output'
#     CONST0 = 'wip_0'
#     CONST1 = 'wip_1'


# @dc.dataclass
# class MaNode:
#     name: str
#     operation: Operation

#     def to_gv_line(self) ->str:
#         shape = {
#             Operation.OR: 'invhouse',
#             Operation.NOT: 'invhouse',
#             Operation.AND: 'invhouse',
#             Operation.INPUT: 'circle',
#             Operation.OUTPUT: 'doublecircle',
#             Operation.CONST0: 'star',
#             Operation.CONST1: 'star',
#         }
#         label = {

#         }


class MaGraph:
    def __init__(self, *, gv_path: str = None, digraph: nx.DiGraph = None) -> None:
        # TODO: this class is a subclass of Graph?, but does not really fit in the inheritance,
        # TODO: in the future should be refactored to behave like the parents, or made its own class

        # guards
        if (gv_path is None) == (digraph is None):
            raise ValueError("One of `gv_path` or `digraph` must be given.")

        # load graph
        if gv_path is not None:
            self._digraph = nx.drawing.nx_agraph.read_dot(gv_path)
        else:
            self._digraph = nx.DiGraph(digraph)

    @cached_property
    def inputs(self) -> Tuple[str]:
        return tuple(
            name
            for name, data in self._digraph.nodes(data=True)
            if data["shape"] == "circle"
        )

    # @cached_property
    # def constants(self) -> Tuple[str]:
    #     return tuple(
    #         name
    #         for name, data in self._digraph.nodes(data=True)
    #         if data["shape"] == "..."
    #     )

    @cached_property
    def gates(self) -> Tuple[str]:
        return tuple(
            name
            for name, data in self._digraph.nodes(data=True)
            if data["shape"] == "invhouse"
        )

    @cached_property
    def outputs(self) -> Tuple[str]:
        return tuple(
            name
            for name, data in self._digraph.nodes(data=True)
            if data["shape"] == "doublecircle"
        )

    def successors(self, node_name: str) -> Tuple[str]:
        return tuple(
            dst
            for src, dst in self._digraph.edges
            if src == node_name
        )

    def predecessors(self, node_name: str) -> Tuple[str]:
        return tuple(
            src
            for src, dst in self._digraph.edges
            if dst == node_name
        )

    def function_of(self, node_name: str) -> Optional[str]:
        functions = {'not', 'and', 'or'}
        return next(
            (
                part.strip()
                for part in self._digraph.nodes[node_name]["label"].split("\\n")
                if part in functions
            ),
            None
        )
