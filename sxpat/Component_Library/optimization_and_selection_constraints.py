from z3 import Sum, Bool
from z3 import Bool, Optimize, BoolRef
from sxpat.utils.graph import is_selection_convex
from z3 import sat, is_true
from sxpat.config.config import WEIGHT
from typing import Dict, List, Optional
import networkx as nx


class OptimizationConstraints:
    @staticmethod
    def add_io_limits(
        opt: Optimize,
        imax: int,
        omax: int,
        partition_input_edges: List[BoolRef],
        partition_output_edges: List[BoolRef],
    ) -> None:
        
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
            opt.add(Sum(partition_output_edges) <= omax)

    @staticmethod
    def add_maximization(
        opt: Optimize,
        gate_literals: Dict[int, BoolRef],
        gate_weight: Optional[Dict[int, int]] = None,
    ) -> None:
        
        max_func = []
        # Generate function to maximize
        if gate_weight is not None:
            for gate_id in gate_literals:
                max_func.append(gate_literals[gate_id] * gate_weight[gate_id])
        else:
            for gate_id in gate_literals:
                max_func.append(gate_literals[gate_id])
        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

    @staticmethod
    def exclude_skipped_nodes(opt: Optimize, graph: nx.DiGraph) -> None:

        skipped_nodes = []
        for node in graph.nodes:
            if graph.nodes[node][WEIGHT] == -1:
                if node.startswith("g"):
                    node_literal = f"{node[0:1]}_{node[1:]}"
                elif node.startswith("in"):
                    node_literal = f"{node[0:2]}_{node[2:]}"
                elif node.startswith("out"):
                    node_literal = f"{node[0:3]}_{node[3:]}"
                else:
                    print(f"Node is neither input, output, nor gate")
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [
            node_literal == False for node_literal in skipped_nodes
        ]
        opt.add(skipped_nodes_constraints)

    @staticmethod
    def validate_selection_convexity(G: nx.DiGraph, node_partition: List[int]) -> None:

        if not is_selection_convex(G, node_partition):
            raise RuntimeError(
                "the subgraph extraction resulted in a non-convex subgraph"
            )

    @staticmethod
    def check_convexity(
        opt: Optimize, G: nx.DiGraph, gate_dict: Dict[int, str]
    ) -> List[str]:
        
        node_partition = []
        if opt.check() == sat:
            m = opt.model()
            for t in m.decls():
                if "g" not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition

        # Check partition convexity
        OptimizationConstraints.validate_selection_convexity(G, node_partition)

        return [gate_dict[idx] for idx in node_partition]
