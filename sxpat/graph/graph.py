import operator as op
from typing import AbstractSet, Any, Iterable, Literal, Mapping, Optional, Sequence, TypeVar, Union, Final, final, Self, cast, overload
from types import MappingProxyType
from components import Subgraph, Weight, Type, Topology, Component

import networkx as nx
import functools as ft
import itertools as it

from .node import (
    AnyVariable, BoolConstant, Expression, Extras, Node, Operation, Constant, GlobalTask,
    #
    BoolVariable, PlaceHolder,
    Target, Constraint,
    #
    AnyNode, AnyConstant, AnyExpression, AnyGlobalObjective,
    AnyNonEndPoint, AnyNonEntryPoint, Variable,
)
from .error import UndefinedNodeError


__all__ = [
    #
    'Graph',
    #
    'IOGraph', 'SGraph', 'PGraph',
    'CGraph',
    #
    'T_Graph', 'AnyGraph', 'T_AnyGraph'
]


class Graph:
    """Generic graph."""

    K = object()
    EXTRAS: Sequence[str] = ()

    def __init__(self, nodes: Iterable[AnyNode]) -> None:
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
        if len(missing := (node_names_in_edges - defined_node_names)) > 0:
            raise UndefinedNodeError(f'The following nodes are not defined but edges from them exist: {missing}')

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
        self._inner: Final[nx.DiGraph] = nx.freeze(_inner)

    def copy(self, nodes: Optional[Iterable[AnyNode]] = None, **extras) -> Self:
        return type(self)(self.nodes if nodes is None else nodes, **{**self.extras, **extras})

    @ft.cached_property
    def extras(self) -> Mapping[str, Any]:
        return MappingProxyType({_ex: getattr(self, _ex) for _ex in self.EXTRAS})

    @final
    def __getitem__(self, name: str) -> AnyNode:
        return self._inner.nodes[name][self.K]

    @final
    def __contains__(self, name: str) -> bool:
        return name in self._inner

    def __eq__(self, other) -> bool:
        return (
            type(self) == type(other)
            and self.nodes == other.nodes  # no need to cast to set before comparison (see .nodes)
        )

    @ft.cached_property
    @final
    def nodes(self) -> Sequence[AnyNode]:
        """Sequence of nodes in the unique lexicographical topological order."""
        return tuple(self._inner.nodes[name][self.K] for name in nx.lexicographical_topological_sort(self._inner))

    @final
    def predecessors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEndPoint]:
        node_name = self._get_name(node_or_name)
        node = self._inner.nodes[node_name][self.K]
        # we iterate over the .predecessors instead of the .operands, so even if `node` is not an Operation it still works
        return tuple(sorted(
            (self._inner.nodes[_name][self.K] for _name in self._inner.predecessors(node_name)),
            key=lambda _n: node.operands.index(_n.name)
        ))

    @final
    def successors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEntryPoint]:
        return tuple(
            self._inner.nodes[_name][self.K]
            for _name in self._inner.successors(self._get_name(node_or_name))
        )

    @ft.cached_property
    @final
    def variables(self) -> Sequence[AnyVariable]:
        return tuple(node for node in self.nodes if isinstance(node, Variable))

    @ft.cached_property
    @final
    def constants(self) -> Sequence[AnyConstant]:
        return tuple(node for node in self.nodes if isinstance(node, Constant))

    @ft.cached_property
    @final
    def variables(self) -> Sequence[AnyVariable]:
        return tuple(node for node in self.nodes if isinstance(node, Variable))

    @ft.cached_property
    @final
    def expressions(self) -> Sequence[AnyExpression]:
        return tuple(node for node in self.nodes if isinstance(node, Expression))

    @ft.cached_property
    @final
    def targets(self) -> Sequence[Target]:
        return tuple(node for node in self.nodes if isinstance(node, Target))

    def _get_name(self, node_or_name: Union[str, Node]) -> str:
        """Given a node or a node name, returns the node name."""
        return node_or_name.name if isinstance(node_or_name, Node) else node_or_name

# COMMENT:from-MARCO: "from typing import TypedDict" this might help you in simplifying the code below
class ComponentsDict(dict[Literal['Subgraph', 'Topology', 'Weight', 'Type'], Component]):
    @overload
    def __getitem__(self, key: Literal["Subgraph"]) -> Subgraph: ...
    
    @overload
    def __getitem__(self, key: Literal["Topology"]) -> Topology: ...
    
    @overload
    def __getitem__(self, key: Literal["Weight"]) -> Weight: ...
    
    @overload
    def __getitem__(self, key: Literal["Type"]) -> Type: ...

    def __getitem__(self, key: Literal['Subgraph', 'Topology', 'Weight', 'Type']) -> Component:
        return super().__getitem__(key)

