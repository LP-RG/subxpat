from z3 import If, IntVal, Sum
from typing import Dict, List, Any
import networkx as nx
from z3 import Optimize, BoolRef, ArithRef


class PenaltyConstraints:
    @staticmethod
    def get_penalty_terms(
        edge_w: Dict[int, int],
        gate_weight: Dict[int, int],
        feasibility_treshold: int,
        gate_literals: Dict[int, BoolRef],
        penalty_coefficient: int = 1,
    ) -> List[Any]:

        """
        Calculates soft boundary constraint penalties.
        """
        
        output_individual_penalty = []
        for s in edge_w:
            if gate_weight[s] > feasibility_treshold:
                penalty_term = If(
                    gate_literals[s],
                    penalty_coefficient * (gate_weight[s] - feasibility_treshold),
                    0,
                )
                output_individual_penalty.append(penalty_term)
        return output_individual_penalty

    @staticmethod
    def apply_penalty_constraints(
        opt: Optimize,
        penalty: ArithRef,
        output_individual_penalty: List[Any],
        soft_limit: int,
        weight: int = 1,
    ) -> None:

        """
        Applies a flexible penalty constraint to balance modularity against feasibility deviations.
        """
        
        opt.add(penalty == Sum(output_individual_penalty))
        # Why IntVal(1)? => Because sometimes the Sum results into an integer "Python number (e.g., int)", but we need a "Z3 number (e.g., ArithRef)"
        opt.add_soft(
            IntVal(1) * Sum(output_individual_penalty) <= soft_limit, weight=weight
        )
