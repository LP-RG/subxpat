from typing import List, Sequence, TypedDict, Unpack, NotRequired
from .graph import Graph
from .components import Component, Weight, Subgraph, Constraints
from .node import AnyNode

class NodeAttributes(TypedDict):
    in_subgraph: NotRequired[bool] 
    weight: NotRequired[int | None]

class GraphCopier:

    graph_to_copy: Graph
    nodes: List[AnyNode]
    subgraph_set: set[str]
    weights_map: dict[str, int]

    def __init__(self, graph_to_copy: Graph) -> None:
        self.graph_to_copy = graph_to_copy
        self.nodes = list()
        self.subgraph_set = set()
        self.weights_map = dict()

    # either the below version of add_node, or a version where the various separate elements for the node
    # creation (type, name, ...) are passed as argument and the node is generated inside add_node
    def add_node(self, node: AnyNode, **extras: Unpack[NodeAttributes]) -> None:
        self.nodes.append(node)
        for n in self.graph_to_copy.nodes:
            if n is node:
                if self.graph_to_copy.has_base_component('Subgraph') and self.graph_to_copy.base_components["Subgraph"].in_subgraph(node.name):
                    self.subgraph_set.add(node.name)
                if self.graph_to_copy.has_base_component('Weight') and self.graph_to_copy.base_components["Weight"].has_weight(node):
                    self.weights_map[node.name] = self.graph_to_copy.base_components['Weight'].get(node.name)
                return
        if "weight" in extras and extras["weight"] != None:
            self.weights_map[node.name] = extras["weight"]
        if "in_subgraph" in extras and extras["in_subgraph"]:
            self.subgraph_set.add(node.name)

    def add_nodes(self, nodes: Sequence[AnyNode], **extras: Unpack[NodeAttributes]) -> None:
        for node in nodes:
            self.add_node(node, **extras)

    def copy(self, extra_components: List[Component] = list()) -> Graph:
        components = extra_components
        if len(self.subgraph_set) > 0:
            subgraph_component = Subgraph(self.subgraph_set)
            components.append(subgraph_component)
        if len(self.weights_map) > 0:
            weights_component = Weight(self.weights_map)
            components.append(weights_component)
        if self.graph_to_copy.has_base_component('Constraints'):
            constraints_component = Constraints(self.nodes)
            components.append(constraints_component)
        return self.graph_to_copy.copy(self.nodes, components)
        
class GraphBuilder:

    nodes: List[AnyNode] 
    subgraph_set: set[str] 
    weights_map: dict[str, int] 

    def __init__(self) -> None:
        self.nodes = list()
        self.subgraph_set = set()
        self.weights_map = dict()

    def add_new_node(self, node: AnyNode, **extras: Unpack[NodeAttributes]) -> None:
        self.nodes.append(node)
        if "weight" in extras and extras["weight"] != None:
            self.weights_map[node.name] = extras["weight"]
        if "in_subgraph" in extras and extras["in_subgraph"]:
            self.subgraph_set.add(node.name)

    def add_new_nodes(self, nodes: Sequence[AnyNode], **extras: Unpack[NodeAttributes]) -> None:
        for node in nodes:
            self.add_new_node(node, **extras)

    def add_inherited_node(self, node: AnyNode, predecessor_graph: Graph) -> None:
        self.nodes.append(node)
        if predecessor_graph.has_base_component('Subgraph') and predecessor_graph.base_components["Subgraph"].in_subgraph(node.name):
            self.subgraph_set.add(node.name)
        if predecessor_graph.has_base_component('Weight') and predecessor_graph.base_components['Weight'].has_weight(node):
            self.weights_map[node.name] = predecessor_graph.base_components['Weight'].get(node.name)

    def add_inherited_nodes(self, nodes: Sequence[AnyNode], predecessor_graph: Graph) -> None:
        for node in nodes:
            self.add_inherited_node(node, predecessor_graph)

    def create(self, 
               extra_components: List[Component] = list(),
               with_constraints_component: bool = False) -> Graph:
        components = extra_components
        if len(self.subgraph_set) > 0:
            subgraph_component = Subgraph(self.subgraph_set)
            components.append(subgraph_component)
        if len(self.weights_map) > 0:
            weights_component = Weight(self.weights_map)
            components.append(weights_component)
        if with_constraints_component:
            constraints_component = Constraints(self.nodes)
            components.append(constraints_component)
        return Graph(self.nodes, components)
        