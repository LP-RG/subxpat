from typing import AbstractSet, Any, Final, List, Sequence, Union, final, Literal
from collections.abc import Callable
import networkx as nx
from copy import deepcopy
from abc import ABC, abstractmethod
from .node import AnyNode, Extras, Node, BoolVariable, BoolConstant, PlaceHolder, AnyGlobalObjective, GlobalTask, Constraint
import functools as ft
import itertools as it
import operator as op

__all__ = [
    'Component', 'CustomComponent', 'Subgraph', 'Topology', 'Weight', 'Parameter', 'IO', 'Constraints', 'Types'
]

available_graph_components = Literal['Subgraph', 'Topology', 'Weight', 'Parameter', 'IO', 'Constraints', 'Types']

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

class CustomComponent(Component):
    """User-defined component"""

    graph: Final[Any]
    graph_reference: Final[bool]
   
    def __init__(self,
                 object: Any,
                 action: Callable[..., Any],
                 inheritable: bool = True,
                 keep_graph_reference: bool = False,
                 graph: Any = None) -> None:
        
        super.__init__(deepcopy(object), action, inheritable)
        self.graph = graph
        self.graph_reference = keep_graph_reference

    @final
    def perform_action(self, *optionalArgs) -> Any:
        return self.action(self.object, *optionalArgs)
    
    @final 
    def with_graph(self, graph: Any = None) -> CustomComponent:
        if not self.graph_reference:
            return self
        else:
            return CustomComponent(self.object, self.action, self.inheritable, self.graph_reference, graph)

class Subgraph(Component):
    """Concrete and 'static' component
        - object: mapping from node id to boolean representing whether node is present in the current subgraph
        - action: return list of node ids in the current subgraph 
    """

    graph: Final[Any]

    def __init__(self, subgraph_set: set[str], graph: Any = None) -> None:
        # COMMENT:from-MARCO: perfect, in the future we can also see about optimising a few things
        # COMMENT:from-MARCO: a thing I noticed now, is that, doing the casting/getting/whatever later, may allow the input datastructure to change
        #                     example: i create the component passing in my own set/dict, then after the component has been created, if I (even outside the component) update the datastructure I passed in, now the component will behave on this new data, making it not deeply immutable
        # from-ILIA: fixed
        action = lambda subgraph_set: list(subgraph_set)
        super().__init__(deepcopy(subgraph_set), action)
        self.graph = graph

    @final
    def nodes_names(self) -> list[str]:
        return self.action(self.object)

    @final
    def in_subgraph(self, node_id: str) -> bool:
        return node_id in self.object

    @final 
    def with_graph(self, graph: Any) -> Subgraph:
        return Subgraph(self.object, graph)

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[AnyNode]:
        subgraph_ids = self.nodes_names()
        types_component = self.graph.base_components['Types']
        return tuple(
            node for node in self.graph.nodes
            if types_component.instance_of(node, [Extras]) and node.name in subgraph_ids
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[AnyNode]:
        # COMMENT:from-MARCO: you should reason about what is best to return from these methods, the node object, or the id/name?
        #                     once you reasoned about it we can discuss this in the next meeting

        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        types_component = self.graph.base_components['Types']
        subgraph_ids = self.nodes_names()
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (
                pred for pred in self.graph.predecessors(node)
                if not types_component.instance_of(pred, [Extras]) or not pred.name in subgraph_ids
            )
            for node in self.subgraph_nodes
        )))

    @ft.cached_property
    @final
    def subgraph_outputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        types_component = self.graph.base_components['Types']
        subgraph_ids = self.nodes_names()
        return tuple(sorted(
            (
                node for node in self.subgraph_nodes
                if any(
                    not types_component.instance_of(succ, [Extras]) or not succ.name in subgraph_ids
                    for succ in self.graph.successors(node)
                )
            ),
            key=op.attrgetter('name')
        ))

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        types_component = self.graph.base_components['Types']
        subgraph_ids = self.nodes_names()
        return sum(
            n.name in subgraph_ids for n in self.graph.successors(node_or_name)
            if types_component.instance_of(n, [Extras])
        )

class Topology(Component):
    """Concrete and 'static' component
        - object: DiGraph representing the topology
        - action: return the DiGraph
    """

    def __init__(self, digraph: nx.DiGraph) -> None:
        # COMMENT:from-MARCO: perfect, in the future we can also see about optimising a few things
        action = lambda digraph: digraph
        super().__init__(nx.freeze(digraph), action, inheritable=False)

    @final
    def get(self) -> nx.DiGraph:
        return self.action(self.object)

    @final
    def with_graph(self, graph: object = None) -> Topology:
        return self

