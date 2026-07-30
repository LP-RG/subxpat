from z3 import Sum, BoolRef, Optimize
from typing import Dict
import networkx as nx


class SensitivityBudgetConstraints:
    @staticmethod
    def add_budget_constraints(
        opt: Optimize,
        edge_w: Dict[int, int],
        edge_constraint: Dict[int, BoolRef],
        sensitivity_t: int,
    ) -> None:

        """
        Imposes a strict budget on the total accumulated sensitivity.
        """
        
        sensitivity_constraints = [edge_constraint[s] * edge_w[s] for s in edge_w]
        opt.add(Sum(sensitivity_constraints) <= sensitivity_t)

    @staticmethod
    def prepare_gate_weights(G, tmp_graph, gate_dict, weight_key):

        """
        Normalizes and prepares gate weights to favor inclusion of critical logic.
        """

        # COMPONENT START: Model Initialization
        from sxpat.Component_Library.model_initialization import ModelInitialization
        gate_weight = ModelInitialization.extract_gate_weights(G, tmp_graph, gate_dict, weight_key)
        # COMPONENT END: Model Initialization

        # Find max weight
        max_weight = 0
        for gate_id in gate_weight:
            max_weight = max(max_weight, gate_weight[gate_id])

        # Update gate weights so that gate_weight = max_weight - max_weight
        for gate_id in gate_weight:
            gate_weight[gate_id] = (
                max_weight - gate_weight[gate_id] + 1
            )  # + 1 must be removed, I'm leaving it just for the initial debugging phase

        return gate_weight
