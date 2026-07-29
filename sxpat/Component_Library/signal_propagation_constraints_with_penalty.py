from z3 import And, Not, Or, BoolRef
from typing import Dict, List, Tuple, Any
import networkx as nx

class PenaltyPropagation:
    
    @staticmethod
    def define_with_penalties(
            input_edges: Dict[int, List[int]],
            gate_edges: Dict[int, List[int]],
            output_edges: Dict[int, List[int]],
            input_literals: Dict[int, BoolRef],
            gate_literals: Dict[int, BoolRef],
            output_literals: Dict[int, BoolRef],
            tmp_graph: nx.DiGraph,
            gate_dict: Dict[int, str],
            WEIGHT: str,
            feasibility_threshold: int,
        ) -> Tuple[
            List[BoolRef], List[BoolRef], List[Any], Dict[int, int], Dict[int, BoolRef]
        ]:
        
        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])
        partition_output_edges_penalty = []
        edge_w, edge_constraint = {}, {}

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges and data structures containing the edge weights
        edge_w = {}
        edge_constraint = {}

        for source in gate_edges:
            # print(f'{gate_literals[source] = }')
            # print(f'{tmp_graph.nodes[gate_dict[source]][WEIGHT] = }')
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            if source not in edge_w:
                edge_w[source] = tmp_graph.nodes[gate_dict[source]][WEIGHT]

            if source not in edge_constraint:
                edge_constraint[source] = Or(edge_out_holder)
            partition_output_edges.append(Or(edge_out_holder))
            if tmp_graph.nodes[gate_dict[source]][WEIGHT] > feasibility_threshold:
                this_output_penalty = tmp_graph.nodes[gate_dict[source]][WEIGHT] - feasibility_threshold
                partition_output_edges_penalty.append(Or(edge_out_holder) * this_output_penalty)
            # else:
            #     partition_output_edges_penalty.append(Or(edge_out_holder) * IntVal(0))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)

            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))
            if predecessor not in edge_w:
                edge_w[predecessor] = tmp_graph.nodes[gate_dict[predecessor]][WEIGHT]
            if predecessor not in edge_constraint:
                edge_constraint[predecessor] = e_out

            partition_output_edges.append(e_out)

            if tmp_graph.nodes[gate_dict[predecessor]][WEIGHT] > feasibility_threshold:
                this_output_penalty = tmp_graph.nodes[gate_dict[predecessor]][WEIGHT] - feasibility_threshold
                partition_output_edges_penalty.append(e_out * this_output_penalty)
            # else:
            #     partition_output_edges_penalty.append(e_out * IntVal(0))

        return partition_input_edges, partition_output_edges, partition_output_edges_penalty, edge_w, edge_constraint