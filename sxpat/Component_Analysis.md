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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__
        iv) Structural Integrity Audit (Local Graph Context)
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

        Sensitivity Budget Constraints:
        i) Weight Normalization
            Purpose: Inverts gate weights (*max - weight + 1*) to prioritize the inclusion of high-weight (critical) gates by making them "cheaper" to fit within the sensitivity budget.
            Logic: __gate_weight[id] = max_weight - gate_weight[id] + 1__

    
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
        iii) Structural Integrity Audit (Local Graph Context)
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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
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

        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__
        
        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: dentifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points, while strictly excluding inactive/skipped nodes (-1 weight).
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold and gate_weight[s] != -1]__
        ii) Minimum Feasibility Guarantee:
            Purpose: Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity Audit (Local Graph Context)
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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Penalty-based Soft Constraints:
        i) Penalty Modeling: 
            Purpose: To create a "soft" boundary for feasibility. By differentiating between interface (output) costs and internal (gate) costs, the solver can prioritize modular connections over internal gate weight.
            Logic:  # For internal gate density
                    __output_individual_penalty.append(If(gate_literals[s], penalty_coefficient * (gate_weight[s] - feasibility_treshold), 0))__
        ii) Soft Constraint Enforcement:
            Purpose: Allows the solver to treat the feasibility boundary as a flexible goal (weight=1) rather than a hard logical requirement.
            Logic: __opt.add_soft(Sum(output_individual_penalty) <= 2 * feasibility_treshold, weight=1)__

        Multi-Partition Iteration Engine:
        i) Partition Enumeration (Exhaustive Search):
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

        Convexity and Structural Constraints:
        i) Descendant Consistency:
            Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
            Logic: __Implies(And(src, Not(dest)), And(Not(descendants)))__
        ii) Ancestor Consistency:
            Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.
            Logic: __Implies(And(Not(src), dest), And(Not(ancestors)))__

        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: dentifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points, while strictly excluding inactive/skipped nodes (-1 weight).
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold and gate_weight[s] != -1]__
        ii) Minimum Feasibility Guarantee:
            Purpose: Forces the partition to possess at least one interface point that meets the feasibility threshold, preventing the extraction of an overly isolated or "locked" subgraph.
            Logic: __opt.add(Sum(feasibility_constraints) >= 1)__
        iii) Structural Integrity Audit (Local Graph Context)
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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Penalty-based Soft Constraints:
        i) Penalty Modeling: 
            Purpose: To create a "soft" boundary for feasibility. By differentiating between interface (output) costs and internal (gate) costs, the solver can prioritize modular connections over internal gate weight.
            Logic:  # For internal gate density
                    __output_individual_penalty.append(If(gate_literals[s], penalty_coefficient * (gate_weight[s] - feasibility_treshold), 0))__
        ii) Soft Constraint Enforcement (Hierarchical)
            Purpose: To establish a priority hierarchy (Lexicographical Preference). The engine treats output-side cut feasibility as a critical requirement (*weight=100*) while treating internal gate density as a flexible optimization goal (*weight=1*).
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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__
        
        Sensitivity Budget Constraints:
        i) Sensitivity Budgeting (Hard Constraint):
            Purpose: Enforces a hard limit on the total accumulated sensitivity at the boundary. Unlike soft penalties, this acts as a "hard budget," ensuring the partition stays within critical exposure limits
            Logic: __opt.add(Sum([edge_constraint[s] * edge_w[s]]) <= sensitivity_t)__
        ii) Weight Normalization
            Purpose: Inverts gate weights (*max - weight + 1*) to prioritize the inclusion of high-weight (critical) gates by making them "cheaper" to fit within the sensitivity budget.
            Logic: __gate_weight[id] = max_weight - gate_weight[id] + 1__
        iii) Structural Integrity Audit (Local Graph Context)
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
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Sensitivity Budget Constraints:
        i) Sensitivity Budgeting (Hard Constraint):
            Purpose: Enforces a hard limit on the total accumulated sensitivity at the boundary. Unlike soft penalties, this acts as a "hard budget," ensuring the partition stays within critical exposure limits
            Logic: __opt.add(Sum([edge_constraint[s] * edge_w[s]]) <= sensitivity_t)__
        ii) Weight Normalization
            Purpose: Inverts gate weights (*max - weight + 1*) to prioritize the inclusion of high-weight (critical) gates by making them "cheaper" to fit within the sensitivity budget.
            Logic: __gate_weight[id] = max_weight - gate_weight[id] + 1__
        iii) Structural Integrity Audit (Local Graph Context)
            Purpose: Inherits convexity and skip-logic rules from the core engine to ensure the final partition remains a logically sound and continuous logic block.
            Logic: __is_selection_convex(G, node_partition)__

