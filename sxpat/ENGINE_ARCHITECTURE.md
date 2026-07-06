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