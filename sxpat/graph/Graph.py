from __future__ import annotations
from typing_extensions import Self, final
from typing import AbstractSet, Any, Iterable, Mapping, Sequence, TypeVar, Union
from types import MappingProxyType

import networkx as nx
import functools as ft
import itertools as it

from .Node import (
    Expression, Node, Operation, Constant, GlobalTask,
    #
    BoolVariable, PlaceHolder,
    Target, Constraint,
    #
    OperationNode, ConstantNode, GlobalTaskNode, ExpressionNode,
)


__all__ = [
    #
    'Graph',
    #
    'IOGraph', 'SGraph', 'PGraph',
    'CGraph',
    #
    '_Graph',
]


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
            if isinstance(node, Operation)
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
            if isinstance(node := data[self.K], Operation)
            for src_name in node.operands
        )

        # freeze inner structure
        self._inner: nx.DiGraph = nx.freeze(_inner)

    def copy(self, nodes: Iterable[Node] = None, **extras) -> Self:
        return type(self)(self.nodes if nodes is None else nodes, **{**self.extras, **extras})

    @ft.cached_property
    def extras(self) -> Mapping[str, Any]:
        return MappingProxyType({_ex: getattr(self, _ex) for _ex in self.EXTRAS})

    @final
    def __getitem__(self, name: str) -> Node:
        return self._inner.nodes[name][self.K]

    @final
    def __contains__(self, name: str) -> bool:
        return name in self._inner

    def __eq__(self, other: object) -> bool:
        return (
            type(self) == type(other)
            and self.nodes == other.nodes  # no need to cast to set before comparison (see .nodes)
        )

    @ft.cached_property
    @final
    def nodes(self) -> Sequence[Node]:
        """Sequence of nodes in the unique lexicographical topological order."""
        return tuple(self._inner.nodes[name][self.K] for name in nx.lexicographical_topological_sort(self._inner))

    @final
    def predecessors(self, node_or_name: Union[str, Node]) -> Sequence[Node]:
        node_name = self._get_name(node_or_name)
        node = self._inner.nodes[node_name][self.K]
        # we iterate over the .predecessors instead of the .operands, so even if `node` is not an Operation it still works
        return tuple(sorted(
            (self._inner.nodes[_name][self.K] for _name in self._inner.predecessors(node_name)),
            key=lambda _n: node.operands.index(_n.name)
        ))

    @final
    def successors(self, node_or_name: Union[str, Node]) -> Sequence[OperationNode]:
        return tuple(
            self._inner.nodes[_name][self.K]
            for _name in self._inner.successors(self._get_name(node_or_name))
        )

    @ft.cached_property
    @final
    def constants(self) -> Sequence[ConstantNode]:
        return tuple(node for node in self.nodes if isinstance(node, Constant))

    @ft.cached_property
    @final
    def expressions(self) -> Sequence[ExpressionNode]:
        return tuple(node for node in self.nodes if isinstance(node, Expression))

    @ft.cached_property
    @final
    def targets(self) -> Sequence[Target]:
        return tuple(node for node in self.nodes if isinstance(node, Target))

    def _get_name(self, node_or_name: Union[str, Node]) -> str:
        """Given a node or a node name, returns the node name."""
        return node_or_name.name if isinstance(node_or_name, Node) else node_or_name


_Graph = TypeVar('_Graph', bound=Graph)


class IOGraph(Graph):
    """Graph with inputs and outputs."""

    EXTRAS = ('inputs_names', 'outputs_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Sequence[str], outputs_names: Sequence[str]
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
    @final
    def inputs(self) -> Sequence[Node]:
        return tuple(self._inner.nodes[name][self.K] for name in self.inputs_names)

    @final
    def input_index_of(self, node_or_name: Union[str, Node]) -> int:
        """Returns the index of the node in the inputs, -1 if the node is not an input."""
        try: return self.inputs_names.index(self._get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def outputs(self) -> Sequence[Node]:
        return tuple(self._inner.nodes[name][self.K] for name in self.outputs_names)

    @final
    def output_index_of(self, node_or_name: Union[str, Node]) -> int:
        """Returns the index of the node in the outputs, -1 if the node is not an output."""
        try: return self.outputs_names.index(self._get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def inners(self) -> Sequence[Node]:
        in_out_set = frozenset((*self.inputs_names, *self.outputs_names))
        return tuple(n for n in self.nodes if n.name not in in_out_set)


class SGraph(IOGraph):
    """Graph with inputs, outputs and a subgraph."""

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[Node]:
        return tuple(node for node in self.nodes if node.in_subgraph)

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[Node]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (pred for pred in self.predecessors(node) if not pred.in_subgraph)
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    @final
    def subgraph_outputs(self) -> Sequence[Node]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        return tuple(
            node
            for node in self.subgraph_nodes
            if any(not succ.in_subgraph for succ in self.successors(node))
        )

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        return sum(n.in_subgraph for n in self.successors(self._get_name(node_or_name)))


class PGraph(SGraph):
    """Graph with inputs, outputs and parameters (for example, parameters of a template)."""

    EXTRAS = (*SGraph.EXTRAS, 'parameters_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Sequence[str], outputs_names: Sequence[str],
                 parameters_names: Sequence[str],
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
    @final
    def parameters(self) -> Sequence[BoolVariable]:
        return tuple(self._inner.nodes[name][self.K] for name in self.parameters_names)


class CGraph(Graph):
    """Graph containing the constraints."""

    @ft.cached_property
    @final
    def placeholders(self) -> AbstractSet[PlaceHolder]:
        """The sequence of all `Constraint` node in the graph."""
        return frozenset(node for node in self.nodes if isinstance(node, Constraint))

    @ft.cached_property
    @final
    def constraints(self) -> Sequence[Constraint]:
        """The sequence of all `Constraint` node in the graph."""
        return tuple(node for node in self.nodes if isinstance(node, Constraint))

    @ft.cached_property
    @final
    def global_tasks(self) -> AbstractSet[GlobalTaskNode]:
        """The set of all `GlobalTask` nodes in the graph."""
        return frozenset(node for node in self.nodes if isinstance(node, GlobalTask))
