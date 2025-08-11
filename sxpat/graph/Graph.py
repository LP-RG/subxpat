from __future__ import annotations
from typing_extensions import Self
from typing import AbstractSet, Any, Iterable, Mapping, Optional, Sequence, TypeVar, Union, Final, final
from types import MappingProxyType
from collections import deque
import networkx as nx
import functools as ft
import itertools as it

from .Node import (
    Expression, Extras, Node, Operation, Constant, GlobalTask,
    #
    BoolVariable, PlaceHolder,
    Target, Constraint,
    #
    OperationNode, ConstantNode, GlobalTaskNode, ExpressionNode, Variable, VariableNode,
)
from .error import UndefinedNodeError


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

    def copy(self, nodes: Optional[Iterable[Node]] = None, **extras) -> Self:
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

    def __eq__(self, other) -> bool:
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
    def variables(self) -> Sequence[VariableNode]:
        return tuple(node for node in self.nodes if isinstance(node, Variable))

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

    EXTRAS: Sequence[str] = ('inputs_names', 'outputs_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Sequence[str], outputs_names: Sequence[str]
                 ) -> None:
        # construct base
        super().__init__(nodes)

        # freeze local instances
        self.inputs_names = tuple(inputs_names)
        self.outputs_names = tuple(outputs_names)

    def __eq__(self, other) -> bool:
        """
        Checks equality with another IOGraph.
        Args:
            other: Another IOGraph object.
        Returns:
            True if the graphs are equal and have the same inputs and outputs.
        """
        return (
            super().__eq__(other)
            and self.inputs_names == other.inputs_names
            and self.outputs_names == other.outputs_names
        )
    def __hash__(self) -> int:
        """
        Make IOGraph hashable by combining hashes of its components.
        """
        nodes_hash = hash(tuple(
            (node.name, type(node).__name__, getattr(node, 'weight', None))
            for node in self.nodes
        ))
        inputs_hash = hash(self.inputs_names)
        outputs_hash = hash(self.outputs_names)
        
        return hash((nodes_hash, inputs_hash, outputs_hash))
    @ft.cached_property

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

    @final
    def distance_to_closest_output(self, node_or_name: Union[str, Node]) -> tuple[int, Node]:
        """
        Returns the distance to the closest output node and the output node itself.
        Args:
            node_or_name: Node object or node name.
        Returns:
            Tuple of distance (int) and closest output Node object.
        @author: Tibob
        """
        start_name = self._get_name(node_or_name)

        if start_name in self.outputs_names:
            return (0, self[start_name])

        queue = deque([(start_name, 0)])
        visited = set()
                
        while queue:
            current_name, distance = queue.popleft()
            
            if current_name in visited:
                continue
                
            visited.add(current_name)
            
            if current_name in self.outputs_names:
                return (distance, self[current_name])
                        
            for successor_name in self._inner.successors(current_name):
                if successor_name not in visited:
                    queue.append((successor_name, distance + 1))
        
        raise ValueError(f"No path from {start_name} to any output node")
    
    @final
    def distance_to_closest_input(self, node_or_name: Union[str, Node]) -> tuple[int, Node]:
        """
        Returns the distance to the closest input node and the input node itself.
        Args:
            node_or_name: Node object or node name.
        Returns:
            Tuple of distance (int) and closest input Node object.
        """
        start_name = self._get_name(node_or_name)

        if start_name in self.inputs_names:
            return (0, self[start_name])

        queue = deque([(start_name, 0)])
        visited = set()
                
        while queue:
            current_name, distance = queue.popleft()
            
            if current_name in visited:
                continue
                
            visited.add(current_name)
            
            # FIXED: Check for inputs, not outputs
            if current_name in self.inputs_names:
                return (distance, self[current_name])
                        
            # FIXED: Go backwards to inputs (predecessors), not forwards
            for predecessor_name in self._inner.predecessors(current_name):
                if predecessor_name not in visited:
                    queue.append((predecessor_name, distance + 1))
        
        raise ValueError(f"No path from {start_name} to any input node")
    @final
    def output_nodes_of_node(self, node_or_name: Union[str, Node]) -> Sequence[Node]:
        """
        Returns the output nodes of the given node.
        Args:
            node_or_name: Node object or node name.
        Returns:
            Iterable of output Node objects.
        note: for Identity nodes, this returns the node itself.
        """
        start_name = self._get_name(node_or_name)
    
        reachable: set[str] = nx.descendants(self._inner, start_name)
        reachable.add(start_name)  
        return tuple(
            self[name] for name in reachable 
            if name in self.outputs_names
        )
    @final
    def biggest_weight_output_node(self, node_or_name: Union[str, Node]) -> Node:
        """
        Returns the output node with the biggest weight from the given node.
        Args:
            node_or_name: Node object or node name.
        Returns:
            Node object with the biggest weight.
        """
        ## Get all output nodes reachable from the given node
        output_nodes = self.output_nodes_of_node(node_or_name)
        if not output_nodes:
            raise ValueError(f"No output nodes reachable from {node_or_name}")
        weighted_nodes = [n for n in output_nodes if isinstance(n, Extras)]
        #we need to check if all output nodes have a weight attribute
        assert all(isinstance(n, Extras) for n in output_nodes), \
        "All output nodes must have weight attribute (inherit from Extras)"

        return max(weighted_nodes, key=lambda n: n.weight)
    
    def count_edges(self) -> int:
        """Count total number of edges in the graph"""
        edge_count = 0
        for node in self.nodes:
            if hasattr(node, 'operands') and node.operands:
                edge_count += len(node.operands)
        return edge_count
    def print(self) -> None:
        """
        Prints the graph in a human-readable format.
        """
        print(f"Graph with {len(self.nodes)} nodes, {len(self.inputs)} inputs, and {len(self.outputs)} outputs:")
        for node in self.nodes:
            print(f"  {node.name}: {node}")
        print(f"Inputs: {', '.join(self.inputs_names)}")
        print(f"Outputs: {', '.join(self.outputs_names)}")
