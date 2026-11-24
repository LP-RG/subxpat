from typing import AbstractSet, Any, Final, List, Sequence, Union, final, Literal, overload
from collections.abc import Callable
import networkx as nx
from copy import deepcopy
from abc import ABC, abstractmethod
from .node import (
    AnyNonEndPoint, AnyNonEntryPoint,
    # 
    AnyNode, If, Limited1Operation, Limited2Operation, Multiplexer, Node, BoolVariable, BoolConstant, PlaceHolder, 
    AnyGlobalObjective, GlobalTask, Constraint, Operation, Valued
)
import functools as ft
import itertools as it
import operator as op
from .orderedDiGraph import OrderedDiGraph

__all__ = [
    'Component', 'CustomComponent', 'Subgraph', 'Topology', 'Weight', 'Parameter', 'IO', 'Constraints', 'Types', 'Values'
]

available_graph_components = Literal['Subgraph', 'Topology', 'Weight', 'Min_Weight', 'Max_Weight', 'Parameter', 'IO', 'Constraints', 'Types', 'Values']

# COMMENT:from-MARCO: (this can be left for later)
# if you want to simplify further your structure (as it will get there eventually anyway) you can use integers as "ids" for nodes, instead than strings.
# NOTE THAT if you do this many other things will break, so you would require a middle-step on the accesses of the graphs to map from an outside string to an inside integer, and viceversa
# from-ILIA: left for later! still TODO


class Component(ABC):
    """Component interface"""
    object: Final[Any]
    action: Final[Callable[..., Any]]
    inheritable: Final[bool]

    def __init__(self,
                 object: Any,
                 action: Callable[..., Any],
                 inheritable: bool = True) -> None:
        """The component stores an object (could also be a list of objects) onto which an action is applied 
           when the component is accessed/used. A component can be inheritable, meaning that a graph resulting
           from a copy of a graph having a the component will automatically inherit it, instead an uninheritable 
           component will not be passed to the graph's copies.
        """
        self.object = object
        self.action = action
        self.inheritable = inheritable

    @abstractmethod
    def with_graph(self, graph: Any) -> Component:
        pass

    @abstractmethod
    def synch_nodes(self, nodes: list[AnyNode]) -> Component:
        pass


class CustomComponent(Component):
    """User-defined component"""

    graph: Final[Any]
    graph_reference: Final[bool]
    nodes_synch_action: Callable[[list[AnyNode], Any], Any]

    def __init__(self,
                 object: Any,
                 action: Callable[..., Any],
                 nodes_synch_action: Callable[[list[AnyNode], Any], CustomComponent],
                 inheritable: bool = True,
                 keep_graph_reference: bool = False,
                 graph: Any = None,
                 ) -> None:

        super.__init__(deepcopy(object), action, inheritable)
        self.graph = graph
        self.graph_reference = keep_graph_reference
        self.nodes_synch_action = nodes_synch_action

    @final
    def perform_action(self, *optionalArgs) -> Any:
        return self.action(self.object, *optionalArgs)

    @final
    def with_graph(self, graph: Any = None) -> CustomComponent:
        if not self.graph_reference:
            return self
        else:
            return CustomComponent(self.object, 
                                   self.action, 
                                   self.nodes_synch_action,
                                   self.inheritable, 
                                   self.graph_reference, 
                                   graph)

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> CustomComponent:
        new_object = self.nodes_synch_action(nodes, self.object)
        return CustomComponent(new_object, 
                               self.action, 
                                self.nodes_synch_action,
                                self.inheritable, 
                                self.graph_reference, 
                                self.graph)


