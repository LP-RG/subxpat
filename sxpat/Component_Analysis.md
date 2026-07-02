# 1) Component_Analysis
- find_subgraph *
- find_subgraph_sensitivity *
- find_subgraph_sensitivity_no_io_constraints *
- find_subgraph_feasible *
- find_subgraph_feasible_hard *
- find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
- find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
- find_subgraph_feasible_soft *
- find_subgraph_feasible_soft_outputs *

# Category: 
- # Connectivity-based Strategies: 1, 4, 11, 12
    Focus on interface bandwidth. They prioritize the number of connections (imax/omax) between the subgraph and the rest of the circuit.

- # Sensitivity-based Strategies: 2, 3
    Use an iterative growth approach. They expand the subgraph by increasing the sensitivity parameter until the min_subgraph_size constraint is satisfied.

- # Formal/Hard Feasibility Strategies: 5, 6, 55
    Use mathematical rigor. They employ Datatypes and BitVec to enforce strict logical feasibility, often including weight-based thresholding for the subgraph boundaries.

- # Heuristic/Manual Strategies: 42, 100
    Represent manual overrides or experimental testing modes that bypass the standard solver optimization process. The reliance on imax and omax for finding the 'largest partition' is replaced by deterministic or experimental selection criteria