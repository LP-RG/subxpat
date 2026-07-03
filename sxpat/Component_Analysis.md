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
    Focus on interface bandwidth. They prioritize the number of connections (*imax/omax*) between the subgraph and the rest of the circuit.
    
    - # 1 - find_subgraph
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges*): Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
                Logic: __And(gate_source, Not(gate_destination))__
        iii) Gate -> Output Boundary:
            Purpose: Validates the exit point where internal logic connects to an external output node.
            Logic: __And(gate_predecessor, Not(output_destination))__
        
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
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Utility Maximization (gate_weight):
            Purpose: The solver prioritizes nodes with higher weight values. By maximizing this sum, the engine selects the most "critical" or "valuable" logic gates that still satisfy the integrity constraints.
            Logic: __opt.maximize(Sum(gate_literals * gate_weight))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__
    
    - # 4 - find_subgraph_feasible
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges*): Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
                Logic: __And(gate_source, Not(gate_destination))__
        iii) Gate -> Output Boundary:
            Purpose: Validates the exit point where internal logic connects to an external output node.
            Logic: __And(gate_predecessor, Not(output_destination))__

        - Key Technical Distinction (Edge Mapping):
            While signal propagation rules remain identical to the base engine, the Edge Constraint Mapping is enhanced here. During propagation analysis, the engine anchors edge_constraint directly to the source gate. This granular mapping enables the feasibility filter (__feasibility_threshold__) to look back at the gate weight of the source during signal propagation, allowing the solver to reject boundary cuts that occur at "critical" (high-weight) gates.

        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__

        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: Identifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points.
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]__
        ii) Minimum Feasibility Guarantee:
            Purpose: Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity (Universal):
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(gate_literals))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

    - # 11 - find_subgraph_feasible_soft
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges*): Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
                Logic: __And(gate_source, Not(gate_destination))__
        iii) Gate -> Output Boundary:
            Purpose: Validates the exit point where internal logic connects to an external output node.
            Logic: __And(gate_predecessor, Not(output_destination))__

        - Key Technical Distinction (Edge Mapping):
            While signal propagation rules remain identical to the base engine, the Edge Constraint Mapping is enhanced here. During propagation analysis, the engine anchors edge_constraint directly to the source gate. This granular mapping enables the feasibility filter (__feasibility_threshold__) to look back at the gate weight of the source during signal propagation, allowing the solver to reject boundary cuts that occur at "critical" (high-weight) gates.
        
        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__
        
        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: Identifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points.
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]__
        ii) Minimum Feasibility Guarantee:
            Purpose: Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity (Universal):
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(gate_literals))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Penalty-based Soft Constraints:
        i) Penalty Modeling:
            Purpose: Instead of strictly rejecting gates above the feasibility_threshold, the engine assigns a numerical cost to them. This creates a "soft" boundary where the solver prefers feasible cuts but can "afford" to include slightly heavier gates if it results in a larger or better-connected subgraph.
            Logic: __If(gate_literals[s], penalty_coefficient * (gate_weight[s] - threshold), 0)__
        ii) Soft Constraint Enforcement:
            Purpose: Allows the solver to treat the feasibility boundary as a flexible goal (weight=1) rather than a hard logical requirement.
            Logic: __opt.add_soft(Sum(output_individual_penalty) <= 2 * feasibility_treshold, weight=1)__

        Multi-Partition Iteration Engine:
        i) Partition Enumeration:
            Purpose: Instead of finding one "optimal" subgraph, the method iteratively extracts and blocks __(opt.add(Not(And(block_clause))))__ multiple valid partitions.
            Logic: Uses a __while count > 0__ loop to repeatedly query the solver for unique solutions.
        ii) Lowest Penalty Selection: 
            Purpose: Post-processing logic that sorts all discovered partitions by penalty (cost) and size, selecting the one that best balances logical density with the feasibility threshold.
            Logic: __sorted(all_partitions.items(), key=lambda item: (-len(item[1][1]), item[1][0]))__
        
    - # 12 - find_subgraph_feasible_soft_outputs
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional & Weighted*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges & partition_output_edges_penalty*): Identifies exiting edges and simultaneously calculates the penalty if the source gate exceeds the feasibility_threshold.
                Cut Logic: __And(gate_source, Not(gate_destination))__
                Penalty Logic: __(Cut_Logic) * (gate_weight - feasibility_threshold)__
        iii) Gate -> Output Boundary:
            Purpose: Validates internal exit points to external outputs and applies penalty scaling.
            Logic: __And(gate_predecessor, Not(output_destination))__
            Penalty Logic: __(Boundary_Cut) * (gate_weight - feasibility_threshold)__

        - Key Technical Distinction (Edge Mapping):
            While signal propagation rules remain identical to the base engine, the Edge Constraint Mapping is enhanced here. During propagation analysis, the engine anchors edge_constraint directly to the source gate. This granular mapping enables the feasibility filter (__feasibility_threshold__) to look back at the gate weight of the source during signal propagation, allowing the solver to reject boundary cuts that occur at "critical" (high-weight) gates.

        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__

        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: Identifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points.
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]__
        ii) Minimum Feasibility Guarantee:
            Purpose: Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity (Universal):
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(max_func))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Penalty-based Soft Constraints:
        i) Penalty Modeling: 
            Purpose: To create a "soft" boundary for feasibility. By differentiating between interface (output) costs and internal (gate) costs, the solver can prioritize modular connections over internal gate weight.
            Logic:  # For internal gate density
                    __output_individual_penalty.append(If(gate_literals[s], penalty_coefficient * (gate_weight[s] - feasibility_treshold), 0))__
        ii) Soft Constraint Enforcement (Hierarchical)
            Purpose: To establish a priority hierarchy (Lexicographical Preference). The engine treats output-side cut feasibility as a critical requirement (weight=100) while treating internal gate density as a flexible optimization goal (weight=1).
            Logic:  # High-priority constraint for interface modularity
                    __opt.add_soft(IntVal(1) * Sum(partition_output_edges_penalty) <= omax * threshold, weight=100)__
                    # Lower-priority constraint for internal gate density
                    __opt.add_soft(IntVal(1) * Sum(output_individual_penalty) <= omax * threshold, weight=1)__
        
        Multi-Partition Iteration Engine
        i) Partition Enumeration (Exhaustive Search):
            Purpose: Instead of finding one "optimal" subgraph, the method iteratively extracts and blocks __(opt.add(Not(And(block_clause))))__ multiple valid partitions.
            Logic: Uses a __while count > 0__ loop to repeatedly query the solver for unique solutions.
        ii) Lowest Penalty Selection (Multi-Attribute Ranking): 
            Purpose: Post-processing logic that ranks all discovered partitions to select the one that optimizes for three criteria: size (maximization), output interface cost (minimization), and internal gate cost (minimization).
            Logic:  # Primary: Maximize partition size (-len)
                    # Secondary: Minimize output penalty (item[1][0])
                    # Tertiary: Minimize internal gate penalty (item[1][1])
                    __sorted(all_partitions.items(), key=lambda item: (-len(item[1][2]), item[1][0], item[1][1]))__