class Subgraph(Component):
    """Concrete and 'static' component
        - object: mapping from node id to boolean representing whether node is present in the current subgraph
        - action: return list of node ids in the current subgraph 
    """

    graph: Final[Any]

    def __init__(self, subgraph_set: set[str], graph: Any = None) -> None:
        action = lambda subgraph_set: list(subgraph_set)
        super().__init__(deepcopy(subgraph_set), action)
        self.graph = graph

    @final
    def nodes_names(self) -> list[str]:
        return self.action(self.object)

    @final
    def in_subgraph(self, node_or_name: Union[Node, str]) -> bool:
        return get_name(node_or_name) in self.object

    @final
    def with_graph(self, graph: Any) -> Subgraph:
        return Subgraph(self.object, graph)

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Subgraph:
        new_subgraph_set: set[str] = set([
            name
            for name in self.object
            if any(name == n.name for n in nodes)
        ])
        return Subgraph(new_subgraph_set)

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[AnyNode]:
        subgraph_ids = self.nodes_names()
        return tuple(
            node for node in self.graph.nodes
            if node.name in subgraph_ids
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        subgraph_ids = self.nodes_names()
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (
                pred for pred in self.graph.predecessors(node)
                if not pred.name in subgraph_ids
            )
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    @final
    def subgraph_outputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        subgraph_ids = self.nodes_names()
        return tuple(sorted(
            (
                node for node in self.subgraph_nodes
                if any(
                    not succ.name in subgraph_ids
                    for succ in self.graph.successors(node)
                )
            ),
            key=op.attrgetter('name')
        ))

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[Node, str]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        subgraph_ids = self.nodes_names()
        return sum(
            n.name in subgraph_ids for n in self.graph.successors(node_or_name)
        )

class Topology(Component, OrderedDiGraph):
    """Concrete and 'static' component
        - object: DiGraph representing the topology
        - action: return the DiGraph
    """

    graph: Final[Any]

    def __init__(self, digraph: OrderedDiGraph, graph: Any = None) -> None:
        action = lambda digraph: digraph
        super().__init__(nx.freeze(deepcopy(digraph)), action, inheritable=False)
        self.graph = graph

    @final
    def get(self) -> OrderedDiGraph:
        return self.action(self.object)

    @final
    def with_graph(self, graph: object = None) -> Topology:
        return Topology(self.get(), graph)

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Topology:
        return self

    @final 
    def operands(self, node_or_name: Union[Node, str]) -> list[str]:
        node_name = get_name(node_or_name)
        assert(self.graph.base_components['Types'].instance_of(node_name, [Operation]))
        return list(name for name in self.get().predecessors(node_name))

    @property
    @final
    def get_nodes(self) -> Sequence[AnyNode]:
        """Sequence of nodes in the unique lexicographical topological order."""
        return tuple(self.get_node(name) for name in nx.lexicographical_topological_sort(self.get()))

    @final
    def get_node(self, node_name: str) -> AnyNode:
        return self.get().nodes(data='node')[node_name]

    @final
    def get_predecessors(self, node_or_name: Union[Node, str]) -> Sequence[AnyNonEndPoint]:
        node_name = get_name(node_or_name)
        node = self.get_node(node_name)
        # we iterate over the .predecessors instead of the .operands, so even if `node` is not an Operation it still works
        return tuple(sorted(
            (self.get_node(_name) for _name in self.get().predecessors(node_name)),
            key=lambda _n: list(n for n in self.get().predecessors(node.name)).index(_n.name)
        ))

    @final
    def get_successors(self, node_or_name: Union[Node, str]) -> Sequence[AnyNonEntryPoint]:
        return tuple(
            self.get_node(name)
            for name in self.get().successors(get_name(node_or_name))
        )

    @final
    def operand(self, node: Limited1Operation) -> str:
        return self.operands(node.name)[0]

    @final
    def left(self, node: Limited2Operation) -> str:
        return self.operands(node.name)[0]

    @final
    def right(self, node: Limited2Operation) -> str:
        return self.operands(node.name)[1]

    @final
    def origin(self, node: Multiplexer) -> str:
        return self.operands(node.name)[0]

    @final
    def parameter_usage(self, node: Multiplexer) -> str:
        """If this parameter is true, the origin will be used, otherwise a constant will be produced"""
        return self.operands(node.name)[1]

    @final
    def parameter_assertion(self, node: Multiplexer) -> str:
        """If this parameter is true, the node will produce the origin or the constant true, otherwise will produce the negated origin or the constant false"""
        return self.operands(node.name)[2]

    @final
    def condition(self, node: If) -> str:
        return self.operands(node.name)[0]

    @final
    def if_true(self, node: If) -> str:
        return self.operands(node.name)[1]

    @final
    def if_false(self, node: If) -> str:
        return self.operands(node.name)[2]
    

class Weight(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its weight
        - action: return the weight corresponding to the given node id
    """

    def __init__(self, map: dict[str, int]) -> None:
        action = lambda map, node_id: map[node_id] if node_id in map else None
        super().__init__(deepcopy(map), action)

    def get(self, node_or_name: Union[Node, str]) -> int | None:
        return self.action(self.object, get_name(node_or_name))

    @final
    def with_graph(self, graph: object = None) -> Weight:
        return self

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Weight:
        new_map: dict[str, int] = dict(
            (name, weight)
            for (name, weight) in self.object.items()
            if any(name == n.name for n in nodes)
        )
        return Weight(new_map)

    @final
    def has_weight(self, node_or_name: Union[Node, str]) -> bool:
        """Returns if the given object has an assigned weight."""
        return self.get(get_name(node_or_name)) is not None


class Parameter(Component):
    """Concrete and 'static' component
        - object: tuple of parameters names
        - action: return the parameters
    """

    graph: Final[Any]

    def __init__(self, parameters_names: Sequence[str], graph: Any = None) -> None:
        action = lambda params, graph: tuple(graph.base_components['Topology'].get_node(name) for name in params)
        super().__init__(tuple(parameters_names), action)
        self.graph = graph

    @final
    def with_graph(self, graph: Any) -> Parameter:
        return Parameter(self.object, graph)

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Parameter:
        new_parameters_names: list[str] = [
            name
            for name in self.object
            if any(name == n.name for n in nodes)
        ]
        return Parameter(new_parameters_names)

    @ft.cached_property
    @final
    def parameters(self) -> Sequence[Union[BoolVariable, BoolConstant]]:
        return self.action(self.object, self.graph)

    @ft.cached_property
    @final
    def parameters_names(self) -> tuple[str]:
        return deepcopy(self.object)

IO_keys = Literal['inputs_names', 'outputs_names']

class IO(Component):
    """Concrete and 'static' component
        - object: dictionary mapping literals 'inputs_names' and 'outputs_names' to the list of inputs and outputs respectively
        - action: return the list of inputs or the list of outputs
    """

    graph: Final[Any]

    def __init__(self, IO_names: dict[IO_keys, Sequence[str]], graph: Any = None) -> None:
        action = lambda IO_dict, index: tuple(IO_dict[index])
        super().__init__(deepcopy(IO_names), action)
        self.graph = graph

    @final
    def with_graph(self, graph: object = None) -> IO:
        return IO(self.object, graph)

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> IO:
        new_IO_names: dict[IO_keys, Sequence[str]] = {
            'inputs_names': [
                name
                for name in self.inputs_names
                if any(name == n.name for n in nodes)
            ],
            'outputs_names': [
                name
                for name in self.outputs_names
                if any(name == n.name for n in nodes)
            ]
        }
        return IO(new_IO_names)

    @ft.cached_property
    @final
    def inputs_names(self) -> tuple[str]:
        return self.action(self.object, 'inputs_names')

    @ft.cached_property
    @final
    def outputs_names(self) -> tuple[str]:
        return self.action(self.object, 'outputs_names')

    @ft.cached_property
    @final
    def inputs(self) -> Sequence[AnyNode]:
        return tuple(self.graph.base_components['Topology'].get_node(name) for name in self.inputs_names)

    @final
    def input_index_of(self, node_or_name: Union[Node, str]) -> int:
        """Returns the index of the node in the inputs, -1 if the node is not an input."""
        try: return self.inputs_names.index(get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def outputs(self) -> Sequence[AnyNode]:
        return tuple(self.graph.base_components['Topology'].get_node(name) for name in self.outputs_names)

    @final
    def output_index_of(self, node_or_name: Union[Node, str]) -> int:
        """Returns the index of the node in the outputs, -1 if the node is not an output."""
        try: return self.outputs_names.index(get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def inners(self) -> Sequence[Node]:
        in_out_set = frozenset((*self.inputs_names, *self.outputs_names))
        return tuple(n for n in self.graph.nodes if n.name not in in_out_set)


class Constraints(Component):
    """Concrete and 'static' component
        - object: list of nodes, grouped into 'PlaceHolder', 'Constraint' and 'GlobalTask' types
        - action: return the nodes corresponding to the given group
    """

    def __init__(self, nodes: Sequence[AnyNode]) -> None:
        placeholders: List[PlaceHolder] = list()
        constraints: List[Constraint] = list()
        globaltasks: List[GlobalTask] = list()
        for node in nodes:
            if isinstance(node, PlaceHolder):
                placeholders.append(deepcopy(node))
            if isinstance(node, Constraint):
                constraints.append(deepcopy(node))
            if isinstance(node, GlobalTask):
                globaltasks.append(deepcopy(node))
        action = lambda index, nodes_list: deepcopy(nodes_list[index])
        super().__init__([placeholders, constraints, globaltasks], action, inheritable=False)

    @final
    def with_graph(self, graph: object = None) -> Constraints:
        return self

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Constraints:
        return self

    @ft.cached_property
    @final
    def placeholders(self) -> AbstractSet[PlaceHolder]:
        """The sequence of all `PlaceHolder` nodes in the graph."""
        return dict.fromkeys(self.action(0, self.object)).keys()

    @ft.cached_property
    @final
    def constraints(self) -> Sequence[Constraint]:
        """The sequence of all `Constraint` nodes in the graph."""
        return tuple(self.action(1, self.object))

    @ft.cached_property
    @final
    def global_tasks(self) -> AbstractSet[AnyGlobalObjective]:
        """The set of all `GlobalTask` nodes in the graph."""
        return dict.fromkeys(self.action(2, self.object)).keys()


class Types(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its type
        - action: return the type corresponding to the given node id
    """

    def __init__(self, map: dict[str, type]) -> None:
        action = lambda map, node_id: map[node_id]
        super().__init__(deepcopy(map), action, inheritable=False)

    @final
    def with_graph(self, graph: object = None) -> Types:
        return self

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Types:
        return self

    @final
    def get(self, node_or_name: Union[Node, str]) -> type:
        return self.action(self.object, get_name(node_or_name))

    @final
    def instance_of(self, node_or_name: Union[Node, str], classes: list[type]) -> bool:
        node_type = self.get(node_or_name)
        for class_name in classes:
            if node_type == class_name or issubclass(node_type, class_name):
                return True
        return False

class Values(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its value
        - action: return the value corresponding to the given node id
    """

    def __init__(self, map: dict[str, int | bool]) -> None:
        action = lambda map, node_id: map[node_id]
        super().__init__(deepcopy(map), action)

    @final
    def with_graph(self, graph: object = None) -> Values:
        return self

    @final
    def synch_nodes(self, nodes: list[AnyNode]) -> Values:
        new_map: dict[str, int | bool] = dict(
            (name, value)
            for (name, value) in self.object.items()
            if any(name == n.name for n in nodes)
        )
        return Values(new_map)

    @final
    def get(self, node_or_name: Union[Node, str]) -> int | bool:
        return self.action(self.object, get_name(node_or_name))

    @final
    def has_value(self, node: AnyNode) -> bool:
        return isinstance(node, Valued)


# Helper methods

def get_name(node_or_name: Union[str, Node]) -> str:
    """Given a node or a node name, returns the node name."""
    return node_or_name.name if isinstance(node_or_name, Node) else node_or_name


# Structures describing components features/attributes

component_name_to_type: dict[available_graph_components, type[Component]] = {
    'Subgraph': Subgraph,
    'Topology': Topology,
    'Weight': Weight, 
    'Min_Weight': Weight, 
    'Max_Weight': Weight, 
    'Parameter': Parameter, 
    'IO': IO, 
    'Constraints': Constraints, 
    'Types': Types,
    'Values': Values,
}

component_empty_object: dict[available_graph_components, type] = {
    'Subgraph': set[str],
    'Topology': OrderedDiGraph,
    'Weight': dict[str, int], 
    'Min_Weight': dict[str, int], 
    'Max_Weight': dict[str, int], 
    'Parameter': list[str], 
    'IO': dict[IO_keys, list], 
    'Constraints': list[AnyNode], 
    'Types': dict[str, type],
    'Values': dict[str, int | bool],
}

class ComponentsObjectsDict(dict[available_graph_components, Any]):
    @overload
    def __getitem__(self, key: Literal["Subgraph"]) -> set[str]: ...
    
    @overload
    def __getitem__(self, key: Literal["Topology"]) -> OrderedDiGraph: ...
    
    @overload
    def __getitem__(self, key: Literal["Weight"]) -> dict[str, int]: ...

    @overload
    def __getitem__(self, key: Literal["Min_Weight"]) -> dict[str, int]: ...

    @overload
    def __getitem__(self, key: Literal["Max_Weight"]) -> dict[str, int]: ...

    @overload
    def __getitem__(self, key: Literal["Parameter"]) -> list[str]: ...

    @overload
    def __getitem__(self, key: Literal["IO"]) ->  dict[IO_keys, list]: ...

    @overload
    def __getitem__(self, key: Literal["Constraints"]) -> list[AnyNode]: ...

    @overload
    def __getitem__(self, key: Literal["Types"]) -> dict[str, type]: ...

    @overload
    def __getitem__(self, key: Literal["Values"]) ->  dict[str, int | bool]: ...

    def __getitem__(self, key: available_graph_components) -> Any:
        return super().__getitem__(key)