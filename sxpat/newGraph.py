from __future__ import annotations
from typing import FrozenSet, Iterable, Sequence, Tuple, Union, Generic, TypeVar

import dataclasses as dc

import networkx as nx
import functools as ft
import itertools as it
import re


__all__ = [
    # nodes
    'AbsDiff', 'And', 'AtLeast', 'AtMost', 'BoolConstant', 'BoolVariable', 'Copy',
    'Equals', 'GreaterEqualThan', 'GreaterThan', 'If', 'Implies', 'IntConstant',
    'IntVariable', 'LessEqualThan', 'LessThan', 'Multiplexer', 'Node', 'Not',
    'OperationNode', 'Or', 'PlaceHolder', 'Sum', 'Switch', 'Target', 'ToInt', 'Valued',
    #
    'boolean_nodes', 'integer_nodes', 'untyped_nodes', 'contact_nodes', 'origin_nodes', 'end_nodes',
    # graphs
    'Graph', 'GGraph', 'CGraph', 'SGraph', 'TGraph',
]

T = TypeVar('T', int, bool)


# > nodes


# abstracts


@dc.dataclass(frozen=True)
class Node:
    name: str
    weight: int = None
    in_subgraph: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, 'in_subgraph', bool(self.in_subgraph))
        # assert re.match(r'^\w+$', self.name), f'The name `{self.name}` is invalid, it must match regex `\w+`.'

    def copy(self, **update):
        return type(self)(**{**vars(self), **update})


@dc.dataclass(frozen=True)
class Valued(Generic[T]):
    value: T = None


@dc.dataclass(frozen=True)
class OperationNode(Node):
    items: Tuple[str, ...] = tuple()

    def __post_init__(self, required_items_count: int = None):
        object.__setattr__(self, 'items',  tuple(i.name if isinstance(i, Node) else i for i in self.items))
        if required_items_count is not None and len(self.items) != required_items_count:
            raise RuntimeError(f'Wrong items count (expected {required_items_count}) in node {self.name} of class {type(self).__name__}')


@dc.dataclass(frozen=True, repr=False)
class Op1Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(1)

    @property
    def item(self) -> str:
        return self.items[0]


@dc.dataclass(frozen=True, repr=False)
class Op2Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(2)


@dc.dataclass(frozen=True, repr=False)
class Op3Node(OperationNode):
    def __post_init__(self):
        super().__post_init__(3)


@dc.dataclass(frozen=True, repr=False)
class Ord2Node(Op2Node):
    @property
    def left(self) -> str:
        return self.items[0]

    @property
    def right(self) -> str:
        return self.items[1]


# inputs


