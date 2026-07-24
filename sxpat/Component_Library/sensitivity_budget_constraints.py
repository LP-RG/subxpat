from z3 import Sum, And, Not
from sxpat.config.config import WEIGHT

class SensitivityBudgetConstraints:
    @staticmethod
    def add_budget_constraints(opt, edge_w, edge_constraint, sensitivity_t):
        sensitivity_constraints = [edge_constraint[s] * edge_w[s] for s in edge_w]
        opt.add(Sum(sensitivity_constraints) <= sensitivity_t)

    @staticmethod
    def prepare_gate_weights(G, tmp_graph, gate_dict, weight_key):
        # Generate structure with gate weights
        gate_weight = {}
        for gate_idx in G.nodes:
            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[gate_dict[gate_idx]][weight_key]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        # Find max weight
        max_weight = 0
        for gate_id in gate_weight:
            max_weight = max(max_weight, gate_weight[gate_id])

        # Update gate weights so that gate_weight = max_weight - max_weight
        for gate_id in gate_weight:
            gate_weight[gate_id] = max_weight - gate_weight[
                gate_id] + 1  # + 1 must be removed, I'm leaving it just for the initial debugging phase