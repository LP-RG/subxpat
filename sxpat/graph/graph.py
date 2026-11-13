import operator as op
from typing import Any, Iterable, List, Literal, Mapping, Optional, Sequence, TypeVar, Union, Final, final, Self, cast, overload
from types import MappingProxyType
from .components import Subgraph, Weight, Types, Topology, Component, Parameter, IO, Constraints, available_graph_components

import networkx as nx
import functools as ft
import itertools as it

from .node import (
    AnyVariable, Expression, Node, Operation, Constant,
    #
    Target,
    #
    AnyNode, AnyConstant, AnyExpression,
    AnyNonEndPoint, AnyNonEntryPoint, Variable,
)
from .error import UndefinedNodeError


__all__ = [
    #
    'Graph',
    #
    'T_Graph', 'AnyGraph', 'T_AnyGraph'
]

# COMMENT:from-MARCO: "from typing import TypedDict" this might help you in simplifying the code below
# from-ILIA: I already explored this solution before coming up with the current one, I couldn't find a solution
# with "TypedDict" that came close to the current behaviour
# COMMENT:from-MARCO: ok, then let's leave it as it is (leave also this conversation)
class ComponentsDict(dict[available_graph_components, Component]):
    @overload
    def __getitem__(self, key: Literal["Subgraph"]) -> Subgraph: ...
    
    @overload
    def __getitem__(self, key: Literal["Topology"]) -> Topology: ...
    
    @overload
    def __getitem__(self, key: Literal["min_weight"]) -> Weight: ...
    @overload
    def __getitem__(self, key: Literal["max_weight"]) -> Weight: ...

    @overload
    def __getitem__(self, key: Literal["Parameter"]) -> Parameter: ...

    @overload
    def __getitem__(self, key: Literal["IO"]) -> IO: ...

    @overload
    def __getitem__(self, key: Literal["Constraints"]) -> Constraints: ...

    @overload
    def __getitem__(self, key: Literal["Types"]) -> Types: ...

    def __getitem__(self, key: available_graph_components) -> Component:
        return super().__getitem__(key)

