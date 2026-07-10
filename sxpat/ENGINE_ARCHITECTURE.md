# Part 1: Component Library
- __Signal Propagation Constraints__
    Defines the logical entry and exit points for subgraphs and enforces signal flow validity. This component maps the physical topology of the circuit into a verifiable logical format.

    Core Mechanisms & Constraints:
    i) Input -> Gate Boundary
        Purpose: Defines the entry points into the partition. An input edge is part of the boundary if the source (external input) is False but the target (internal gate) is True.
    ii) Gate <-> Gate Cut (*Bidirectional*)
            - Input-side Cut: Identifies edges entering the sub-graph. A cut exists if the source gate is False (inactive) and the destination gate is True (active).
            - Output-side Cut: Identifies edges exiting the sub-graph. A cut exists if the source gate is True (active) and the destination gate is False (inactive).
    iii) Gate -> Output Boundary:
        Purpose: Validates the exit point where internal logic connects to an external output node.

- __Convexity and Structural Constraints__
    Maintains logical soundness and topological continuity within subgraphs. This component ensures that partitions are free from "broken" signal paths or spontaneously generated logic.

    Core Mechanisms & Constraints:
    i) Descendant Consistency:
        Purpose -> If a signal is blocked at the destination node, all logical descendants must be forced to an inactive state (False). This prevents "broken" signal paths within the partition.
    ii) Ancestor Consistency:
        Purpose -> If a signal appears at a destination while the source is inactive, the logic propagates False upstream to all ancestors. This ensures the partition does not contain "spontaneously generated" logic.

- __Optimization and Selection Constraints__
    Governs the selection criteria and performance goals for subgraph extraction, allowing the solver to balance structural modularity with the inclusion of high-value logic gates.

    Core Mechanisms & Constraints:
    i) Boundary Bandwidth Control:
        Purpose: Limits the "interface bandwidth" of the subgraph. It forces the solver to find a clean, modular cut with a restricted number of external connections.
    ii) Utility Maximization:
        Purpose: The solver prioritizes nodes with higher weight values. By maximizing this sum, the engine selects the most "critical" or "valuable" logic gates that still satisfy the integrity constraints.
    iii) Mandatory Inactivity (Skip-Logic):
        Purpose: Explicitly excludes designated nodes (e.g., nodes marked with a specific weight identifier) from the partitioning process.
    iv) Structural Integrity Integration:
        Purpose: Ensures that even during the optimization phase, the partition adheres to convexity and continuity requirements established by the core integrity modules.

- __Sensitivity Budget Constraints__
    Manages the accumulation of sensitivity metrics across the partition boundary, ensuring that the selected subgraph remains within defined operational exposure limits.

    Core Mechanisms & Constraints:
    i) Sensitivity Budgeting (Hard Constraint):
        Purpose: Imposes a strict "hard budget" on the total accumulated sensitivity, acting as a safeguard to prevent the selection of partitions that exceed critical exposure thresholds.
    ii) Weight Normalization:
        Purpose: Re-calculates gate weights to favor the inclusion of high-value (critical) logic. By inversely scaling weights, this mechanism makes high-priority gates "cheaper" to fit within the sensitivity budget.

- __Feasibility and Filtering Constraints__
    Defines the rules for identifying "safe-to-cut" boundaries within the circuit, ensuring that extracted subgraphs meet defined feasibility and connectivity criteria.

    Core Mechanisms & Constraints:
    i) Feasibility Threshold Filtering:
        Purpose: Identifies "safe-to-cut" interface edges by qualifying them based on weight thresholds. Beyond the standard weight threshold check, this mechanism implicitly applies Mandatory Inactivity (Skip-Logic) filters. Any gate marked with a specific weight identifier (e.g., -1) is automatically excluded from the eligibility pool, ensuring that only "active" and "weight-compliant" gates serve as valid boundary points.
    ii) Feasibility Enforcement Strategies:
            - Strategy A (Minimum Guarantee): Forces the partition to contain at least one interface point meeting the threshold, preventing the extraction of overly isolated or "locked" logic blocks.
            - Strategy B (Strict Boundary): Enforces an absolute constraint where all output edges must originate from feasible gates. This acts as a "zero-tolerance" mode for boundary integrity; if a cut cannot be formed purely by feasible gates, the solver returns no solution.

