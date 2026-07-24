from z3 import Sum, Bool, Not, And
from z3 import Bool, Optimize
from sxpat.utils.graph import is_selection_convex
from z3 import sat, is_true
from sxpat.config.config import WEIGHT

class OptimizationConstraints:
    @staticmethod
    def add_io_limits(opt, imax, omax, partition_input_edges, partition_output_edges):
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
            opt.add(Sum(partition_output_edges) <= omax)

    @staticmethod
    def add_maximization(opt, gate_literals, gate_weight=None):
        # Generate function to maximize
        if gate_weight is not None:
            max_func = [gate_literals[gate_id] * gate_weight[gate_id] for gate_id in gate_literals]
        else:
            max_func = [gate_literals[gate_id] for gate_id in gate_literals]
        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

    @staticmethod
    def exclude_skipped_nodes(opt, graph):
        skipped_nodes = []
        for node in graph.nodes:
            if graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)

    @staticmethod
    def check_convexity(opt, G, gate_dict):
        print("NUMBER:", len(opt.assertions()))
        node_partition = []
        if opt.check() == sat:
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition

        # Check partition convexity
        if not is_selection_convex(G, node_partition):
            raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')
        return [gate_dict[idx] for idx in node_partition]
    
    @staticmethod
    def validate_selection_convexity(G, node_partition):
        if not is_selection_convex(G, node_partition):
            raise RuntimeError('the subgraph extraction resulted in a non-convex subgraph')