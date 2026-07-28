from z3 import If, Sum

class PenaltyConstraints:
    @staticmethod
    def get_penalty_terms(edge_w, gate_weight, feasibility_treshold, gate_literals, penalty_coefficient=1):
        output_individual_penalty = []
        for s in edge_w:
            if gate_weight[s] > feasibility_treshold:
                penalty_term = If(
                    gate_literals[s], 
                    penalty_coefficient * (gate_weight[s] - feasibility_treshold), 
                    0
                )
                output_individual_penalty.append(penalty_term)
        return output_individual_penalty
    
    @staticmethod
    def apply_penalty_constraints(opt, penalty, output_individual_penalty, soft_limit, weight=1):
        opt.add(penalty == Sum(output_individual_penalty))
        opt.add_soft(Sum(output_individual_penalty) <= soft_limit, weight=weight)