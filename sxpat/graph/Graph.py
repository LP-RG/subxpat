from __future__ import annotations
from typing_extensions import Self
from typing import Any, FrozenSet, Iterable, Mapping, Sequence, Tuple, TypeVar, Union
from types import MappingProxyType

import networkx as nx
import functools as ft
import itertools as it

from .Node import *


__all__ = ['Graph', 'IOGraph', 'CGraph', 'SGraph', 'PGraph',
           '_Graph']


class Graph:
    """Generic graph."""

    K = object()
    EXTRAS: Sequence[str] = ()

    def __init__(self, nodes: Iterable[Node]) -> None:
        """
            Creates a new graph from the given nodes.

            @authors: Marco Biasion
        """

        nodes = tuple(nodes)

        # check for graph correctness
        defined_node_names = set(
            node.name
            for node in nodes
        )
        node_names_in_edges = set(
            src_name
            for node in nodes
            if isinstance(node, OperationNode)
            for src_name in node.operands
        )
        if len(node_names_in_edges - defined_node_names) > 0:
            print(*(node_names_in_edges - defined_node_names), sep='\n')
            raise RuntimeError('Some nodes are not defined')

        # construct digraph
        _inner = nx.DiGraph()
        _inner.add_nodes_from(
            (node.name, {self.K: node})
            for node in nodes
        )
        _inner.add_edges_from(
            (src_name, dst_name)
            for dst_name, data in _inner.nodes(data=True)
            if isinstance(node := data[self.K], OperationNode)
            for src_name in node.operands
        )

        # freeze inner structure
        self._inner: nx.DiGraph = nx.freeze(_inner)

    def copy(self, nodes: Iterable[Node] = None, **extras) -> Self:
        return type(self)(self.nodes if nodes is None else nodes, **{**self.extras, **extras})

    @ft.cached_property
    def extras(self) -> Mapping[str, Any]:
        return MappingProxyType({_ex: getattr(self, _ex) for _ex in self.EXTRAS})

    def __getitem__(self, name: str) -> Node:
        return self._inner.nodes[name][self.K]

    def __contains__(self, name: str) -> bool:
        return name in self._inner

    def __eq__(self, other: object) -> bool:
        return (
            type(self) == type(other)
            and self.nodes == other.nodes
        )

    @ft.cached_property
    def nodes(self) -> Tuple[Node, ...]:
        """Sequence of nodes in the unique lexicographical topological order."""
        return tuple(self._inner.nodes[name][self.K] for name in nx.lexicographical_topological_sort(self._inner))

    def predecessors(self, node_or_name: Union[str, Node]) -> Tuple[Node, ...]:
        node_name = node_or_name.name if isinstance(node_or_name, Node) else node_or_name
        node = self._inner.nodes[node_name][self.K]
        # we iterate over the .predecessors instead of the .operands, so even if `node` is not an OperationNode it still works
        return tuple(sorted(
            (self._inner.nodes[_name][self.K] for _name in self._inner.predecessors(node_name)),
            key=lambda _n: node.operands.index(_n.name)
        ))

    def successors(self, node_or_name: Union[str, Node]) -> Tuple[OperationNode, ...]:
        node_name = node_or_name.name if isinstance(node_or_name, Node) else node_or_name
        return tuple(self._inner.nodes[_name][self.K] for _name in self._inner.successors(node_name))

    @ft.cached_property
    def constants(self) -> Tuple[Node, ...]:
        return tuple(node for node in self.nodes if isinstance(node, (BoolConstant, IntConstant)))

    # @ft.cached_property
    # def origins(self) -> Tuple[Node, ...]:
    #     return tuple(node for node in self.nodes if isinstance(node, (BoolVariable, IntVariable, BoolConstant, IntConstant)))

    @ft.cached_property
    def operations(self) -> Tuple[OperationNode, ...]:
        return tuple(node for node in self.nodes if not isinstance(node, (*contact_nodes, *origin_nodes, Target)))

    @ft.cached_property
    def end_nodes(self) -> Tuple[Copy, ...]:
        return tuple(node for node in self.nodes if isinstance(node, (Copy, Target)))

    # @ft.cached_property
    # def non_gates(self) -> Tuple[Node, ...]:
    #     return tuple(node for node in self.nodes if not isinstance(node, OperationNode))

    @ft.cached_property
    def targets(self) -> Tuple[Target, ...]:
        return tuple(node for node in self.nodes if isinstance(node, Target))


_Graph = TypeVar('_Graph', bound=Graph)


class IOGraph(Graph):
    """Graph with inputs and outputs."""

    EXTRAS = ('inputs_names', 'outputs_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Iterable[str] = (), outputs_names: Iterable[str] = ()
                 ) -> None:
        # construct base
        super().__init__(nodes)

        # freeze local instances
        self.inputs_names = tuple(inputs_names)
        self.outputs_names = tuple(outputs_names)

    def __eq__(self, other: object) -> bool:
        return (
            super().__eq__(other)
            and self.inputs_names == other.inputs_names
            and self.outputs_names == other.outputs_names
        )

    @ft.cached_property
    def inputs(self) -> Tuple[Node, ...]:
        return tuple(self._inner.nodes[name][self.K] for name in self.inputs_names)

    @ft.cached_property
    def outputs(self) -> Tuple[Node, ...]:
        return tuple(self._inner.nodes[name][self.K] for name in self.outputs_names)

    @ft.cached_property
    def inners(self) -> Tuple[Node, ...]:
        in_out_set = frozenset((*self.inputs_names, *self.outputs_names))
        return tuple(n for n in self.nodes if n.name not in in_out_set)


class SGraph(IOGraph):
    """Graph with inputs, outputs and subgraph."""

    @ft.cached_property
    def subgraph_nodes(self) -> Tuple[Node, ...]:
        return tuple(node for node in self.nodes if node.in_subgraph)

    @ft.cached_property
    def subgraph_inputs(self) -> Tuple[Node, ...]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        return tuple(frozenset(it.chain.from_iterable(
            (pred for pred in self.predecessors(node) if not pred.in_subgraph)
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    def subgraph_outputs(self) -> Tuple[Node, ...]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        return tuple(
            node
            for node in self.subgraph_nodes
            if any(not succ.in_subgraph for succ in self.successors(node))
        )


class PGraph(SGraph):
    """Graph with inputs, outputs and parameters (for example, parameters of a template)."""

    EXTRAS = (*SGraph.EXTRAS, 'parameters_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Iterable[str] = (), outputs_names: Iterable[str] = (),
                 parameters_names: Iterable[str] = (),
                 ) -> None:

        super().__init__(nodes, inputs_names, outputs_names)

        # freeze local instances
        self.parameters_names = tuple(parameters_names)

    def __eq__(self, other: object) -> bool:
        return (
            super().__eq__(other)
            and frozenset(self.parameters_names) == frozenset(other.parameters_names)
        )

    @ft.cached_property
    def parameters(self) -> Tuple[Node, ...]:
        return tuple(self._inner.nodes[name][self.K] for name in self.parameters_names)


class CGraph(Graph):
    """Graph containing the constraints."""

    @staticmethod
    def is_placeholder(node: Node) -> bool:
        return isinstance(node, PlaceHolder)

    @ft.cached_property
    def placeholders(self) -> FrozenSet[PlaceHolder]:
        return frozenset(node for node in self.nodes if CGraph.is_placeholder(node))