class SGraph(IOGraph):
    """Graph with inputs, outputs and a subgraph."""

    @ft.cached_property
    @final
    def subgraph_nodes(self) -> Sequence[Node]:
        return tuple(
            node for node in self.nodes
            if isinstance(node, Extras) and node.in_subgraph
        )

    @ft.cached_property
    @final
    def subgraph_inputs(self) -> Sequence[Node]:
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
    def subgraph_outputs(self) -> Sequence[Node]:
        # a node is a subgraph output if it is in the subgraph and at least one successor is not in the subgraph
        return tuple(
            node for node in self.subgraph_nodes
            if any(
                not isinstance(succ, Extras) or not succ.in_subgraph
                for succ in self.successors(node)
            )
        )

    @final
    def node_edges_to_subgraph(self, node_or_name: Union[str, Node]) -> int:
        """Returns the number of edges from this node to the subgraph."""
        return sum(
            n.in_subgraph for n in self.successors(self._get_name(node_or_name))
            if isinstance(n, Extras)
        )


class PGraph(SGraph):
    """Graph with inputs, outputs and parameters (for example, parameters of a template)."""

    EXTRAS: Sequence[str] = (*SGraph.EXTRAS, 'parameters_names')

    def __init__(self, nodes: Iterable[Node],
                 inputs_names: Sequence[str], outputs_names: Sequence[str],
                 parameters_names: Sequence[str],
                 ) -> None:

        super().__init__(nodes, inputs_names, outputs_names)

        # freeze local instances
        self.parameters_names = tuple(parameters_names)

    def __eq__(self, other) -> bool:
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
        return frozenset(node for node in self.nodes if isinstance(node, PlaceHolder))

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