@dc.dataclass(frozen=True, repr=False)
class BoolVariable(Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class IntVariable(Node):
    pass


# constants


@dc.dataclass(frozen=True)
class BoolConstant(Valued[bool], Node):
    pass


@dc.dataclass(frozen=True)
class IntConstant(Valued[bool], Node):
    pass

# output


@dc.dataclass(frozen=True, repr=False)
class Copy(Op1Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class Target(Copy):  # TODO:MARCO: or result/question/...?
    pass


# placeholder


@dc.dataclass(frozen=True, repr=False)
class PlaceHolder(Node):
    pass


# bool operations


@dc.dataclass(frozen=True, repr=False)
class Not(Op1Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class And(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class Or(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class Implies(Ord2Node):
    pass


# int operations


@dc.dataclass(frozen=True, repr=False)
class ToInt(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class Sum(OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class AbsDiff(Ord2Node):
    pass


# comparison operations


@dc.dataclass(frozen=True, repr=False)
class Equals(Op2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class AtLeast(Valued[int], OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class AtMost(Valued[int], OperationNode):
    pass


@dc.dataclass(frozen=True, repr=False)
class LessThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class LessEqualThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class GreaterThan(Ord2Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class GreaterEqualThan(Ord2Node):
    pass


# branching operations


@dc.dataclass(frozen=True, repr=False)
class Multiplexer(Op3Node):
    @property
    def origin(self) -> str:
        return self.items[0]

    @property
    def parameter_1(self) -> str:
        return self.items[1]

    @property
    def parameter_2(self) -> str:
        return self.items[2]


@dc.dataclass(frozen=True, repr=False)
class Switch(Op3Node):
    @property
    def origin(self) -> str:
        return self.items[0]

    @property
    def parameter(self) -> str:
        return self.items[1]

    @property
    def off_value(self) -> str:
        return self.items[2]


@dc.dataclass(frozen=True, repr=False)
class If(Op3Node):
    @property
    def contition(self) -> str:
        return self.items[0]

    @property
    def if_true(self) -> str:
        return self.items[1]

    @property
    def if_false(self) -> str:
        return self.items[2]


# TODO:WIP: global nodes


@dc.dataclass(frozen=True, repr=False)
class Min(Op1Node):
    pass


@dc.dataclass(frozen=True, repr=False)
class Max(Op1Node):
    pass


#
boolean_nodes = (BoolVariable, BoolConstant, Not, And, Or, Implies, Equals, AtLeast, AtMost, LessThan, LessEqualThan, GreaterThan, GreaterEqualThan,)
integer_nodes = (IntVariable, IntConstant, ToInt, Sum, AbsDiff,)
untyped_nodes = (Copy, Target, Multiplexer, Switch, If,)
#
contact_nodes = (PlaceHolder,)  # TODO:MARCO: what name should we use?
#
origin_nodes = (BoolVariable, BoolConstant, IntVariable, IntConstant)
end_nodes = (Copy, Target)

# > graphs


class Graph:
    """Generic graph."""

    K = object()
    EXTRA: Sequence[str] = ()

    def __init__(self, nodes: Iterable[Node],
                 *, _inner: nx.DiGraph = None
                 ) -> None:
        # generate inner mutable structure
        if _inner is None:
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
                for src_name in node.items
            )
            if len(node_names_in_edges - defined_node_names) > 0:
                raise RuntimeError("Some nodes are not defined")

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
                for src_name in node.items
            )

        self._graph: nx.DiGraph = nx.freeze(_inner)

    def __getitem__(self, key: str) -> Node:
        return self._graph.nodes[key][self.K]

    def __eq__(self, other: object) -> bool:
        return (
            type(self) == type(other)
            and frozenset(self.nodes) == frozenset(other.nodes)
        )

    @ft.cached_property
    def nodes(self) -> Tuple[Node, ...]:
        """Sequence of nodes in topological order."""
        return tuple(self._graph.nodes[name][self.K] for name in nx.topological_sort(self._graph))

    def predecessors(self, node_or_name: Union[str, Node]) -> Tuple[Node, ...]:
        node_name = node_or_name.name if isinstance(node_or_name, Node) else node_or_name
        node = self._graph.nodes[node_name][self.K]
        # we iterate over the .predecessors instead of the .items, so even if `node` is not an OperationNode it still works
        return tuple(sorted(
            (self._graph.nodes[_name][self.K] for _name in self._graph.predecessors(node_name)),
            key=lambda _n: node.items.index(_n.name)
        ))

    def successors(self, node_or_name: Union[str, Node]) -> Tuple[OperationNode, ...]:
        node_name = node_or_name.name if isinstance(node_or_name, Node) else node_or_name
        return tuple(self._graph.nodes[_name][self.K] for _name in self._graph.successors(node_name))

    @ft.cached_property
    def constants(self) -> Tuple[Node, ...]:
        return tuple(node for node in self.nodes if isinstance(node, (BoolConstant, IntConstant)))

    # @ft.cached_property
    # def origins(self) -> Tuple[Node, ...]:
    #     return tuple(node for node in self.nodes if isinstance(node, (BoolVariable, IntVariable, BoolConstant, IntConstant)))

    @ft.cached_property
    def operations(self) -> Tuple[OperationNode, ...]:
        return tuple(node for node in self.nodes if not isinstance(node, (*contact_nodes, *origin_nodes, *end_nodes)))

    @ft.cached_property
    def end_nodes(self) -> Tuple[Copy, ...]:
        return tuple(node for node in self.nodes if isinstance(node, (Copy, Target)))

    # @ft.cached_property
    # def non_gates(self) -> Tuple[Node, ...]:
    #     return tuple(node for node in self.nodes if not isinstance(node, OperationNode))

    @ft.cached_property
    def targets(self) -> Tuple[Target, ...]:
        return tuple(node for node in self.nodes if isinstance(node, Target))


class GGraph(Graph):
    """Graph with inputs and outputs."""

    EXTRA = ('inputs_names', 'outputs_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Iterable[str] = (), outputs_names: Iterable[str] = (),
                 *, _inner: nx.DiGraph = None,
                 ) -> None:
        # construct base
        super().__init__(nodes, _inner=_inner)

        # freeze local instances
        self.inputs_names = tuple(inputs_names)
        self.outputs_names = tuple(outputs_names)
        # self.int_result = next(node for node in self.nodes if isinstance(node, ToInt))

    def __eq__(self, other: object) -> bool:
        return (
            super().__eq__(other)
            and self.inputs_names == other.inputs_names
            and self.outputs_names == other.outputs_names
        )

    @classmethod
    def from_Graph(cls, graph: Graph) -> GGraph:
        """**WARNING**: this function makes (**possibly wrong**) assumptions for which nodes are inputs or outputs."""
        inputs_names = (node.name for node in graph.nodes if isinstance(node, BoolVariable))
        outputs_names = (node.name for node in graph.nodes if isinstance(node, Copy))
        return cls(None, inputs_names, outputs_names, _inner=graph._graph)

    @ft.cached_property
    def inputs(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self.inputs_names)

    @ft.cached_property
    def outputs(self) -> Tuple[Node, ...]:
        return tuple(self._graph.nodes[name][self.K] for name in self.outputs_names)

    def with_prefix(self, prefix: str):
        """Returns a copy of the current graph with all nodes names (and items names) updated with the prefix (except the inputs)"""

        nodes = []
        for node in self.nodes:
            if node in self.inputs:
                nodes.append(node)
            elif isinstance(node, OperationNode):
                items = (name if name in self.inputs_names else f'{prefix}{name}' for name in node.items)
                nodes.append(node.copy(name=f'{prefix}{node.name}', items=items))
            else:
                nodes.append(node.copy(name=f'{prefix}{node.name}'))

        outputs_names = (f'{prefix}{name}' for name in self.outputs_names)

        return type(self)(nodes, self.inputs_names, outputs_names)


class SGraph(GGraph):
    """Graph with inputs, outputs and subgraph."""

    @ft.cached_property
    def subgraph_nodes(self) -> Tuple[Node, ...]:
        return tuple(node for node in self.nodes if node.in_subgraph)

    @ft.cached_property
    def subgraph_inputs(self) -> Tuple[Node, ...]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        return tuple(it.chain.from_iterable(
            (pred for pred in self.predecessors(node) if not pred.in_subgraph)
            for node in self.subgraph_nodes
        ))

    @ft.cached_property
    def subgraph_outputs(self) -> Tuple[Node, ...]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        return tuple(
            node
            for node in self.subgraph_nodes
            if any(not succ.in_subgraph for succ in self.successors(node))
        )


class TGraph(SGraph):
    """Graph with inputs, outputs and template (replacing subgraph)."""

    EXTRA = (*SGraph.EXTRA, 'parameters_names')

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
        return tuple(self._graph.nodes[name][self.K] for name in self.parameters_names)


class CGraph(Graph):
    """Graph containing the constraints."""

    @staticmethod
    def is_placeholder(node: Node) -> bool:
        return isinstance(node, PlaceHolder)

    @ft.cached_property
    def placeholders(self) -> FrozenSet[PlaceHolder]:
        return frozenset(node for node in self.nodes if CGraph.is_placeholder(node))