- __Penalty-based Soft Constraints__
    Introduces flexibility into the feasibility boundary by treating requirements as optimization goals rather than hard logical constraints. This allows the solver to balance modularity against internal density.

    Core Mechanisms & Constraints:
    i) Penalty Modeling:
        Purpose: To create a "soft" boundary for feasibility. By differentiating between interface (output) costs and internal (gate) costs, the solver can prioritize modular connections over internal gate weight.
    ii) Soft Constraint Enforcement:
            - Strategy A (Flexible Goal): Treats the feasibility boundary as a general optimization objective (weight = 1), allowing for minor deviations if necessary to find a valid solution.
            - Strategy B (Hierarchical): Establishes a priority hierarchy to manage conflicting goals.
                High-Priority (weight = 100): Treats interface modularity as a critical requirement.
                Low-Priority (weight = 1): Treats internal gate density as a secondary, flexible optimization goal.

- __Multi-Partition Iteration Engine__
    Orchestrates the exhaustive discovery of valid subgraphs and performs multi-criteria ranking to select the most effective partition.

    Core Mechanisms & Constraints:
    i) Partition Enumeration (Exhaustive Search):
        Purpose: Enables the discovery of multiple unique valid partitions by iteratively extracting solutions and applying blocking clauses to prevent the solver from finding the same partition twice.
    ii) Lowest Penalty Selection:
            - Strategy A (Balanced Penalty Ranking): Sorts partitions based on cost and size to balance logical density against the feasibility threshold.
            - Strategy B (Multi-Attribute Hierarchical Ranking): Implements a comprehensive post-processing hierarchy to optimize for three distinct criteria: partition size (maximization), output interface cost (minimization), and internal gate cost (minimization).

- __Search Space Calibration & State Management__
    Orchestrates the adaptive search process by normalizing the problem space and ensuring functional isolation of the solver's state.

    Core Mechanisms & Constraints:
    i) Weight Distribution Analysis:
        Purpose: Dynamically calibrates the feasibility search space by analyzing the range of gate weights unique to the current circuit instance. It then discretizes the weight range into representative threshold levels, mapping them to actual gate weights to avoid testing invalid search parameters.
    ii) Iterative Threshold Sweep:
        Purpose: Implements a coarse-to-fine search by testing 8 discretized threshold levels (actual_partition). It attempts to extract a valid subgraph starting from the lowest threshold level, ensuring the most restrictive (and often most conservative/safe) feasible partition is found first.
    iii) State Restoration:
        Purpose: Guarantees functional atomicity by reverting the specifications object to its original configuration after execution, effectively preventing side effects within the engine.

- __Symbolic Topology Management__
    Establishes the formal, typed environment for circuit representation and enforces topological soundness at the node level. This component maps physical circuit topology into a verifiable symbolic format for the solver.

    Core Mechanisms & Constraints:
    i) Architecture Initialization:
        Purpose: Establishes a formal, typed environment for the circuit. By declaring Node and Edge as symbolic datatypes, it enables the solver to perform attribute-based operations (ID, Weight, Subgraph-Membership) rather than managing raw lists of variables.
    ii) Graph Data Ingestion:
        Purpose: Maps the physical circuit topology into the solver's memory. This phase initializes every node by binding its unique identity, weight properties, and initial subgraph membership status to a symbolic object. Mechanism: Registers identity anchors and state bindings simultaneously to establish the node's formal symbolic state.
    iii) Symbolic Cut & Flow Analysis:
        Purpose: Detects boundary cuts dynamically. Instead of pre-calculating every edge, the solver evaluates the in_subgraph status of the source vs. target of every declared Edge object to identify entry/exit points and enforces bandwidth constraints.
    iv) Node-Level Structural Integrity:
        Purpose: Maintains topological consistency by enforcing convexity constraints (Descendant and Ancestor Consistency) to prevent floating logic or spontaneously generated fragments.
    v) Formal Feasibility Filter:
        Purpose: Enforces an absolute constraint where boundary edges are only permissible if the source gate meets the feasibility_threshold. This is a symbolic verification of the signal path's integrity at the partition boundary.
    vi) Optimization & Maximization Objective:
        Purpose: Guarantees the absolute maximum density of the subgraph. It employs a two-stage solver strategy: it finds the theoretical maximum (h.upper()) and, if the initial model falls short, forces a second pass to guarantee optimality.
    vii) Structural Integrity Audit (Global Graph Context)
        Purpose: Acts as the final safety auditor and translator. It ensures that the symbolic result from the solver is topologically sound (convex) and maps the internal Z3 identifiers back to the original graph's gate references.
    ix) Structural Cohesion (Child-Consistency):
        Purpose: Enforces strict logical integrity for signal paths. If a parent node is included in the subgraph and at least one child node is also selected, the solver is forced to include all children. This prevents the solver from selecting "partial" logic paths, ensuring that if a signal starts propagating through a gate, the entire downstream branch must be captured.
    x) Global Feasibility Budgeting:
        Purpose: Implements a cumulative constraint on the interface cost. Instead of filtering individual edges against the threshold (which is binary/permissive), this method aggregates the weight of all boundary-crossing edges into a single feasibility_sum. This budget-based approach allows for flexible partitioning where a single high-weight boundary edge might be permitted as long as the total "cut cost" remains below the defined feasibility_threshold.
    