class Graph:
    """Generic graph."""

    EXTRAS: Sequence[str] = ()
    base_components: ComponentsDict
    extra_components: dict[str, Component]

    # from-MARCO: BUG: you never create a local list from components, so in the best case scenario, the system crashes, but in the worst, the default list gets reused over and over in different calls, possibly propagating a state that should not be there. 
    # from-ILIA: fixed
    def __init__(self, nodes: Iterable[AnyNode], components: Sequence[Component] = list()) -> None:
        """
        Creates a new graph from the given nodes.

        :authors: Marco Biasion, Ilia Zeller
        """

        nodes = tuple(nodes)
        components = list(components)

        #Add default Subgraph and Weight components if they're not passed as argument 
        #(this because the Node structure had default weight = None and in_subgraph = False)
        if not any(type(c).__name__ == 'Subgraph' for c in components):
            components.append(Subgraph(set()))
        
        if not any(type(c).__name__ == 'Weight' for c in components):
            components.append(Weight(dict()))

        #Add Types component
        types_mapping: dict[str, type] = dict()
        for n in nodes:
            types_mapping[n.name] = type(n)
        components.append(Types(types_mapping))

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
            node.name
            for node in nodes
        )
        _inner.add_edges_from(
            (src_name, dst_name)
            for dst_name, data in _inner.nodes(data=True)
            if isinstance(node := data[self.K], Operation)
            for src_name in node.operands
        )

        # # freeze inner structure
        # self._inner: Final[nx.DiGraph] = nx.freeze(_inner)

        #Add Topology component
        components.append(Topology(_inner))

        self.base_components = ComponentsDict([
            (cast(available_graph_components, type(c).__name__), c.with_graph(self))
            for c in components
        ])
        self.extra_components = dict()

        # parameters guard
        if self.has_base_component('Parameter'):
            if len(missing := tuple(name for name in self.base_components['Parameter'].parameters_names if name not in self)) > 0:
                raise UndefinedNodeError(f'The following nodes are not defined but are being used as parameters: {missing}')

        # inputs/outputs guard
        if self.has_base_component('IO'):
            if len(missing := tuple(name for name in self.base_components['IO'].inputs_names if name not in self)) > 0:
                raise UndefinedNodeError(f'The following nodes are not defined but are being used as inputs: {missing}')
            if len(missing := tuple(name for name in self.base_components['IO'].outputs_names if name not in self)) > 0:
                raise UndefinedNodeError(f'The following nodes are not defined but are being used as outputs: {missing}')
        

    def copy(self, nodes: Optional[Iterable[AnyNode]] = None, new_base_components: List[Component] = list()) -> Self:
        # from-ILIA: TODO refactor this method to make it less "hardcoded" (lines 149-150)
        # from-MARCO: yes, we can also discuss this together if you want, so we stay aligned on the requirements
        copy = type(self)(self.nodes if nodes is None else nodes)
        #handle base components
        copy_base_components = new_base_components
        new_base_components_types = [type(c).__name__ for c in new_base_components]
        for name, component in self.base_components.items():
            if (not name in new_base_components_types) and component.inheritable:
                copy_base_components.append(component)
        copy_base_components.append(copy.base_components['Types'])
        copy_base_components.append(copy.base_components['Topology'])
        copy.base_components = ComponentsDict([
            (cast(available_graph_components, type(c).__name__), c.with_graph(copy))
            for c in copy_base_components
        ])
        #handle extra components
        inheritable_extra_components: dict[str, Component] = dict()
        for name, component in self.extra_components.items(): 
            if component.inheritable:
                inheritable_extra_components[name] = component.with_graph(copy)
        copy.extra_components = inheritable_extra_components
        return copy

    @ft.cached_property
    def extras(self) -> Mapping[str, Any]:
        return MappingProxyType({_ex: getattr(self, _ex) for _ex in self.EXTRAS})

    @final
    def __getitem__(self, name: str) -> AnyNode:
        return self.base_components['Topology'].get().nodes[name][self.K]

    @final
    def __contains__(self, name: str) -> bool:
        return name in self.base_components['Topology'].get()

    def __eq__(self, other) -> bool:
        # from-MARCO: this is to be discussed
        if self.has_base_component('IO') != other.has_base_component('IO'):
            return False
        if self.has_base_component('Parameter') != other.has_base_component('Parameter'):
            return False
        if self.has_base_component('IO'):
            if (self.base_components['IO'].inputs_names != other.base_components['IO'].inputs_names 
                or self.base_components['IO'].outputs_names != other.base_components['IO'].outputs_names):
                return False
        if self.has_base_component('Parameter'):
            if (frozenset(self.base_components['Parameter'].parameters_names) 
                != frozenset(other.base_components['Parameter'].parameters_names)):
                return False
        return (
            type(self) == type(other)
            and self.nodes == other.nodes  # no need to cast to set before comparison (see .nodes)
        )

    @ft.cached_property
    @final
    def nodes(self) -> Sequence[AnyNode]:
        """Sequence of nodes in the unique lexicographical topological order."""
        topology = self.base_components['Topology'].get()
        return tuple(topology.nodes[name][self.K] for name in nx.lexicographical_topological_sort(topology))

    @final
    def predecessors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEndPoint]:
        topology = self.base_components['Topology'].get()
        node_name = self._get_name(node_or_name)
        node = topology.nodes[node_name][self.K]
        # we iterate over the .predecessors instead of the .operands, so even if `node` is not an Operation it still works
        return tuple(sorted(
            (topology.nodes[_name][self.K] for _name in topology.predecessors(node_name)),
            key=lambda _n: node.operands.index(_n.name)
        ))

    @final
    def successors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEntryPoint]:
        topology = self.base_components['Topology'].get()
        return tuple(
            topology.nodes[_name][self.K]
            for _name in topology.successors(self._get_name(node_or_name))
        )

    @ft.cached_property
    @final
    def variables(self) -> Sequence[AnyVariable]:
        types_component = self.base_components['Types']
        return tuple(node for node in self.nodes if types_component.instance_of(node, [Variable]))

    @ft.cached_property
    @final
    def constants(self) -> Sequence[AnyConstant]:
        types_component = self.base_components['Types']
        return tuple(node for node in self.nodes if types_component.instance_of(node, [Constant]))

    @ft.cached_property
    @final
    def expressions(self) -> Sequence[AnyExpression]:
        types_component = self.base_components['Types']
        return tuple(node for node in self.nodes if types_component.instance_of(node, [Expression]))

    @ft.cached_property
    @final
    def targets(self) -> Sequence[Target]:
        types_component = self.base_components['Types']
        return tuple(node for node in self.nodes if types_component.instance_of(node, [Target]))

    @ft.cached_property
    @final
    def inners(self) -> Sequence[Node]:
        if self.has_base_component('IO'):
            return self.base_components['IO'].inners
        return []

    def _get_name(self, node_or_name: Union[str, Node]) -> str:
        """Given a node or a node name, returns the node name."""
        return node_or_name.name if isinstance(node_or_name, Node) else node_or_name

    @final 
    def has_base_component(self, component_name: available_graph_components) -> bool:
        return component_name in self.base_components

    @final 
    def has_extra_component(self, component_name: str) -> bool:
        return component_name in self.extra_components

    @final
    def with_base_component(self, new_component: Component) -> Graph:
        copy: Graph
        new_name = cast(available_graph_components, type(new_component).__name__)
        #handle base components
        if len(self.base_components) > 0:
            new_base_components = list()
            new_base_components.append(new_component)
            for name, component in self.base_components.items():
                if name != new_name and component.inheritable:
                    new_base_components.append(component)
            copy = Graph(self.nodes, new_base_components)
        else: 
            copy = Graph(self.nodes, [new_component])
        #handle extra components
        inheritable_extra_components: dict[str, Component] = dict()
        for name, component in self.extra_components.items():
            if component.inheritable:
                inheritable_extra_components[name] = component.with_graph(copy)
        copy.extra_components = inheritable_extra_components
        return copy

    @final
    def with_extra_component(self, new_component: Component, new_name: str) -> Graph:
        copy: Graph
        #handle base components
        if len(self.base_components) > 0:
            new_base_components = list()
            for name, component in self.base_components.items():
                if component.inheritable:
                    new_base_components.append(component)
            copy = Graph(self.nodes, new_base_components)
        else: 
            copy = Graph(self.nodes)
        #handle extra components
        inheritable_extra_components: dict[str, Component] = dict()
        inheritable_extra_components[new_name] = new_component.with_graph(copy)
        for name, component in self.extra_components.items():
            if component.inheritable and name != new_name:
                inheritable_extra_components[name] = component.with_graph(copy)
        copy.extra_components = inheritable_extra_components
        return copy


# class GraphBuilder
# class GraphCopier (maybe, this can be absorbed by GraphBuilder)

# > Typing help

T_Graph = TypeVar('T_Graph', Graph, Graph)
AnyGraph = Union[Graph]
T_AnyGraph = TypeVar('T_AnyGraph', bound=AnyGraph)