- # Formal/Hard Feasibility Strategies: 5, 6, 55
    Use mathematical rigor. They employ Datatypes and BitVec to enforce strict logical feasibility, often including weight-based thresholding for the subgraph boundaries.

    - # 5 - find_subgraph_feasible_hard
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

        Optimization and Selection Constraints:
        i) Boundary Bandwidth (imax/omax):
            Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
            Logic: __opt.add(Sum(partition_input_edges) <= imax) and opt.add(Sum(partition_output_edges) <= omax)__
        ii) Gate Count Maximization:
            Purpose: Shifts the optimization goal from maximizing total weighted utility to maximizing the total number of logic gates (density) within the partition.
            Logic: __opt.maximize(Sum(max_func))__
        iii) Mandatory Inactivity (skipped_nodes):
            Purpose: Explicitly excludes nodes marked with *WEIGHT == -1*, ensuring they are treated as inactive and are not included in the final node_partition.
            Logic: __node_literal == False__

        Feasibility and Filtering Constraints:
        i) Feasibility Threshold Filtering:
            Purpose: Identifies "safe-to-cut" interface edges. Only edges connected to gates with a weight lower than or equal to the feasibility_threshold are eligible for selection as boundary points.
            Logic: __feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]__
        ii) Strict Boundary Feasibility:
            Purpose: Enforces an absolute constraint where every single output edge of the partition must originate from a "feasible" gate (a gate with a weight below or equal to the feasibility_threshold). Unlike the soft-constraint variant, this method permits no exceptions; if a boundary cut cannot be formed by feasible gates, the solver will return no solution.
            Logic: __opt.add(Sum(feasibility_constraints) == Sum(partition_output_edges))__
        iii) Structural Integrity Audit (Global Graph Context):
            Purpose: Acts as the final safety auditor and translator. It ensures that the symbolic result from the solver is topologically sound (convex) and maps the internal Z3 identifiers back to the original graph's gate references.
            Logic:  # Integrity Audit: Discards any result that fails the connectivity test, raising a *RuntimeError* if the subgraph is non-convex.
                        __if not is_selection_convex(self.graph, node_partition): raise RuntimeError(...)__

    - # 6 - find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold
        Purpose-Logic Documentation:
        i) Weight Distribution Analysis:
            Purpose: Dynamically determines the range of gate weights (min_weight to max_weight) to calibrate the feasibility search space based on the specific circuit instance. It then discretizes this range into 8 representative threshold levels to ensure the search is both efficient and aligned with the actual weight distribution of the graph.
            Logic: # Linear Scaling: Creates 8 linearly spaced steps across the weight range.
                    __weights = sorted(frozenset(...)), partition_step = (max_weight - min_weight) / (8 - 1)__
                    __linear_partition = [min_weight + partition_step * i for i in range(8)]__
                   # Weight Mapping: Maps the linear steps to the actual nearest gate weights present in the circuit to avoid testing "impossible" thresholds.
                    __actual_partition = sorted(frozenset(min(weights, key=lambda w: abs(w - p)) for p in linear_partition))__
        ii) Iterative Threshold Sweep:
            Purpose: Implements a coarse-to-fine search by testing 8 discretized threshold levels (actual_partition). It attempts to extract a valid subgraph starting from the lowest threshold level, ensuring the most restrictive (and often most conservative/safe) feasible partition is found first.
            Logic: __for (i, specs_obj.et) in enumerate(actual_partition):__
                   __subgraph_nodes = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)__
        iii) State Restoration:
            Purpose: Ensures that the Specifications object is returned to its original state after the execution,preventing side effects on other parts of your engine.
            Logic: __specs_obj.et = saved_et__

    - # 55 - find_subgraph_feasible_hard_limited_inputs_datatype_bitvec
        Architecture Initialization:
            Purpose: Establishes a formal, typed environment for the circuit. By declaring Node and Edge as Datatypes, you enable the solver to perform attribute-based operations (ID, Weight, In-Subgraph) rather than managing large lists of disconnected Boolean variables.
            Logic:  __Node = Datatype('Node'); Node.declare('mk_node', ('id', BitVecSort), ('weight', BitVecSort),('in_subgraph', BoolSort))__
                    __Edge = Datatype('Edge'); Edge.declare('mk_edge', ('source', Node), ('target', Node))__

        Graph Data Ingestion:
            Purpose: Maps the physical circuit topology into the solver's memory. This phase initializes every node by binding its unique identity, weight properties, and initial subgraph membership status to a symbolic Node object.
            Logic: For each node in the graph, the solver registers the following constraints simultaneously to establish the node's formal state:
                # Identity Anchor: __Node.id(node) == BitVecVal(id, NUM_BITS)__
                # Weight Property: __Node.weight(node) == BitVecVal(weight, NUM_BITS)__
                # State Binding: __Node.in_subgraph(node) == BoolVal(False)__ (Locks external nodes/constants out of the partition scope)

        Symbolic Cut & Flow Constraints:
            Purpose: Detects boundary cuts dynamically. Instead of pre-calculating every edge, the solver evaluates the in_subgraph status of the source vs. target of every declared Edge object to identify entry/exit points and enforces bandwidth constraints.
            Logic:  # Boundary Detection:
                        + Outgoing Cut: __And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des])))__
                        + Incoming Cut: __And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des]))__
                    # Symbolic Counting: Uses an If statement to map boolean cut conditions to BitVec values for summation.
                        __If(Or(outgoing_conditions or incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))__
                    # Bandwidth Enforcement:
                        + Max Incoming: __opt.add(Sum(unique_incoming_edges) <= imax)__
                        + Max Outgoing: __opt.add(Sum(unique_outgoing_edges) <= omax)__

        Structural & Convexity Constraints:
            i) Descendant Consistency:
                Purpose: Ensures that if a signal path is broken at the boundary (source is in_subgraph, destination is out), no downstream nodes can be included in the subgraph. This prevents the solver from picking "floating" logic fragments downstream that have no connection to the partition's internal logic.
                Logic: __Implies(And(src_in, Not(des_in)), And(Not(descendants_in)))__

            ii) Ancestor Consistency:
                Purpose: Ensures that if a destination node is included in the subgraph while its source is not, no upstream nodes (ancestors) can be included. This prevents the solver from creating "spontaneously generated" logic fragments that are fed by external nodes not present in the subgraph.
                Logic: __Implies(And(Not(src_in), des_in), And(Not(ancestors_in)))__
                
        Formal Feasibility Filter:
            Purpose: Enforces an absolute constraint where boundary edges are only permissible if the source gate meets the *feasibility_threshold*. This is a symbolic verification of the signal path's integrity at the partition boundary.
            Logic: __opt.add(And([Implies__
                        __(And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),__
                        __Node.weight(Edge.source(edge)) <= BitVecVal(feasibility_threshold, NUM_BITS))]))__
        
        Optimization & Maximization Objective:
            Purpose: Guarantees the absolute maximum density of the subgraph. It employs a two-stage solver strategy: it finds the theoretical maximum (h.upper()) and, if the initial model falls short, forces a second pass to guarantee optimality.
            Logic:  __h = opt.maximize(Sum(max_nodes))__
                    __if correct_maximum != model_maximized: opt.add(Sum(max_nodes) == correct_maximum)__
        
        Structural Integrity Audit (Global Graph Context):
            Purpose: Acts as the final safety auditor and translator. It ensures that the symbolic result from the solver is topologically sound (convex) and maps the internal Z3 identifiers back to the original graph's gate references.
            Logic:  # Integrity Audit: Discards any result that fails the connectivity test, raising a *RuntimeError* if the subgraph is non-convex.
                        __if not is_selection_convex(self.graph, node_partition): raise RuntimeError(...)__
        
