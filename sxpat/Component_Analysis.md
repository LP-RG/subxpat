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

* almost the same 

# Category: 
- # Connectivity-based Strategies: 1, 4, 11, 12
    Focus on interface bandwidth. They prioritize the number of connections (imax/omax) between the subgraph and the rest of the circuit.
    
    - # 1 - find_subgraph
        Signal Propagation Constraints: 
        i) Input -> Gate (Prevents a gate from activating if its source input is inactive)
            Formula: And(Not(input), gate)
        ii) Gate -> Gate (Loss) (Detects signal loss: If the source is 0, the destination must not be 1)
            Formula: And(Not(source), destination)
        iii) Gate -> Gate (Spontaneous) (Detects spontaneous activation: If the source is 1, the dest. must reflect this)
            Formula: And(source, Not(destination))
        iv) Gate -> Output (Validates final output consistency against the preceding gate state)
            Formula: And(gate, Not(output))
        
        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: Implies(And(src, Not(dest)), And(Not(descendants)))
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: Implies(And(Not(src), dest), And(Not(ancestors)))
        
        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: Sum(partition_edges) <= imax / omax
        ii) Utility Maximization (gate_weight):
            Purpose: The solver prioritizes nodes with higher weight values. By maximizing this sum, the engine selects the most "critical" or "valuable" logic gates that still satisfy the integrity constraints.
            Logic: opt.maximize(Sum(gate_literals * gate_weight))
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: node_literal == False
    
    - # 4 - find_subgraph_feasible

- # Sensitivity-based Strategies: 2, 3
    Use an iterative growth approach. They expand the subgraph by increasing the sensitivity parameter until the min_subgraph_size constraint is satisfied.

- # Formal/Hard Feasibility Strategies: 5, 6, 55
    Use mathematical rigor. They employ Datatypes and BitVec to enforce strict logical feasibility, often including weight-based thresholding for the subgraph boundaries.

- # Heuristic/Manual Strategies: 42, 100
    Represent manual overrides or experimental testing modes that bypass the standard solver optimization process. The reliance on imax and omax for finding the 'largest partition' is replaced by deterministic or experimental selection criteria