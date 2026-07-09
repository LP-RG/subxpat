from Component_Library.signal_propagation_constraints_minimal import SignalPropagationConstraintsMinimal
from Component_Library.signal_propagation_constraints_with_penalty import PenaltyPropagation
from Component_Library.signal_propagation_constraints import SignalPropagationConstraints
from Component_Library.convexity_and_structural_constraints import ConvexityConstraints

class ComponentManager:
    def get_signal_propagation_minimal(self, inputs, gates, outputs, lit_in, lit_gate, lit_out):
        return SignalPropagationConstraintsMinimal.define_constraints(inputs, gates, outputs, lit_in, lit_gate, lit_out)
    
    def get_signal_propagation_with_penalty(self, inputs, gates, outputs, lit_in, lit_gate, lit_out, 
                                            tmp_graph, gate_dict, WEIGHT, feasibility_threshold):
        return PenaltyPropagation.define_with_penalties(
            inputs, gates, outputs, lit_in, lit_gate, lit_out,
            tmp_graph, gate_dict, WEIGHT, feasibility_threshold
        )
    
    def get_signal_propagation(inputs, gates, outputs, lit_in, lit_gate, lit_out, 
                                   tmp_graph, gate_dict, weight):
        return SignalPropagationConstraints.define_structural_constraints(
            inputs, gates, outputs, lit_in, lit_gate, lit_out, 
            tmp_graph, gate_dict, weight
        )
    
    def add_convexity(opt, G, gate_literals, gate_edges):
        ConvexityConstraints.add_convexity_constraints(opt, G, gate_literals, gate_edges)