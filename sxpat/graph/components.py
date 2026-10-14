from typing import Any, Final, Sequence, Union, final, overload
from collections.abc import Callable
import networkx as nx
from copy import deepcopy
from abc import ABC, abstractmethod
from .node import AnyNode, Extras, Node, T_Node
import functools as ft
import itertools as it
import operator as op

__all__ = [
    'Subgraph', 'Topology', 'Weight', 'Type', 'Component',
]


# COMMENT:from-MARCO: all this looks good.
# i think you can simplify a few things, specifically:
# - given that different components may behave vary different behaviours, you can keep each one in its own unique hierarchy, meaning that, if you want to inherit from Component, Component can be only a very coincise interface, maybe specifying the requirements all components should follow (like as immutability and such).
# - given the above, the .perform_action could be removed, and instead of passing thorugh self.action, each component directly defines its methods (e.g. .nodes_names, .get, ...).
# these could simplify the effort required for a new developer to understand the component

# COMMENT:from-MARCO: (this can be left for later)
# if you want to simplify further your structure (as it will get there eventually anyway) you can use integers as "ids" for nodes, instead than strings.
# NOTE THAT if you do this many other things will break, so you would require a middle-step on the accesses of the graphs to map from an outside string to an inside integer, and viceversa

class Component(ABC):
    """Component interface"""
    object: Final[Any]
    action: Final[Callable[..., Any]]
    inheritable: Final[bool]

    # COMMENT:from-MARCO: i think the auto-inherit-on-copy is a very good idea
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
        
        super.__init__(object, action, inheritable)
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

    def __init__(self, map: dict[str, bool], graph: Any = None) -> None:
        action = lambda map: [k for k in map.keys() if map[k] == 1]
        super().__init__(map, action)
        self.graph = graph

    @final
    def nodes_names(self) -> list[str]:
        return self.action(self.object)

    @final 
    def with_graph(self, graph: Any) -> Subgraph:
        return Subgraph(self.object, graph)

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[AnyNode]:
        subgraph_ids = self.nodes_names()
        return tuple(
            node for node in self.graph.nodes
            if isinstance(node, Extras) and node.name in subgraph_ids
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[AnyNode]:
        # a node is a subgraph input if it is not in the subgraph and at least one successor is in the subgraph
        subgraph_ids = self.nodes_names()
        return tuple(dict.fromkeys(it.chain.from_iterable(
            (
                pred for pred in self.graph.predecessors(node)
                if not isinstance(pred, Extras) or not pred.name in subgraph_ids
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
                    not isinstance(succ, Extras) or not succ.name in subgraph_ids
                    for succ in self.graph.successors(node)
                )
            ),
            key=op.attrgetter('name')
        ))

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        subgraph_ids = self.nodes_names()
        return sum(
            n.name in subgraph_ids for n in self.graph.successors(node_or_name)
            if isinstance(n, Extras)
        )

class Topology(Component):
    """Concrete and 'static' component
        - object: DiGraph representing the topology
        - action: return the DiGraph
    """

    def __init__(self, digraph: nx.DiGraph) -> None:
        action = lambda digraph: deepcopy(digraph)
        super().__init__(digraph, action)

    @final
    def get(self) -> nx.DiGraph:
        # COMMENT:from-MARCO: values produced by components should not allow to change the graph 
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
        action = lambda map, node_id: map[node_id]
        super().__init__(map, action)

    def get(self, node_id: str) -> int | None:
        return self.action(self.object, node_id)

    @final
    def with_graph(self, graph: object = None) -> Weight:
        return self

    @final 
    def has_weight(self, obj: Any) -> bool:
        """Returns if the given object is an instance of `Extras` and has an assigned weight."""
        return isinstance(obj, Extras) and self.get(obj.name) is not None

class Type(Component):
    """Concrete and 'static' component
        - object: mapping from node id to its type
        - action: return the type corresponding to the given node id
    """

    # COMMENT:from-MARCO: types here should be specific Node types (Sum, And, ...)
    def __init__(self, map: dict[str, T_Node]) -> None:
        action = lambda map, node_id: map[node_id]
        super().__init__(map, action)

    @final
    def get(self, node_id: str) -> T_Node:
        return self.action(self.object, node_id)

    @final
    def with_graph(self, graph: object = None) -> Type:
        return self
