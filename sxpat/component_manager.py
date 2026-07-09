from Component_Library.signal_propagation_constraints_minimal import SignalPropagationConstraintsMinimal
from Component_Library.signal_propagation_constraints_with_penalty import PenaltyPropagation
from Component_Library.signal_propagation_constraints import SignalPropagationConstraints
from Component_Library.convexity_and_structural_constraints import ConvexityConstraints
from Component_Library.optimization_and_selection_constraints import OptimizationConstraints 
from Component_Library.sensitivity_budget_constraints import SensitivityBudgetConstraints 

class ComponentManager:
    @staticmethod
    def get_signal_propagation_minimal(inputs, gates, outputs, lit_in, lit_gate, lit_out):
        return SignalPropagationConstraintsMinimal.define_constraints(inputs, gates, outputs, lit_in, lit_gate, lit_out)
    
    @staticmethod
    def get_signal_propagation_with_penalty(inputs, gates, outputs, lit_in, lit_gate, lit_out, 
                                            tmp_graph, gate_dict, WEIGHT, feasibility_threshold):
        return PenaltyPropagation.define_with_penalties(
            inputs, gates, outputs, lit_in, lit_gate, lit_out,
            tmp_graph, gate_dict, WEIGHT, feasibility_threshold
        )
    
    @staticmethod
    def get_signal_propagation(inputs, gates, outputs, lit_in, lit_gate, lit_out, 
                                   tmp_graph, gate_dict, weight):
        return SignalPropagationConstraints.define_structural_constraints(
            inputs, gates, outputs, lit_in, lit_gate, lit_out, 
            tmp_graph, gate_dict, weight
        )
    
    @staticmethod
    def add_convexity(opt, G, gate_literals, gate_edges):
        ConvexityConstraints.add_convexity_constraints(opt, G, gate_literals, gate_edges)

    @staticmethod
    def add_io_limits(opt, imax, omax, p_in, p_out):
        OptimizationConstraints.add_io_limits(opt, imax, omax, p_in, p_out)

    @staticmethod
    def add_maximization(opt, gate_literals, gate_weight):
        OptimizationConstraints.add_maximization(opt, gate_literals, gate_weight)

    @staticmethod
    def exclude_skipped_nodes(opt, graph):
        OptimizationConstraints.exclude_skipped_nodes(opt, graph)

    @staticmethod
    def check_convexity(opt, G, gate_dict):
        return OptimizationConstraints.check_convexity(opt, G, gate_dict)
    
    @staticmethod
    def validate_selection_convexity(G, node_partition):
        OptimizationConstraints.validate_selection_convexity(G, node_partition)

    @staticmethod
    def add_sensitivity_budget(opt, edge_w, edge_constraint, sensitivity_t):
        SensitivityBudgetConstraints.add_budget_constraints(opt, edge_w, edge_constraint, sensitivity_t)

    @staticmethod
    def prepare_gate_weights(G, tmp_graph, gate_dict, weight_key):
        return SensitivityBudgetConstraints.prepare_gate_weights(G, tmp_graph, gate_dict, weight_key)