- __Interactive & Diagnostic Tools__
    Provides a manual interface for circuit exploration and subgraph definition, enabling direct user intervention outside of the automated solver loop. This component bridges the gap between manual prototyping and the formal integrity requirements of the engine, ensuring that all user-selected subgraphs remain topologically valid and functional.

    Core Mechanisms & Constraints:
    i) Interactive Selection Loop:
        Purpose: Provides complete control to the user, bypassing the solver logic. This allows for manual prototyping, debugging, or creating specific subgraphs that the solver might struggle to find.
    ii) Validation & Topological Guardrails:
        Purpose: Ensures the manual selection adheres to the same structural integrity requirements as the automated methods, preventing the creation of disconnected or non-functional logic fragments.
            - Logic (Existence): Validates node presence within the graph.
            - Logic (Convexity): Enforces convex selection criteria.
    iii) Visualization & Feedback Loop:
        Purpose: Provides immediate visual verification. By exporting the graph state before and after selection to *.gv* files, it bridges the gap between the user's textual input and the logical structure of the circuit.

# Part 2: Algorithm Catalog
- __Algorithm 1: find_subgraph__
    Description: Identifies and extracts a maximally weighted convex subgraph from the circuit. It formulates the extraction as a constraint satisfaction and optimization problem, using SMT solvers to ensure convexity, boundary constraints (*imax, omax*), and weighted gate inclusion.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Optimization and Selection Constraints (i, ii, iii, iv)
    + Sensitivity Budget Constraints (ii)

- __Algorithm 2: find_subgraph_sensitivity__
    Description: Extracts a functional subgraph by optimizing for maximum gate inclusion while strictly enforcing a global sensitivity budget (*sensitivity_t*). Unlike standard extraction, this algorithm weights the edges based on gate importance and uses an SMT solver to ensure the total cumulative sensitivity of the partitioned sub-circuit remains within the specified threshold, maintaining structural integrity through convexity constraints.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Optimization and Selection Constraints (i, ii, iii, iv)
    + Sensitivity Budget Constraints (i, ii)

- __Algorithm 3: find_subgraph_sensitivity_no_io_constraints__
    Description: A specialized subgraph extraction algorithm that focuses exclusively on satisfying the global sensitivity budget (*sensitivity_t*) while maintaining structural convexity. By removing specific constraints on the number of input/output edges (*imax, omax*), this algorithm provides more flexibility in partition sizing, prioritizing the preservation of critical logic blocks within the sensitivity threshold.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Optimization and Selection Constraints (ii, iii, iv)
    + Sensitivity Budget Constraints (i, ii)

- __Algorithm 4: find_subgraph_feasible__
    Description: Extracts a subgraph by filtering components based on a specific feasibility threshold (*et*). The algorithm evaluates node weights against this threshold to select valid gates, ensuring that the resulting partition is both structurally convex and compliant with connectivity constraints (*imax, omax*). It focuses on including only those logic blocks that meet the defined performance or feasibility criteria.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Feasibility and Filtering Constraints (i, ii-Strategy A)
    + Optimization and Selection Constraints (i, ii, iii, iv)

