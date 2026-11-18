from typing import Iterable, Literal, Sequence, get_args, Union, Final, final, cast, overload, Self, TypedDict, Unpack, NotRequired
import functools as ft
from abc import ABC

from .components import (
    Subgraph, Weight, Types, Topology, Component, Parameter, IO, Constraints, CustomComponent, Values,
    #
    ComponentsObjectsDict,
    #
    available_graph_components, component_name_to_type, component_empty_object,
)
from .node import (
    AnyVariable, Expression, Node, Operation, Constant, Valued, Target, Variable,
    #
    AnyNode, AnyConstant, AnyExpression, AnyNonEndPoint, AnyNonEntryPoint,
)
from .orderedDiGraph import NodeAttributesDict, OrderedDiGraph
from .error import UndefinedNodeError

__all__ = [
    'Graph',
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
    def __getitem__(self, key: Literal["Weight"]) -> Weight: ...

    @overload
    def __getitem__(self, key: Literal["Min_Weight"]) -> Weight: ...

    @overload
    def __getitem__(self, key: Literal["Max_Weight"]) -> Weight: ...

    @overload
    def __getitem__(self, key: Literal["Parameter"]) -> Parameter: ...

    @overload
    def __getitem__(self, key: Literal["IO"]) -> IO: ...

    @overload
    def __getitem__(self, key: Literal["Constraints"]) -> Constraints: ...

    @overload
    def __getitem__(self, key: Literal["Types"]) -> Types: ...

    @overload
    def __getitem__(self, key: Literal["Values"]) -> Values: ...

    def __getitem__(self, key: available_graph_components) -> Component:
        return super().__getitem__(key)

class Graph:

    base_components: Final[ComponentsDict]
    extra_components: Final[dict[str, CustomComponent]]

    def __init__(self, nodes: Iterable[AnyNode], 
                 components: Sequence[Component], 
                 extra_component: dict[str, CustomComponent] = dict()) -> None:
        """
        Creates a new graph from the given nodes.

        :authors: Marco Biasion, Ilia Zeller
        """

        nodes = list(nodes)
        components = list(components)
        extra_component = extra_component.copy()

        self.base_components = ComponentsDict([
            (cast(available_graph_components, type(c).__name__), c.with_graph(self))
            for c in components
        ])
        self.extra_components = dict([
            (name, c.with_graph(self))
            for name, c in extra_component.items()
        ])

        # graph correctness guard
        defined_node_names = set(
            node.name
            for node in nodes
        )
        node_names_in_edges = set(
            src_name
            for node in nodes
            if self.base_components['Types'].instance_of(node, [Operation])
            for src_name in self.base_components['Topology'].operands(node)
        )
        if len(missing := (node_names_in_edges - defined_node_names)) > 0:
            raise UndefinedNodeError(f'The following nodes are not defined but edges from them exist: {missing}')

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

    @final
    def __getitem__(self, name: str) -> AnyNode:
        return self.base_components['Topology'].get_node(name)

    @final
    def __contains__(self, name: str) -> bool:
        return self.base_components['Topology'].get().has_node(name)

    def __eq__(self, other) -> bool:
        # from-MARCO: this is to be discussed -> TODO: check
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
        return self.base_components['Topology'].get_nodes

    @final
    def predecessors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEndPoint]:
        return self.base_components['Topology'].get_predecessors(node_or_name)

    @final
    def successors(self, node_or_name: Union[str, Node]) -> Sequence[AnyNonEntryPoint]:
        return self.base_components['Topology'].get_successors(node_or_name)

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

    @final 
    def has_base_component(self, component_name: available_graph_components) -> bool:
        return component_name in self.base_components

    @final 
    def has_extra_component(self, component_name: str) -> bool:
        return component_name in self.extra_components

    @final
    def with_base_component(self, new_component: Component) -> Graph:
        graph_copier = GraphCopier(self)
        graph_copier.add_base_component(new_component)
        graph_copier.add_all_nodes()
        return graph_copier.copy()

    @final
    def with_extra_component(self, component_name: str, new_component: CustomComponent) -> Graph:
        graph_copier = GraphCopier(self)
        graph_copier.add_extra_component(component_name, new_component)
        graph_copier.add_all_nodes()
        return graph_copier.copy()