class Weight(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its weight
        - action: return the weight corresponding to the given node id
    """

    def __init__(self, map: dict[str, int]) -> None:
        # COMMENT:from-MARCO: a thing I noticed now, is that, doing the casting/getting/whatever later, may allow the input datastructure to change
        #                     example: i create the component passing in my own set/dict, then after the component has been created, if I (even outside the component) update the datastructure I passed in, now the component will behave on this new data, making it not deeply immutable
        # from-ILIA: fixed
        action = lambda map, node_id: map[node_id] if node_id in map else None
        super().__init__(deepcopy(map), action)

    def get(self, node_id: str) -> int | None:
        return self.action(self.object, node_id)

    @final
    def with_graph(self, graph: object = None) -> Weight:
        return self

    @final 
    def has_weight(self, node: Any) -> bool:
        """Returns if the given object is an instance of `Extras` and has an assigned weight."""
        return isinstance(node, Extras) and self.get(node.name) is not None

class Parameter(Component):
    """Concrete and 'static' component
        - object: tuple of parameters names
        - action: return the parameters
    """

    graph: Final[Any]

    def __init__(self, parameters_names: Sequence[str], graph: Any = None) -> None:
        action = lambda params, graph: tuple(graph.base_components['Topology'].get().nodes[name][graph.K] for name in params)
        super().__init__(tuple(parameters_names), action)
        self.graph = graph

    @final 
    def with_graph(self, graph: Any) -> Parameter:
        return Parameter(self.object, graph)

    @ft.cached_property
    @final
    def parameters(self) -> Sequence[Union[BoolVariable, BoolConstant]]:
        return self.action(self.object, self.graph)

    @ft.cached_property
    @final
    def parameters_names(self) -> tuple[str]:
        return deepcopy(self.object)

class IO(Component):
    """Concrete and 'static' component
        - object: list of inputs and outputs
        - action: return the inputs or the outputs according to 'index'
    """

    graph: Final[Any]

    def __init__(self, inputs_names: Sequence[str], outputs_names: Sequence[str], graph: Any = None) -> None:
        action = lambda inputs_outputs_list, index: deepcopy(inputs_outputs_list[index])
        super().__init__([tuple(inputs_names), tuple(outputs_names)], action)
        self.graph = graph

    @final
    def with_graph(self, graph: object = None) -> IO:
        return IO(self.object[0], self.object[1], graph)

    @ft.cached_property
    @final
    def inputs_names(self) -> tuple[str]:
        return self.action(self.object, 0)

    @ft.cached_property
    @final
    def outputs_names(self) -> tuple[str]:
        return self.action(self.object, 1)

    @ft.cached_property
    @final
    def inputs(self) -> Sequence[AnyNode]:
        return tuple(self.graph.base_components['Topology'].get().nodes[name][self.graph.K] for name in self.inputs_names)

    @final
    def input_index_of(self, node_or_name: Union[str, Node]) -> int:
        """Returns the index of the node in the inputs, -1 if the node is not an input."""
        try: return self.inputs_names.index(self.graph._get_name(node_or_name))
        except: return -1

    @ft.cached_property
    @final
    def outputs(self) -> Sequence[AnyNode]:
        return tuple(self.graph.base_components['Topology'].get().nodes[name][self.graph.K] for name in self.outputs_names)

    @final
    def output_index_of(self, node_or_name: Union[str, Node]) -> int:
        """Returns the index of the node in the outputs, -1 if the node is not an output."""
        try: return self.outputs_names.index(self.graph._get_name(node_or_name))
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
        # COMMENT:from-MARCO: a thing I noticed now, is that, doing the casting/getting/whatever later, may allow the input datastructure to change
        #                     example: i create the component passing in my own set/dict, then after the component has been created, if I (even outside the component) update the datastructure I passed in, now the component will behave on this new data, making it not deeply immutable
        # from-ILIA: Does creating a deepcopy of the input and using the copy inside the component solve this problem? Like I did below. If yes, I'll modify the above components this way.
        # from-MARCO: yes, this fixes it
        action = lambda map, node_id: map[node_id]
        super().__init__(deepcopy(map), action, inheritable=False)

    @final
    def get(self, node: AnyNode) -> type:
        return self.action(self.object, node.name)

    @final
    def instance_of(self, node: AnyNode, classes: list[type]) -> bool:
        node_type = self.get(node)
        for class_name in classes:
            if node_type == class_name or issubclass(node_type, class_name):
                return True
        return False

    @final
    def with_graph(self, graph: object = None) -> Types:
        return self