- # Heuristic/Manual Strategies: 42, 100
    Represent manual overrides or experimental testing modes that bypass the standard solver optimization process. The reliance on imax and omax for finding the 'largest partition' is replaced by deterministic or experimental selection criteria

    - # 42 - extract
        Interactive Selection Loop:
            Purpose: Provides complete control to the user, bypassing the solver logic. This allows for manual prototyping, debugging, or creating specific subgraphs that the solver might struggle to find.
            Logic: __while True: selected_nodes = input(...).split()__
        Validation & Topological Guardrails:
            Purpose: Ensures the manual selection adheres to the same structural integrity requirements as the automated methods, preventing the creation of disconnected or non-functional logic fragments.
            Logic:  # check nodes existance
                    __if not all(n in graph.nodes for n in selected_nodes): continue__
                    # check convexity
                    __if not is_selection_convex(graph, selected_nodes): continue__
        Visualization & Feedback Loop:
            Purpose: Provides immediate visual verification. By exporting the graph state before and after selection to *.gv* files, it bridges the gap between the user's textual input and the logical structure of the circuit.
            Logic: __export(graph, after_path, selected_nodes)__

    - # 100 - slash_to_kill
        Architecture Initialization:
            Purpose: Establishes a formal, typed environment for the circuit. By declaring Node and Edge as Datatypes, you enable the solver to perform attribute-based operations (ID, Weight, In-Subgraph) rather than managing large lists of disconnected Boolean variables.
            Logic:  __Node = Datatype('Node'); Node.declare('mk_node', ('id', BitVecSort), ('weight', BitVecSort),('in_subgraph', BoolSort))__
                    __Edge = Datatype('Edge'); Edge.declare('mk_edge', ('source', Node), ('target', Node))__

        Graph Data Ingestion:
            Purpose: Maps the physical circuit topology into the solver's memory. This phase initializes every node by binding its unique identity, weight properties, and initial subgraph membership status to a symbolic Node object.
            Logic: For each node in the graph, the solver registers the following constraints simultaneously to establish the node's formal state:
                # Identity Anchor: __Node.id(node) == BitVecVal(id, NUM_BITS)__
                # Weight Property: __Node.weight(node) == BitVecVal(weight, NUM_BITS)__
                # State Binding: __Node.in_subgraph(node) == BoolVal(False)__ (Locks external nodes/constants out of the partition scope)

        Symbolic Cut & Flow Constraints:
            Purpose: Detects boundary cuts dynamically. Instead of pre-calculating every edge, the solver evaluates the in_subgraph status of the source vs. target of every declared Edge object to identify entry/exit points and enforces bandwidth constraints.
            Logic:  # Boundary Detection:
                        + Outgoing Cut: __And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des])))__
                        + Incoming Cut: __And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des]))__
                    # Symbolic Counting: Uses an If statement to map boolean cut conditions to BitVec values for summation.
                        __If(Or(outgoing_conditions or incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))__
                    # Bandwidth Enforcement:
                        + Max Incoming: __opt.add(Sum(unique_incoming_edges) <= imax)__
                        + Max Outgoing: __opt.add(Sum(unique_outgoing_edges) <= omax)__

        Structural & Convexity Constraints:
            i) Descendant Consistency:
                Purpose: Ensures that if a signal path is broken at the boundary (source is in_subgraph, destination is out), no downstream nodes can be included in the subgraph. This prevents the solver from picking "floating" logic fragments downstream that have no connection to the partition's internal logic.
                Logic: __Implies(And(src_in, Not(des_in)), And(Not(descendants_in)))__

            ii) Ancestor Consistency:
                Purpose: Ensures that if a destination node is included in the subgraph while its source is not, no upstream nodes (ancestors) can be included. This prevents the solver from creating "spontaneously generated" logic fragments that are fed by external nodes not present in the subgraph.
                Logic: __Implies(And(Not(src_in), des_in), And(Not(ancestors_in)))__
        
        Structural Cohesion (Child-Consistency)
            Purpose: Enforces strict logical integrity for signal paths. If a parent node is included in the subgraph and at least one child node is also selected, the solver is forced to include all children. This prevents the solver from selecting "partial" logic paths, ensuring that if a signal starts propagating through a gate, the entire downstream branch must be captured.
            Logic: __Implies(And(Node.in_subgraph(parent), Or(children_in)), And(children_in))__

        Global Feasibility Budgeting
            Purpose: Implements a cumulative constraint on the interface cost. Instead of filtering individual edges against the threshold (which is binary/permissive), this method aggregates the weight of all boundary-crossing edges into a single feasibility_sum. This budget-based approach allows for flexible partitioning where a single high-weight boundary edge might be permitted as long as the total "cut cost" remains below the defined feasibility_threshold.
            Logic:  # Cost Aggregation: Sums the weights of all edges crossing the partition boundary
                    __feasibility_sum = Sum([ If(__
                        __And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),__
                        __Node.weight(Edge.source(edge)),__
                        __BitVecVal(0, NUM_BITS))__
                    __for edge in edges])__
                    # Global Budget Enforcement: Ensures the total interface cost is strictly bounded.
                    __opt.add(feasibility_sum <= BitVecVal(feasibility_threshold, NUM_BITS))__

        Optimization & Maximization Objective:
            Purpose: Guarantees the absolute maximum density of the subgraph. It employs a two-stage solver strategy: it finds the theoretical maximum (h.upper()) and, if the initial model falls short, forces a second pass to guarantee optimality.
            Logic:  __h = opt.maximize(Sum(max_nodes))__
                    __if correct_maximum != model_maximized: opt.add(Sum(max_nodes) == correct_maximum)__

        Structural Integrity Audit (Global Graph Context): 
            Purpose: Acts as the final safety auditor and translator. It ensures that the symbolic result from the solver is topologically sound (convex) and maps the internal Z3 identifiers back to the original graph's gate references.
            Logic:  # Integrity Audit: Discards any result that fails the connectivity test, raising a *RuntimeError* if the subgraph is non-convex.
                        __if not is_selection_convex(self.graph, node_partition): raise RuntimeError(...)__