automatic_components = Literal['Subgraph', 'Weight', 'Min_Weight', 'Max_Weight', 'Values']
"""
    automatic_components: Components derived from node attributes (completely automatic)
"""
autofill_components = Literal['Constraints']
"""
    autofill_components: Components explicitly added by the user, but automatically filled
"""
inaddible_components = Union[Topology, Types]
"""
    inaddible_components: Components always internally generated and managed by GraphCreator, can't be added by users
"""

class NodeAttributes(TypedDict):
    in_subgraph: NotRequired[bool]
    weight: NotRequired[int | None]
    max_weight: NotRequired[int | None]
    min_weight: NotRequired[int | None]
    value: NotRequired[int | bool]

class GraphCreator(ABC):

    base_components_objects: ComponentsObjectsDict
    base_components: list[Component]
    extra_components: dict[str, CustomComponent]
    nodes: list[AnyNode]
    current_node: Union[AnyNode, None]

    @property
    def current(self) -> AnyNode | None:
        return self.current_node

    def __check_component_addition(self, component_name: str) -> None:
        if (component_name in self.base_components_objects
            or any(type(c).__name__ == component_name for c in self.base_components)):
            raise RuntimeError(
                f'Base component {component_name} already present in the graph'
            )
        if len(self.nodes) > 0:
            add_first = get_args(automatic_components) + get_args(autofill_components)
            raise RuntimeError(
                f'Illegal action: Base component {component_name} is being added after nodes are added'
                f'These base components are required to be added before the nodes: {', '.join(add_first)}'
            )

    def __add_automatic_component(self, component_name: automatic_components) -> Self:
        """
            Derived from node attributes (completely automatic)
        """
        if any(type(c).__name__ == component_name for c in self.base_components):
            raise RuntimeError(
                f'Base component {component_name} already present in the graph'
            )
        if not component_name in self.base_components_objects: 
            empty_object_type = component_empty_object[component_name]
            self.base_components_objects[component_name] = empty_object_type()
        return self
   
    def add_autofill_component(self, component_name: autofill_components) -> Self:
        """
            Explicitly added by the user and autofilled
        """
        self.__check_component_addition(component_name)
        empty_object_type = component_empty_object[component_name]
        self.base_components_objects[component_name] = empty_object_type()
        return self

    def add_base_component(self, component: Component) -> Self:
        """
            Explicitly added and "manually" generated by the user
        """
        assert(not isinstance(component, CustomComponent))
        assert(not any(isinstance(component, x) for x in get_args(inaddible_components)))
        self.__check_component_addition(type(component).__name__)
        self.base_components.append(component)
        return self

    def add_extra_component(self, component_name: str, component: CustomComponent) -> Self:
        """
            Explicitly added and "manually" generated by the user
        """
        if component_name in self.extra_components:
            raise RuntimeError(
                f'Extra component {component_name} already present in the graph'
            )
        self.extra_components[component_name] = component
        return self

    def add_new_node(self, node_name: str, node_type: type[AnyNode]) -> Self:
        new_node: AnyNode = node_type(node_name)
        self.current_node = new_node
        self.nodes.append(new_node)
        if 'Constraint' in self.base_components_objects:
            self.base_components_objects['Constraints'].append(new_node)
        self.base_components_objects['Topology'].add_node(node_name, name=node_name, node=new_node)
        self.base_components_objects['Types'][node_name] = node_type
        return self

    def add_extras(self, **extras: Unpack[NodeAttributes]) -> Self:
        if self.current is None: raise
        node_name = self.current.name
        if "weight" in extras and extras["weight"] != None:
            self.__add_automatic_component('Weight')
            self.base_components_objects['Weight'][node_name] = extras["weight"]
        if "max_weight" in extras and extras["max_weight"] != None:
            self.__add_automatic_component('Max_Weight')
            self.base_components_objects['Max_Weight'][node_name] = extras["max_weight"]
        if "min_weight" in extras and extras["min_weight"] != None:
            self.__add_automatic_component('Min_Weight')
            self.base_components_objects['Min_Weight'][node_name] = extras["min_weight"]
        if "in_subgraph" in extras and extras["in_subgraph"]:
            self.__add_automatic_component('Subgraph')
            self.base_components_objects['Subgraph'].add(node_name)
        if "value" in extras:
            assert(isinstance(self.current, Valued))
            assert(type(extras['value']) == type(self.current).value_type)
            self.__add_automatic_component('Values')
            self.base_components_objects['Values'][node_name] = extras['value']
        return self

    def add_operands(self, operands: list[str]) -> Self:
        if self.current is None: raise
        assert(isinstance(self.current, Operation))
        required_count = type(self.current).required_operands
        if len(operands) != required_count:
            raise RuntimeError(
                f'Wrong operands count: '
                f'{len(operands)} operands were given (expected {required_count}) '
                f'in {self!r}.'
            )
        dst_name = self.current.name
        self.base_components_objects['Topology'].add_edges_from((src_name, dst_name) for src_name in operands)
        return self
    