class IOGraph(Graph):
    """Graph with inputs and outputs."""

    EXTRAS: Sequence[str] = ('inputs_names', 'outputs_names')
    base_components: ComponentsDict
    extra_components: dict[str, Component]

    # COMMENT:from-MARCO: you can assume that also inputs and outputs will be given by components (one comp. for both, or individually for each, we can discuss about this)
    # COMMENT:from-MARCO: taking in directly the ComponentsDict may be better; we should discuss this.
    def __init__(self, nodes: Iterable[AnyNode],
                 inputs_names: Sequence[str], 
                 outputs_names: Sequence[str],
                 components: Sequence[Component] = list()
                 ) -> None:
        # construct base
        super().__init__(nodes)

        # freeze local instances
        self.inputs_names = tuple(inputs_names)
        self.outputs_names = tuple(outputs_names)
        self.base_components = ComponentsDict([
            (cast(Literal['Subgraph', 'Topology', 'Weight', 'Type'], type(c).__name__), c)
            for c in components
        ])

        # guard
        if len(missing := tuple(name for name in self.inputs_names if name not in self)) > 0:
            raise UndefinedNodeError(f'The following nodes are not defined but are being used as inputs: {missing}')
        if len(missing := tuple(name for name in self.outputs_names if name not in self)) > 0:
            raise UndefinedNodeError(f'The following nodes are not defined but are being used as outputs: {missing}')

    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other)
            and self.inputs_names == other.inputs_names
            and self.outputs_names == other.outputs_names
        )

    @ft.cached_property
    @final
    def inputs(self) -> Sequence[AnyNode]:
        return tuple(self._inner.nodes[name][self.K] for name in self.inputs_names)

    @final
    def input_index_of(self, node_or_name: Union[str, Node]) -> int:
        """Returns the index of the node in the inputs, -1 if the node is not an input."""
        try: return self.inputs_names.index(self._get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def outputs(self) -> Sequence[AnyNode]:
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

    # COMMENT:from-MARCO: the following two methods are very nice QoL (Quality of Life) features to have.
    # the naming of them is a bit counter-intuitive, but the logic is sound.

    @final
    def add_base_component(self, new_component: Subgraph | Topology | Weight | Type) -> IOGraph:
        copy: IOGraph
        new_name = cast(Literal['Subgraph', 'Topology', 'Weight', 'Type'], type(new_component).__name__)
        if len(self.base_components) > 0:
            new_base_components = list()
            new_base_components.append(new_component)
            for name, component in self.base_components.items():
                if name != new_name:
                    new_base_components.append(component)
            copy = IOGraph(self.nodes, self.inputs_names, self.outputs_names, new_base_components)
        else: 
            copy = IOGraph(self.nodes, self.inputs_names, self.outputs_names, [new_component])
        #handle extra components
        inheritable_extra_components: dict[str, Component] = dict()
        for name, component in self.extra_components.items():
            if component.inheritable:
                inheritable_extra_components[name] = component
        copy.extra_components = inheritable_extra_components
        return copy

    @final
    def add_extra_component(self, new_component: Component, new_name: str) -> IOGraph:
        copy: IOGraph
        if len(self.base_components) > 0:
            copy = IOGraph(self.nodes, self.inputs_names, self.outputs_names, list(self.base_components.values()))
        else: 
            copy = IOGraph(self.nodes, self.inputs_names, self.outputs_names)
        #handle extra components
        inheritable_extra_components: dict[str, Component] = dict()
        inheritable_extra_components[new_name] = new_component
        for name, component in self.extra_components.items():
            if component.inheritable and name != new_name:
                inheritable_extra_components[name] = component
        copy.extra_components = inheritable_extra_components
        return copy

    # COMMENT:from-MARCO: the following 4 functionalities could be contained in the component.
    # doing so firther modularise the architecture.
    # note that, doing that requires reasoning about a few extra things, but once that is reasoned about, the rest should be much easier.

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[AnyNode]:
        if not 'Subgraph' in self.base_components:
            print("IoGraph does not possess a subgraph component")
            exit(1)
        subgraph_ids = self.base_components['Subgraph'].nodes_names()
        return tuple(
            node for node in self.nodes
            if isinstance(node, Extras) and node.name in subgraph_ids
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        if not 'Subgraph' in self.base_components:
            print("IoGraph does not possess a subgraph component")
            exit(1)
        subgraph_ids = self.base_components['Subgraph'].nodes_names()
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (
                pred for pred in self.predecessors(node)
                if not isinstance(pred, Extras) or not pred.name in subgraph_ids
            )
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    @final
    def subgraph_outputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        if not 'Subgraph' in self.base_components:
            print("IoGraph does not possess a subgraph component")
            exit(1)
        subgraph_ids = self.base_components['Subgraph'].nodes_names()
        return tuple(sorted(
            (
                node for node in self.subgraph_nodes
                if any(
                    not isinstance(succ, Extras) or not succ.name in subgraph_ids
                    for succ in self.successors(node)
                )
            ),
            key=op.attrgetter('name')
        ))

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        if not 'Subgraph' in self.base_components:
            print("IoGraph does not possess a subgraph component")
            exit(1)
        subgraph_ids = self.base_components['Subgraph'].nodes_names()
        return sum(
            n.name in subgraph_ids for n in self.successors(node_or_name)
            if isinstance(n, Extras)
        )

class SGraph(IOGraph):
    """Graph with inputs, outputs and a subgraph."""

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[AnyNode]:
        return tuple(
            node for node in self.nodes
            if isinstance(node, Extras) and node.in_subgraph
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (
                pred for pred in self.predecessors(node)
                if not isinstance(pred, Extras) or not pred.in_subgraph
            )
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    @final
    def subgraph_outputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        return tuple(sorted(
            (
                node for node in self.subgraph_nodes
                if any(
                    not isinstance(succ, Extras) or not succ.in_subgraph
                    for succ in self.successors(node)
                )
            ),
            key=op.attrgetter('name')
        ))

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        return sum(
            n.in_subgraph for n in self.successors(node_or_name)
            if isinstance(n, Extras)
        )


class PGraph(SGraph):
    """Graph with inputs, outputs and parameters (for example, parameters of a template)."""

    EXTRAS: Sequence[str] = (*SGraph.EXTRAS, 'parameters_names')

    def __init__(self, nodes: Iterable[AnyNode],
                 inputs_names: Sequence[str], outputs_names: Sequence[str],
                 parameters_names: Sequence[str],
                 ) -> None:

        super().__init__(nodes, inputs_names, outputs_names)

        # freeze local instances
        self.parameters_names = tuple(parameters_names)

        # guard
        if len(missing := tuple(name for name in self.parameters_names if name not in self)) > 0:
            raise UndefinedNodeError(f'The following nodes are not defined but are being used as parameters: {missing}')

    def __eq__(self, other) -> bool:
        return (
            super().__eq__(other)
            and frozenset(self.parameters_names) == frozenset(other.parameters_names)
        )

    @ft.cached_property
    @final
    def parameters(self) -> Sequence[Union[BoolVariable, BoolConstant]]:
        return tuple(self._inner.nodes[name][self.K] for name in self.parameters_names)


class CGraph(Graph):
    """Graph containing the constraints."""

    @ft.cached_property
    @final
    def placeholders(self) -> AbstractSet[PlaceHolder]:
        """The sequence of all `Constraint` node in the graph."""
        return dict.fromkeys(node for node in self.nodes if isinstance(node, PlaceHolder)).keys()

    @ft.cached_property
    @final
    def constraints(self) -> Sequence[Constraint]:
        """The sequence of all `Constraint` node in the graph."""
        return tuple(node for node in self.nodes if isinstance(node, Constraint))

    @ft.cached_property
    @final
    def global_tasks(self) -> AbstractSet[AnyGlobalObjective]:
        """The set of all `GlobalTask` nodes in the graph."""
        return dict.fromkeys(node for node in self.nodes if isinstance(node, GlobalTask)).keys()


# > Typing help


T_Graph = TypeVar('T_Graph', Graph, IOGraph, SGraph, PGraph, CGraph)
T_IOGraph = TypeVar('T_IOGraph', IOGraph, SGraph, PGraph)
AnyGraph = Union[Graph, IOGraph, SGraph, PGraph, CGraph]
T_AnyGraph = TypeVar('T_AnyGraph', bound=AnyGraph)
