from sxpat.Component_Library.signal_propagation_constraints_minimal import SignalPropagationConstraintsMinimal
from sxpat.Component_Library.signal_propagation_constraints_with_penalty import PenaltyPropagation
from sxpat.Component_Library.signal_propagation_constraints import SignalPropagationConstraints
from sxpat.Component_Library.convexity_and_structural_constraints import ConvexityConstraints
from sxpat.Component_Library.optimization_and_selection_constraints import OptimizationConstraints 
from sxpat.Component_Library.sensitivity_budget_constraints import SensitivityBudgetConstraints 
from sxpat.Component_Library.feasibility_and_filtering_constraints import FeasibilityConstraints
from sxpat.Component_Library.penalty_based_soft_constraints import PenaltyConstraints
from sxpat.Component_Library.model_initialization import ModelInitialization
from sxpat.Component_Library.multi_partition_iteration_engine import MultiPartitionIterationEngine
from sxpat.Component_Library.bitvector_topology_management import BitvectorTopologyManagement

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
    
    @staticmethod
    def get_feasibility(edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True):
        return FeasibilityConstraints.get_feasibility_constraints(edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=strict)
    
    @staticmethod
    def add_feasibility_logic(opt, feasibility_constraints, partition_output_edges=None, mode='at_least_one'):
        FeasibilityConstraints.get_feasibility_logic(opt, feasibility_constraints, partition_output_edges, mode)

    @staticmethod
    def get_penalty_terms(edge_w, gate_weight, feasibility_treshold, gate_literals, penalty_coefficient=1):
        return PenaltyConstraints.get_penalty_terms(
            edge_w, gate_weight, feasibility_treshold, gate_literals, penalty_coefficient
        )
    
    @staticmethod
    def apply_penalty(opt, penalty_var, penalty_list, soft_limit, weight=1):
        PenaltyConstraints.apply_penalty_constraints(opt, penalty_var, penalty_list, soft_limit, weight)

    @staticmethod
    def prepare_circuit_model(tmp_graph, constant_dict):
        return ModelInitialization.prepare_circuit_model(tmp_graph, constant_dict)
    
    @staticmethod
    def build_gate_graph(tmp_graph, constant_dict):
        return ModelInitialization.build_gate_graph(tmp_graph, constant_dict)
    
    @staticmethod
    def add_boundary_conditions(opt, input_literals, output_literals):
        ModelInitialization.add_boundary_conditions(opt, input_literals, output_literals)
    
    @staticmethod
    def extract_gate_weights(G, tmp_graph, gate_dict, weight_key):
        return ModelInitialization.extract_gate_weights(G, tmp_graph, gate_dict, weight_key)
    
    @staticmethod
    def extract_multiple_subgraphs(opt, G, specs_obj, mode='multi', penalty=None):
        return MultiPartitionIterationEngine.extract_multiple_subgraphs(
            opt, G, specs_obj, mode=mode, penalty=penalty
        )
    
    @staticmethod
    def select_best_partition(all_partitions, mode='multi'):
        return MultiPartitionIterationEngine.select_best_partition(all_partitions, mode=mode)
    
    @staticmethod
    def datatype_model_initialization(graph, weight_key, input_dict, gate_dict, output_dict, constant_dict, opt, num_outputs, num_gates):
        return BitvectorTopologyManagement.datatype_model_initialization(
            graph, weight_key, input_dict, gate_dict, output_dict, constant_dict, opt, num_outputs, num_gates
        )
    
    @staticmethod
    def datatype_signal_propagation_constraints(graph, nodes, Node, NUM_BITS):
        return BitvectorTopologyManagement.datatype_signal_propagation_constraints(
            graph, nodes, Node, NUM_BITS
        )
    
    @staticmethod
    def datatype_convexity_and_structural_constraints(graph, nodes, Node, opt):
        BitvectorTopologyManagement.datatype_convexity_and_structural_constraints(
            graph, nodes, Node, opt
        )

    @staticmethod
    def datatype_optimization_and_selection_constraints(
        opt, max_nodes, graph, gate_dict, imax=None, omax=None, 
        unique_incoming_edges=None, unique_outgoing_edges=None, apply_io_limits=False
    ):
        return BitvectorTopologyManagement.datatype_optimization_and_selection_constraints(
            opt, max_nodes, graph, gate_dict, imax, omax, 
            unique_incoming_edges, unique_outgoing_edges, apply_io_limits
        )
    
    @staticmethod
    def datatype_feasibility_and_filtering_constraints(edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode=False):
        return BitvectorTopologyManagement.datatype_feasibility_and_filtering_constraints(
            edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode
        )
    
    @staticmethod
    def datatype_parent_child_constraints(graph, nodes, Node, opt):
        BitvectorTopologyManagement.datatype_parent_child_constraints(graph, nodes, Node, opt)