class GraphBuilder(GraphCreator):

    def __init__(self) -> None:
        self.base_components_objects = ComponentsObjectsDict()
        self.base_components_objects['Topology'] = OrderedDiGraph()
        self.base_components_objects['Types'] = dict()
        self.base_components = list()
        self.extra_components = dict()
        self.nodes = list()
        self.current_node = None

    def add_node_from(self, node: AnyNode, predecessor_graph: Graph) -> None:
        gb = self.add_new_node(node.name, predecessor_graph.base_components["Types"].get(node))
        extras = {}
        if predecessor_graph.has_base_component('Subgraph') and predecessor_graph.base_components["Subgraph"].in_subgraph(node.name):
            extras['in_subgraph': True]
        if predecessor_graph.has_base_component('Weight') and predecessor_graph.base_components['Weight'].has_weight(node):
            extras['weight': predecessor_graph.base_components['Weight'].get(node.name)]
        if predecessor_graph.has_base_component('Max_Weight') and predecessor_graph.base_components['Max_Weight'].has_weight(node):
            extras['max_weight': predecessor_graph.base_components['Max_Weight'].get(node.name)]
        if predecessor_graph.has_base_component('Min_Weight') and predecessor_graph.base_components['Min_Weight'].has_weight(node):
            extras['min_weight': predecessor_graph.base_components['Min_Weight'].get(node.name)]
        if predecessor_graph.has_base_component('Values') and predecessor_graph.base_components['Values'].has_value(node):
            extras['value': predecessor_graph.base_components['Values'].get(node)]
        gb.add_extras(**extras)
        if predecessor_graph.base_components["Types"].instance_of(node, [Operation]):
            gb.add_operands(list(predecessor_graph.base_components['Topology'].operands(node)))

    def add_all_nodes_from(self, predecessor_graph: Graph) -> None:
        for node in predecessor_graph.nodes:
            self.add_node_from(node, predecessor_graph)

    def create(self) -> Graph:

        components: list[Component] = list()
        components.extend(self.base_components)
        for comp_name, comp_obj in self.base_components_objects.items():
            components.append(component_name_to_type(comp_name)(comp_obj))

        # Add default Subgraph and Weight components if they're not passed as argument 
        #(this because the Node structure had default weight = None and in_subgraph = False)
        if not any(type(c).__name__ == 'Subgraph' for c in components):
            components.append(Subgraph(set()))
        if not any(type(c).__name__ == 'Weight' for c in components):
            components.append(Weight(dict()))
        
        return Graph(self.nodes, components, self.extra_components)


