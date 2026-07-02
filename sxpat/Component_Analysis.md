# 1) Component_Analysis
- 1. find_subgraph * 
- 2. find_subgraph_sensitivity *
- 3. find_subgraph_sensitivity_no_io_constraints *
- 4. find_subgraph_feasible *
- 5. find_subgraph_feasible_hard *
- 55. find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
- 6. find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
- 100. slash_to_kill
- 11. find_subgraph_feasible_soft *
- 12. find_subgraph_feasible_soft_outputs *

* almost the same 

# Category: 
- # Connectivity-based Strategies: 1, 4, 11, 12
    Focus on interface bandwidth. They prioritize the number of connections (imax/omax) between the subgraph and the rest of the circuit.
    
    - # 1 - find_subgraph
        Signal Propagation Constraints: 
        i) Input -> Gate (Prevents a gate from activating if its source input is inactive)
            Formula: __And(Not(input), gate)__
        ii) Gate -> Gate (Loss) (Detects signal loss: If the source is 0, the destination must not be 1)
            Formula: __And(Not(source), destination)__
        iii) Gate -> Gate (Spontaneous) (Detects spontaneous activation: If the source is 1, the dest. must reflect this)
            Formula: __And(source, Not(destination))__
        iv) Gate -> Output (Validates final output consistency against the preceding gate state)
            Formula: __And(gate, Not(output))__
        
        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__
        
        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __Sum(partition_edges) <= imax / omax__
        ii) Utility Maximization (gate_weight):
            Purpose: The solver prioritizes nodes with higher weight values. By maximizing this sum, the engine selects the most "critical" or "valuable" logic gates that still satisfy the integrity constraints.
            Logic: __opt.maximize(Sum(gate_literals * gate_weight))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__
    
    - # 4 - find_subgraph_feasible
        Signal Propagation Constraints: 
        i) Input -> Gate (Prevents a gate from activating if its source input is inactive)
            Formula: __And(Not(input), gate)__
        ii) Gate -> Gate (Loss) (Detects signal loss: If the source is 0, the destination must not be 1)
            Formula: __And(Not(source), destination)__
        iii) Gate -> Gate (Spontaneous) (Detects spontaneous activation: If the source is 1, the dest. must reflect this)
            Formula: __And(source, Not(destination))__
        iv) Gate -> Output (Validates final output consistency against the preceding gate state)
            Formula: __And(gate, Not(output))__

        - Key Technical Distinction (Edge Mapping):
            While signal propagation rules remain identical to the base engine, the Edge Constraint Mapping is enhanced here. During propagation analysis, the engine anchors edge_constraint directly to the source gate. This granular mapping enables the feasibility filter (feasibility_threshold) to look back at the gate weight of the source during signal propagation, allowing the solver to reject boundary cuts that occur at "critical" (high-weight) gates.

        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__

        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose -> Identifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points.
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]__
        ii) Minimum Feasibility Guarantee:
            Purpose -> Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity (Universal):
            Purpose -> Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __opt.add(Sum(partition_input_edges) <= imax)__
        ii) Gate Count Maximization:
            Purpose -> Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(gate_literals))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__


- # Sensitivity-based Strategies: 2, 3
    Use an iterative growth approach. They expand the subgraph by increasing the sensitivity parameter until the min_subgraph_size constraint is satisfied.

- # Formal/Hard Feasibility Strategies: 5, 6, 55
    Use mathematical rigor. They employ Datatypes and BitVec to enforce strict logical feasibility, often including weight-based thresholding for the subgraph boundaries.

- # Heuristic/Manual Strategies: 42, 100
    Represent manual overrides or experimental testing modes that bypass the standard solver optimization process. The reliance on imax and omax for finding the 'largest partition' is replaced by deterministic or experimental selection criteria