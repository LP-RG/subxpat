import networkx as nx
from typing import List, Self, Sequence, TypedDict, Unpack, NotRequired

from sxpat.graph.ds import AttributeMonoDict
from .graph import Graph
from .components import Component, Weight, Subgraph, Constraints
from .node import AnyNode


class NodeAttributes(TypedDict):
    in_subgraph: NotRequired[bool]
    weight: NotRequired[int | None]
    max_weight: NotRequired[int | None]


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

    type Id = str

    def __init__(self) -> None:
        self.nodes = list()
        self._topology = nx.DiGraph()  # OrderedDiGraph
        self._types = dict()
        self.subgraph_set = set()
        self.weights_map = dict()
        self._last_node = None

        self._components = dict()

    def m_prepare_component(self, comp_id: str, comp_type: type[Component]) -> Self:
        self._components[comp_id] = comp_type
        return self

    def m_add_component(self, comp_id: str, component: Component) -> Self:
        return self

    def m_add_node(self, id: Id, type: AnyNode) -> Self:
        self._last_node = id
        self._topology.add_node((id, AttributeMonoDict(id)))
        self._types[id] = type
        return self

    def m_add_operands(self, *operands: Id) -> Self:
        if self._last_node is None: raise
        self._topology.add_edges_from((op, self._last_node) for op in operands)
        return self

    def m_add_node_extra(self, **extras: Unpack[NodeAttributes]) -> Self:
        if self._last_node is None: raise
        if "weight" in extras and extras["weight"] != None:
            self.weights_map[self._last_node] = extras["weight"]
        if "in_subgraph" in extras and extras["in_subgraph"]:
            self.subgraph_set.add(self._last_node)
        return self

    @property
    def last(self) -> Id: return self._last_node

    # builder \
    #     .m_add_component('max_weight', Weight) \
    #     .m_add_component('min_weight', Weight)

    # node_id = builder \
    #     .m_add_node('summy', Sum()) \
    #     .m_add_operands('a', 'b') \
    #     .m_add_extras(max_weight=3, in_subgraph=True) \
    #     .last
    # node2_id = builder.m_add_node('proddy', Div()).m_add_operands('a', 'b').last

    def add_new_node(self, node: AnyNode, **extras: Unpack[NodeAttributes]) -> None:
        self.nodes.append(node)
        if "weight" in extras and extras["weight"] != None:
            self.weights_map[self._last_node] = extras["weight"]
        if "in_subgraph" in extras and extras["in_subgraph"]:
            self.subgraph_set.add(node.name)

    def add_new_nodes(self, nodes: Sequence[AnyNode], **extras: Unpack[NodeAttributes]) -> None:
        """DEPRECATED"""
        for node in nodes:
            self.add_new_node(node, **extras)

    def m_add_node_from(self, node: Id, other_graph: Graph) -> Self:
        return self \
            .m_add_node(node, other_graph.types.get(node)) \
            .m_add_operands(other_graph.topology.predecessors(node)) \
            .m_add_node_extra(...)
    
    def m_add_nodes_from(self, nodes: Iterable[Id], other_graph): ...
    def m_add_all_nodes_from(self, other_graph): ...

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