class GraphCopier(GraphCreator):

    graph_to_copy: Final[Graph]

    def __init__(self, graph_to_copy: Graph) -> None:
        self.base_components_objects = ComponentsObjectsDict()
        self.base_components_objects['Topology'] = OrderedDiGraph()
        self.base_components_objects['Types'] = dict()
        self.base_components = list()
        self.extra_components = dict()
        self.nodes = list()
        self.current_node = None
        self.graph_to_copy = graph_to_copy

    def add_node(self, node: AnyNode, **extras: Unpack[NodeAttributes]) -> None:
        gc = self.add_new_node(node.name, self.graph_to_copy.base_components["Types"].get(node))
        new_extras = {}
        if "in_subgraph" in extras and extras["in_subgraph"]:
            new_extras['in_subgraph': True]
        elif self.graph_to_copy.has_base_component('Subgraph') and self.graph_to_copy.base_components["Subgraph"].in_subgraph(node.name):
            new_extras['in_subgraph': True]
        if "weight" in extras and extras["weight"] != None:
            new_extras['weight': extras["weight"]] 
        elif self.graph_to_copy.has_base_component('Weight') and self.graph_to_copy.base_components['Weight'].has_weight(node):
            new_extras['weight': self.graph_to_copy.base_components['Weight'].get(node.name)]
        if "max_weight" in extras and extras["max_weight"] != None:
            new_extras['max_weight': extras["max_weight"]] 
        elif self.graph_to_copy.has_base_component('Max_Weight') and self.graph_to_copy.base_components['Max_Weight'].has_weight(node):
            new_extras['max_weight': self.graph_to_copy.base_components['Max_Weight'].get(node.name)]
        if "min_weight" in extras and extras["min_weight"] != None:
            new_extras['min_weight': extras["min_weight"]] 
        elif self.graph_to_copy.has_base_component('Min_Weight') and self.graph_to_copy.base_components['Min_Weight'].has_weight(node):
            new_extras['min_weight': self.graph_to_copy.base_components['Min_Weight'].get(node.name)]
        if "value" in extras:
            new_extras['value': extras["value"]] 
        elif self.graph_to_copy.has_base_component('Values') and self.graph_to_copy.base_components['Values'].has_value(node):
            new_extras['value': self.graph_to_copy.base_components['Values'].get(node)]
        gc.add_extras(**new_extras)
        if self.graph_to_copy.base_components["Types"].instance_of(node, [Operation]):
            gc.add_operands(list(self.graph_to_copy.base_components['Topology'].operands(node)))

    def add_all_nodes(self, **extras: Unpack[NodeAttributes]) -> None:
        for node in self.graph_to_copy.nodes:
            self.add_node(node, **extras)

    def copy(self) -> Graph:

        components: list[Component] = list()
        components.extend(self.base_components)
        for comp_name, comp_obj in self.base_components_objects.items():
            components.append(component_name_to_type(comp_name)(comp_obj))

        components_types = [type(c).__name__ for c in components]
        for name, component in self.graph_to_copy.base_components.items():
            if (not name in components_types) and component.inheritable:
                components.append(component)

        # Add default Subgraph and Weight components if they're not passed as argument 
        #(this because the Node structure had default weight = None and in_subgraph = False)
        if not any(type(c).__name__ == 'Subgraph' for c in components):
            components.append(Subgraph(set()))
        if not any(type(c).__name__ == 'Weight' for c in components):
            components.append(Weight(dict()))

        inheritable_extra_components: dict[str, CustomComponent] = dict()
        inheritable_extra_components.update(self.extra_components)
        extra_components_types = [type(c).__name__ for c in self.extra_components]
        for name, component in self.graph_to_copy.extra_components.items(): 
            if (not name in extra_components_types) and component.inheritable:
                inheritable_extra_components[name] = component

        return Graph(self.nodes, components, inheritable_extra_components)