===================================================================================================================================

#
--- 
Signal Propagation Constraints              | 1                                 |                        
(Basic/Structural)                          |                                   |
Logic Gates (AND/OR gates for cuts)

---
Signal Propagation Constraints              | 2, 3, 4, 5, 11                    |                        
(with Feasibility/Sensitivity Metadata)     |                                   |
Boundary Metadata (Weights + Constraint Mapping)

---
Signal Propagation Constraints              | 12                                |                        
(Penalty-based (Soft))                      |                                   |
Defines boundaries + computes numeric "penalty" costs for the solver

---
Symbolic State Propagation                  | 6, 55, 100                        |
(Constraints)                               |                                   |
It dynamically calculates boundary conditions based on the *in_subgraph* attribute of the *Node* datatype during the solver's execution.

#
---
Structural & Convexity Constraints          | 1, 2, 3, 4, 5, 11, 12             | 
(Path-Centric Convexity)                    |                                   |
Topology-based: Validates the integrity of logic paths and partition "cuts" to prevent the fragmentation of signal flows.

---
Structural & Convexity Constraints          | 6, 55, 100                        | 
(Node-Centric Convexity)                    |                                   |
Attribute-based: Validates the boolean *in_subgraph* state of individual nodes and their neighbors to ensure structural continuity.