- # Sensitivity-based Strategies: 2, 3
    Use an iterative growth approach. They expand the subgraph by increasing the sensitivity parameter until the min_subgraph_size constraint is satisfied.

    - # 2 - find_subgraph_sensitivity
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges*): Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
                Logic: __And(gate_source, Not(gate_destination))__
        iii) Gate -> Output Boundary:
            Purpose: Validates the exit point where internal logic connects to an external output node.
            Logic: __And(gate_predecessor, Not(output_destination))__

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
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(max_func))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__
        
        Sensitivity Budget Constraints:
        i) Sensitivity Budgeting (Hard Constraint):
            Purpose: Enforces a hard limit on the total accumulated sensitivity at the boundary. Unlike soft penalties, this acts as a "hard budget," ensuring the partition stays within critical exposure limits
            Logic: __opt.add(Sum([edge_constraint[s] * edge_w[s]]) <= sensitivity_t)__
        ii) Weight Normalization:
            Purpose: Inverts gate weights (max - weight + 1) to prioritize the inclusion of high-weight (critical) gates by making them "cheaper" to fit within the sensitivity budget.
            Logic: __gate_weight[id] = max_weight - gate_weight[id] + 1__
        iii) Structural Integrity (Universal):
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

    - # 3 - find_subgraph_sensitivity_no_io_constraints
        Signal Propagation Constraints: 
        i) Input -> Gate Boundary (*partition_input_edges*):
            Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
            Logic: __And(Not(input_source), gate_destination)__
        ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut (*partition_input_edges*): Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
                Logic: __And(Not(gate_source), gate_destination)__
            - Output-side Cut (*partition_output_edges*): Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
                Logic: __And(gate_source, Not(gate_destination))__
        iii) Gate -> Output Boundary:
            Purpose: Validates the exit point where internal logic connects to an external output node.
            Logic: __And(gate_predecessor, Not(output_destination))__
        
        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__

        Optimization and Selection Constraints:
        i) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(max_func))__
        ii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with WEIGHT == -1, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Sensitivity Budget Constraints:
        i) Sensitivity Budgeting (Hard Constraint):
            Purpose: Enforces a hard limit on the total accumulated sensitivity at the boundary. Unlike soft penalties, this acts as a "hard budget," ensuring the partition stays within critical exposure limits
            Logic: __opt.add(Sum([edge_constraint[s] * edge_w[s]]) <= sensitivity_t)__
        ii) Weight Normalization:
            Purpose: Inverts gate weights (max - weight + 1) to prioritize the inclusion of high-weight (critical) gates by making them "cheaper" to fit within the sensitivity budget.
            Logic: __gate_weight[id] = max_weight - gate_weight[id] + 1__
        iii) Structural Integrity (Universal):
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

- # Formal/Hard Feasibility Strategies: 5, 6, 55
    Use mathematical rigor. They employ Datatypes and BitVec to enforce strict logical feasibility, often including weight-based thresholding for the subgraph boundaries.

- # Heuristic/Manual Strategies: 42, 100
    Represent manual overrides or experimental testing modes that bypass the standard solver optimization process. The reliance on imax and omax for finding the 'largest partition' is replaced by deterministic or experimental selection criteria