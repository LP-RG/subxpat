from z3 import Sum, And, Not

class FeasibilityConstraints:
    @staticmethod
    def get_feasibility_constraints(edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=True):
        feasibility_constraints = []
        for s in edge_w:
            if strict:
                if gate_weight[s] <= feasibility_treshold:
                    # print(s, "is feasible", gate_weight[s])
                    feasibility_constraints.append(edge_constraint[s])
            else:
                if gate_weight[s] <= feasibility_treshold and gate_weight[s] != -1:
                    # print(s, "is feasible", gate_weight[s])
                    feasibility_constraints.append(edge_constraint[s])
        return feasibility_constraints
    
    @staticmethod
    def get_feasibility_logic(opt, feasibility_constraints, partition_output_edges=None, mode='at_least_one'):
        if mode == 'at_least_one':
            opt.add(Sum(feasibility_constraints) >= 1)
        elif mode == 'match_outputs':
            if partition_output_edges is None:
                raise ValueError("partition_output_edges is required for match_outputs mode")
            opt.add(Sum(feasibility_constraints) == Sum(partition_output_edges))