#
---
Optimization and Selection Constraints      | 1, 2, 4, 5, 11, 12                |
(Boundary Bandwidth (imax/omax))            |                                   |

---
Optimization and Selection Constraints      | 1, 2, 3, 4, 5, 11, 12             |
(Mandatory Inactivity (skipped_nodes))      |                                   |

---
Optimization and Selection Constraints      | 1                                 |
(Utility Maximization (gate_weight))        |                                   |
Logic: *max_func.append(gate_literals[gate_id] * gate_weight[gate_id])*
        *opt.maximize(Sum(max_func))*

---
Optimization and Selection Constraints      | 2, 3, 4, 5, 11, 12                |
(Utility Maximization (gate_weight))        |                                   |
Logic: *max_func.append(gate_literals[gate_id])*
        *opt.maximize(Sum(max_func))*

#
---
Feasibility and Filtering Constraints       | 4, 5                              |
(Feasibility Threshold Filtering)           |                                   |
Logic: *feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold]*

---
Feasibility and Filtering Constraints       | 11, 12                            |
(Feasibility Threshold Filtering)           |                                   |
Logic: *feasibility_constraints = [edge_constraint(s) for s in edge_w if gate_weight(s) <= feasibility_threshold and gate_weight[s] != -1]*

---
Feasibility and Filtering Constraints       | 4, 11, 12                         |
(Minimum Feasibility Guarantee)             |                                   |
Logic: *opt.add(Sum(feasibility_constraints) >= 1)*