- __Algorithm 5: find_subgraph_feasible_hard__
    Description: A strict variant of the feasibility-based extraction algorithm. It enforces a "hard" constraint where the sum of selected feasible edge constraints must exactly equal the sum of the subgraph's output edges (*Sum(feasibility_constraints) == Sum(partition_output_edges)*). This ensures that every exit point of the partition is rigorously validated against the feasibility threshold (*et*), guaranteeing that only high-integrity logic blocks are extracted.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Feasibility and Filtering Constraints (i, ii-Strategy B)
    + Optimization and Selection Constraints (i, ii, iii, iv)

- __Algorithm 55: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec__
    Description: A high-precision extraction algorithm that integrates symbolic topological modeling with strict interface bandwidth constraints. By utilizing Datatype and BitVec for binary node and edge representation, it enforces rigid input/output limits (*imax / omax*) and filters interface edges through a strict feasibility threshold condition. The algorithm ensures robust gate density optimization within predefined structural and interface constraints, with all logic natively integrated into the symbolic topology.

    Components Utilized:
    + Symbolic Topology Management(i, ii, iii, iv, v, vi, vii)

- __Algorithm 6: find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold__
    Description: A meta-algorithm that automates the selection of an optimal feasibility threshold (*et*). It performs a linear partition of the graph's weight distribution into eight representative intervals and iteratively executes *Algorithm 55* across these intervals to identify the most suitable threshold. By dynamically calibrating the feasibility constraint, this algorithm ensures successful subgraph extraction even when the initial threshold is overly restrictive, effectively acting as an automated wrapper for *Algorithm 55*.

    Components Utilized:
    + Search Space Calibration & State Management(i, ii, iii)
    + Symbolic Topology Management (relies on Algorithm 55)

- __Algorithm 100: slash_to_kill__
    Description: A high-precision subgraph extraction algorithm that leverages Z3 custom Datatypes and BitVector logic to model circuit nodes and edges. It implements a rigorous constraint satisfaction approach where "cutting" edges (slashing) is evaluated against a bit-width constrained feasibility threshold. By encoding topology into symbolic structures, it enforces strict structural integrity, including mandatory child-inclusion rules for parent gates and exhaustive convexity validation, making it suitable for complex, constraint-heavy logic pruning.

    Components Utilized:
    + Symbolic Topology Management(i, ii, iii, iv, vi, vii, ix, x)

- __Algorithm 11: find_subgraph_feasible_soft__
    Description: A flexible subgraph extraction algorithm that implements a "soft" feasibility model. Instead of strictly rejecting nodes exceeding the feasibility threshold (*et*), it calculates a penalty cost for these violations and uses *opt.add_soft* to minimize the overall penalty while maximizing the subgraph size. The algorithm employs a multi-pass iteration engine to explore and rank multiple potential partitions, ultimately selecting the one that best balances size and penalty.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Feasibility and Filtering Constraints (i, ii-Strategy A)
    + Optimization and Selection Constraints (i, ii, iii, iv)
    + Penalty-based Soft Constraints (i, ii-Strategy A)
    + Multi-Partition Iteration Engine (i, ii-Strategy A)

- __Algorithm 12: find_subgraph_feasible_soft_outputs__
    Description: An advanced subgraph extraction algorithm that refines the "soft" feasibility approach by introducing dual-penalty metrics: one for internal gate violations and one specifically for output-edge feasibility violations. It balances subgraph size against these combined output and gate penalties, using a multi-pass optimization to rank candidate partitions based on size and penalty minimization. This approach is ideal for circuits where output signal integrity is as critical as internal gate feasibility.

    Components Utilized:
    + Signal Propagation Constraints
    + Convexity and Structural Constraints
    + Feasibility and Filtering Constraints (i, ii-Strategy A)
    + Optimization and Selection Constraints (i, ii, iii, iv)
    + Penalty-based Soft Constraints (i, ii-Strategy B)
    + Multi-Partition Iteration Engine (i, ii-Strategy B)
    
- __Algorithm 42: extract__
    Description: An interactive diagnostic utility that allows users to manually define a subgraph through a command-line interface. The tool visualizes the original graph via *Graphviz*, validates the user's manual selection for node existence and convexity compliance, and provides a confirmation preview before finalizing the extraction. It serves as a verification tool for manually validating subgraph selections against structural rules.
    
    Components Utilized:
    + Interactive & Diagnostic Tools(i, ii, iii)
    