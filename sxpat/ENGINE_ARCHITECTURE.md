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