---
Feasibility and Filtering Constraints       | 5                                 |
(Strict Boundary Feasibility)               |                                   |
Logic: *opt.add(Sum(feasibility_constraints) == Sum(partition_output_edges))*

#
---
Optimization and Selection Constraints      | 1, 2, 3, 4, 11, 12                |
(Structural Integrity Audit                 |                                   |
(Local Graph Context))
Logic: *is_selection_convex(G, node_partition)*

---
Optimization and Selection Constraints      | 5, 6, 55, 100                     |
(Structural Integrity Audit                 |                                   |
(Global Graph Context))
Logic: *if not is_selection_convex(self.graph, node_partition): raise RuntimeError(...)*

#
---
Penalty-based Soft Constraints              | 11, 12                            |
(Penalty Modeling)                          |                                   |
Logic: *output_individual_penalty.append(If(gate_literals[s], penalty_coefficient * (gate_weight[s] - feasibility_treshold), 0))*

Penalty-based Soft Constraints              | 11                                |
(Soft Constraint Enforcement)               |                                   |
Logic: *opt.add_soft(Sum(output_individual_penalty) <= 2 * feasibility_treshold, weight=1)*

Penalty-based Soft Constraints              | 12                                |
(Soft Constraint Enforcement (Hierarchical))|                                   |
Logic:  *# High-priority constraint for interface modularity*
            *opt.add_soft(IntVal(1) * Sum(partition_output_edges_penalty) <= omax * threshold, weight=100)*
        *# Lower-priority constraint for internal gate density* 
            *opt.add_soft(IntVal(1) * Sum(output_individual_penalty) <= omax * threshold, weight=1)*

#
---
Multi-Partition Iteration Engine            | 11, 12                            |
(Partition Enumeration (Exhaustive Search)) |                                   |
Logic: uses a *while count > 0* loop to repeatedly query the solver for unique solutions

---
Multi-Partition Iteration Engine            | 11                                |
(Lowest Penalty Selection)                  |                                   |
Logic: *sorted(all_partitions.items(), key=lambda item: (-len(item[1][1]), item[1][0]))*

---
Multi-Partition Iteration Engine            | 12                                |
(Lowest Penalty Selection                   |                                   |
(Multi-Attribute Ranking))
Logic: *sorted(all_partitions.items(), key=lambda item: (-len(item[1][2]), item[1][0], item[1][1]))*

#
---
Sensitivity Budget Constraints              | 1, 2, 3                           |
(Weight Normalization)                      |                                   |
Logic: *gate_weight[id] = max_weight - gate_weight[id] + 1*

---
Sensitivity Budget Constraints              | 2, 3                              |
(Sensitivity Budgeting (Hard Constraint))   |                                   |
Logic: *opt.add(Sum([edge_constraint[s] * edge_w[s]]) <= sensitivity_t)*

#
---
Purpose-Logic Documentation                 | 6                                 |
(Weight Distribution Analysis)              |                                   |
Logic:  *# Linear Scaling: Creates 8 linearly spaced steps across the weight range.*
            *weights = sorted(frozenset(...)), partition_step = (max_weight - min_weight) / (8 - 1)*
            *linear_partition = [min_weight + partition_step * i for i in range(8)]*   
        *# Weight Mapping: Maps the linear steps to the actual nearest gate weights present in the circuit to avoid testing "impossible" thresholds.*
            *actual_partition = sorted(frozenset(min(weights, key=lambda w: abs(w - p)) for p in linear_partition))*

---
Purpose-Logic Documentation                 | 6                                 |
(Iterative Threshold Sweep)                 |                                   |
Logic: *for (i, specs_obj.et) in enumerate(actual_partition):*
       *subgraph_nodes = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)*

---
Purpose-Logic Documentation                 | 6                                 |
(State Restoration)                         |                                   |
Logic: *specs_obj.et = saved_et*

#
---
Graph Data Ingestion                        | 55, 100                           |
                                            |                                   |
Logic:  # Identity Anchor: *Node.id(node) == BitVecVal(id, NUM_BITS)*
        # Weight Property: *Node.weight(node) == BitVecVal(weight, NUM_BITS)*
        # State Binding: *Node.in_subgraph(node) == BoolVal(False)*

---
Symbolic Cut & Flow Constraints             | 55, 100                           |
                                            |                                   |
Logic:  # Boundary Detection:
            + Outgoing Cut: *And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des])))*
            + Incoming Cut: *And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des]))*
        # Symbolic Counting: Uses an If statement to map boolean cut conditions to BitVec values for summation.
            *If(Or(outgoing_conditions or incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))*
        # Bandwidth Enforcement:
            + Max Incoming: *opt.add(Sum(unique_incoming_edges) <= imax)*
            + Max Outgoing: *opt.add(Sum(unique_outgoing_edges) <= omax)*

---
Optimization & Maximization Objective       | 55, 100                           |
                                            |                                   |
Logic:  *h = opt.maximize(Sum(max_nodes))*
        *if correct_maximum != model_maximized: opt.add(Sum(max_nodes) == correct_maximum)*

---
Formal Feasibility Filter                   | 55                                |
                                            |                                   |
Logic: *opt.add(And([Implies*
            *(And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),*
            *Node.weight(Edge.source(edge)) <= BitVecVal(feasibility_threshold, NUM_BITS))]))*

---
Structural Cohesion (Child-Consistency)     | 100                               |
                                            |                                   |
Logic: *Implies(And(Node.in_subgraph(parent), Or(children_in)), And(children_in))*

---
Global Feasibility Budgeting                | 100                               |
                                            |                                   |
Logic:  # Cost Aggregation: Sums the weights of all edges crossing the partition boundary
            *feasibility_sum = Sum([ If(*
                *And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),*
                *Node.weight(Edge.source(edge)),*
                *BitVecVal(0, NUM_BITS))*
            *for edge in edges])*
        # Global Budget Enforcement: Ensures the total interface cost is strictly bounded.
            *opt.add(feasibility_sum <= BitVecVal(feasibility_threshold, NUM_BITS))*

===================================================================================================================================