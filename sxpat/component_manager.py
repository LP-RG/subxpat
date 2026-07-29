from typing import Dict, List, Tuple, Optional, Any
import networkx as nx
from z3 import Optimize, BoolRef, ArithRef, ExprRef, DatatypeSortRef

from sxpat.Component_Library.signal_propagation_constraints_minimal import (
    SignalPropagationConstraintsMinimal,
)
from sxpat.Component_Library.signal_propagation_constraints_with_penalty import (
    PenaltyPropagation,
)
from sxpat.Component_Library.signal_propagation_constraints import (
    SignalPropagationConstraints,
)
from sxpat.Component_Library.convexity_and_structural_constraints import (
    ConvexityConstraints,
)
from sxpat.Component_Library.optimization_and_selection_constraints import (
    OptimizationConstraints,
)
from sxpat.Component_Library.sensitivity_budget_constraints import (
    SensitivityBudgetConstraints,
)
from sxpat.Component_Library.feasibility_and_filtering_constraints import (
    FeasibilityConstraints,
)
from sxpat.Component_Library.penalty_based_soft_constraints import (
    PenaltyConstraints,
)
from sxpat.Component_Library.model_initialization import (
    ModelInitialization,
)
from sxpat.Component_Library.multi_partition_iteration_engine import (
    MultiPartitionIterationEngine,
)
from sxpat.Component_Library.bitvector_topology_management import (
    BitvectorTopologyManagement,
)

class ComponentManager:
    @staticmethod
    def get_signal_propagation_minimal(
        input_edges: Dict[int, List[int]],
        gate_edges: Dict[int, List[int]],
        output_edges: Dict[int, List[int]],
        input_literals: Dict[int, BoolRef],
        gate_literals: Dict[int, BoolRef],
        output_literals: Dict[int, BoolRef],
    ) -> Tuple[List[BoolRef], List[BoolRef]]:
        
        """
        Defines the minimal logical entry and exit points for subgraphs.

        Args:
            input_edges: Dictionary mapping input nodes to connected gate IDs.
            gate_edges: Dictionary mapping gate IDs to successor gate IDs.
            output_edges: Dictionary mapping output nodes to predecessor gate IDs.
            input_literals: Z3 boolean literals for input nodes.
            gate_literals: Z3 boolean literals for gate nodes.
            output_literals: Z3 boolean literals for output nodes.
        """

        return SignalPropagationConstraintsMinimal.define_constraints(
            input_edges,
            gate_edges,
            output_edges,
            input_literals,
            gate_literals,
            output_literals,
        )

    @staticmethod
    def get_signal_propagation_with_penalty(
        input_edges: Dict[int, List[int]],
        gate_edges: Dict[int, List[int]],
        output_edges: Dict[int, List[int]],
        input_literals: Dict[int, BoolRef],
        gate_literals: Dict[int, BoolRef],
        output_literals: Dict[int, BoolRef],
        tmp_graph: nx.DiGraph,
        gate_dict: Dict[int, str],
        WEIGHT: str,
        feasibility_threshold: int,
    ) -> Tuple[
        List[BoolRef], List[BoolRef], List[Any], Dict[int, int], Dict[int, BoolRef]
    ]:
        
        """
        Defines signal propagation constraints with built-in penalty modeling for soft constraints.

        Args:
            input_edges, gate_edges, output_edges: Structure of the graph edges.
            input_literals, gate_literals, output_literals: Z3 variables corresponding to the nodes.
            tmp_graph: Directed graph of the circuit.
            gate_dict: Mapping of gate IDs to their string labels.
            WEIGHT: The string key used for weight attributes.
            feasibility_threshold: Threshold limit for feasibility calculations.
        """

        return PenaltyPropagation.define_with_penalties(
            input_edges,
            gate_edges,
            output_edges,
            input_literals,
            gate_literals,
            output_literals,
            tmp_graph,
            gate_dict,
            WEIGHT,
            feasibility_threshold,
        )

    @staticmethod
    def get_signal_propagation(
        input_edges: Dict[int, List[int]],
        gate_edges: Dict[int, List[int]],
        output_edges: Dict[int, List[int]],
        input_literals: Dict[int, BoolRef],
        gate_literals: Dict[int, BoolRef],
        output_literals: Dict[int, BoolRef],
        tmp_graph: nx.DiGraph,
        gate_dict: Dict[int, str],
        WEIGHT: str,
    ) -> Tuple[List[BoolRef], List[BoolRef], Dict[int, int], Dict[int, BoolRef]]:
        
        """
        Defines the structural constraints mapping the physical circuit topology into a symbolic logical format.

        Args:
            input_edges, gate_edges, output_edges: Structure of the graph edges.
            input_literals, gate_literals, output_literals: Z3 variables corresponding to the nodes.
            tmp_graph: The networkx circuit graph.
            gate_dict: Dictionary resolving gate indices to graph node names.
            weight: The string key used for weight attributes.
        """

        return SignalPropagationConstraints.define_structural_constraints(
            input_edges,
            gate_edges,
            output_edges,
            input_literals,
            gate_literals,
            output_literals,
            tmp_graph,
            gate_dict,
            WEIGHT,
        )

    @staticmethod
    def add_convexity(
        opt: Optimize,
        G: nx.DiGraph,
        gate_literals: Dict[int, BoolRef],
        gate_edges: Dict[int, List[int]],
    ) -> None:
        
        """
        Maintains logical soundness and topological continuity within subgraphs (convexity).

        Args:
            opt: Z3 Optimizer instance.
            G: The directed graph of internal gates.
            gate_literals: Z3 boolean literals mapping for gates.
            gate_edges: Dictionary containing successors for each gate.
        """

        ConvexityConstraints.add_convexity_constraints(
            opt, G, gate_literals, gate_edges
        )

    @staticmethod
    def add_io_limits(
        opt: Optimize,
        imax: int,
        omax: int,
        partition_input_edges: List[BoolRef],
        partition_output_edges: List[BoolRef],
    ) -> None:
        
        """
        Limits the interface bandwidth of the subgraph by enforcing boundary restrictions.

        Args:
            opt: Z3 Optimizer instance.
            imax: Maximum allowed input connections.
            omax: Maximum allowed output connections.
            partition_input_edges: List of symbolic partition input edges.
            partition_output_edges: List of symbolic partition output edges.
        """

        OptimizationConstraints.add_io_limits(
            opt, imax, omax, partition_input_edges, partition_output_edges
        )

    @staticmethod
    def add_maximization(
        opt: Optimize,
        gate_literals: Dict[int, BoolRef],
        gate_weight: Optional[Dict[int, int]],
    ) -> None:
        
        """
        Prioritizes the selection of high-value logic gates.

        Args:
            opt: Z3 Optimizer instance.
            gate_literals: Z3 boolean literals mapping for gates.
            gate_weight: Optional dictionary of weights. If None, default weight is 1.
        """

        OptimizationConstraints.add_maximization(opt, gate_literals, gate_weight)

    @staticmethod
    def exclude_skipped_nodes(opt: Optimize, graph: nx.DiGraph) -> None:

        """
        Explicitly excludes designated nodes (Mandatory Inactivity) from the partition.

        Args:
            opt: Z3 Optimizer instance.
            graph: The annotated networkx graph.
        """

        OptimizationConstraints.exclude_skipped_nodes(opt, graph)

    @staticmethod
    def check_convexity(
        opt: Optimize, G: nx.DiGraph, gate_dict: Dict[int, str]
    ) -> List[str]:

        """
        Runs the optimizer and guarantees maximum density and structural integrity.

        Args:
            opt: Z3 Optimizer instance.
            G: Directed graph of gates.
            gate_dict: Mapping of gate IDs to string labels.
        """
        
        return OptimizationConstraints.check_convexity(opt, G, gate_dict)

    @staticmethod
    def validate_selection_convexity(G: nx.DiGraph, node_partition: List[int]) -> None:

        """
        Validates manual or pre-calculated node selection for topological convexity.

        Args:
            G: Directed graph of gates.
            node_partition: List of node IDs representing the partition.
        """

        OptimizationConstraints.validate_selection_convexity(G, node_partition)

    @staticmethod
    def add_sensitivity_budget(
        opt: Optimize,
        edge_w: Dict[int, int],
        edge_constraint: Dict[int, BoolRef],
        sensitivity_t: int,
    ) -> None:

        """
        Imposes a strict budget on the total accumulated sensitivity.

        Args:
            opt: Z3 Optimizer instance.
            edge_w: Dictionary containing edge weights.
            edge_constraint: Dictionary of logical constraints representing the cut edges.
            sensitivity_t: Global sensitivity budget threshold.
        """
        
        SensitivityBudgetConstraints.add_budget_constraints(
            opt, edge_w, edge_constraint, sensitivity_t
        )

    @staticmethod
    def prepare_gate_weights(
        G: nx.DiGraph, tmp_graph: nx.DiGraph, gate_dict: Dict[int, str], weight_key: str
    ) -> Dict[int, int]:

        """
        Normalizes and prepares gate weights to favor inclusion of critical logic.

        Args:
            G: Directed gate graph.
            tmp_graph: Full annotated networkx graph.
            gate_dict: Gate ID to string mapping.
            weight_key: String key for accessing weight properties.
        """
        
        return SensitivityBudgetConstraints.prepare_gate_weights(
            G, tmp_graph, gate_dict, weight_key
        )

    @staticmethod
    def get_feasibility(
        edge_w: Dict[int, int],
        gate_weight: Dict[int, int],
        feasibility_treshold: int,
        edge_constraint: Dict[int, BoolRef],
        strict: bool = True,
    ) -> List[BoolRef]:

        """
        Identifies interface edges based on weight thresholds.

        Args:
            edge_w: Edge weight dictionary.
            gate_weight: Gate weight dictionary.
            feasibility_treshold: The specific feasibility limit.
            edge_constraint: Logical edge selection constraints.
            strict: If True, rigorously excludes all out-of-bounds nodes.
        """
        
        return FeasibilityConstraints.get_feasibility_constraints(
            edge_w, gate_weight, feasibility_treshold, edge_constraint, strict=strict
        )

    @staticmethod
    def add_feasibility_logic(
        opt: Optimize,
        feasibility_constraints: List[BoolRef],
        partition_output_edges: Optional[List[BoolRef]] = None,
        mode: str = "at_least_one",
    ) -> None:

        """
        Defines filtering rules for identifying "safe-to-cut" boundaries in the circuit.

        Args:
            opt: Z3 Optimizer instance.
            feasibility_constraints: List of logic constraints dictating feasibility.
            partition_output_edges: Required if mode is 'match_outputs'.
            mode: Enforcement strategy ('at_least_one' or 'match_outputs').
        """
        
        FeasibilityConstraints.get_feasibility_logic(
            opt, feasibility_constraints, partition_output_edges, mode
        )

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

        Args:
            edge_w: Edge weight dictionary.
            gate_weight: Gate weight dictionary.
            feasibility_treshold: Limit threshold.
            gate_literals: Symbolic Z3 mapping of active gates.
            penalty_coefficient: Scaling factor for the penalty score.
        """
        
        return PenaltyConstraints.get_penalty_terms(
            edge_w,
            gate_weight,
            feasibility_treshold,
            gate_literals,
            penalty_coefficient,
        )

    @staticmethod
    def apply_penalty(
        opt: Optimize,
        penalty: ArithRef,
        output_individual_penalty: List[Any],
        soft_limit: int,
        weight: int = 1,
    ) -> None:

        """
        Applies a flexible penalty constraint to balance modularity against feasibility deviations.

        Args:
            opt: Z3 Optimizer instance.
            penalty: Z3 Arithmetic variable to track penalty sum.
            output_individual_penalty: List of calculated penalty components.
            soft_limit: Upper limit to trigger penalty weighting.
            weight: Priority multiplier.
        """
        
        PenaltyConstraints.apply_penalty_constraints(
            opt, penalty, output_individual_penalty, soft_limit, weight
        )

    @staticmethod
    def prepare_circuit_model(
        tmp_graph: nx.DiGraph, constant_dict: Dict[int, str]
    ) -> Tuple[
        Dict[int, BoolRef],
        Dict[int, BoolRef],
        Dict[int, BoolRef],
        Dict[int, List[int]],
        Dict[int, List[int]],
        Dict[int, List[int]],
    ]:

        """
        Initializes literals and edge structures to map the physical topology to a symbolic format.

        Args:
            tmp_graph: Directed graph of the complete circuit.
            constant_dict: Map of constant variables to ignore.
        """

        return ModelInitialization.prepare_circuit_model(tmp_graph, constant_dict)

    @staticmethod
    def build_gate_graph(
        tmp_graph: nx.DiGraph, constant_dict: Dict[int, str]
    ) -> nx.DiGraph:

        """
        Creates the directed graph of the internal circuit excluding I/O nodes.

        Args:
            tmp_graph: Original complete networkx circuit graph.
            constant_dict: Map of constant variables.
        """
        
        return ModelInitialization.build_gate_graph(tmp_graph, constant_dict)

    @staticmethod
    def add_boundary_conditions(
        opt: Optimize,
        input_literals: Dict[int, BoolRef],
        output_literals: Dict[int, BoolRef],
    ) -> None:

        """
        Sets inputs and outputs boundaries to False ensuring isolated internal graph analysis.

        Args:
            opt: Z3 Optimizer instance.
            input_literals: Dictionary of symbolic input boundaries.
            output_literals: Dictionary of symbolic output boundaries.
        """
        
        ModelInitialization.add_boundary_conditions(
            opt, input_literals, output_literals
        )

    @staticmethod
    def extract_gate_weights(
        G: nx.DiGraph, tmp_graph: nx.DiGraph, gate_dict: Dict[int, str], weight_key: str
    ) -> Dict[int, int]:

        """
        Extracts unmodified gate weights from the network graph.

        Args:
            G: Directed gate graph.
            tmp_graph: Full annotated network graph.
            gate_dict: Gate ID resolution dictionary.
            weight_key: Node attribute string key for weights.
        """
        
        return ModelInitialization.extract_gate_weights(
            G, tmp_graph, gate_dict, weight_key
        )

    @staticmethod
    def extract_multiple_subgraphs(
        opt: Optimize,
        G: nx.DiGraph,
        specs_obj: Any,
        mode: str = "multi",
        penalty: Optional[ArithRef] = None,
    ) -> List[Any]:

        """
        Orchestrates iterative discovery of valid subgraphs using blocking clauses.

        Args:
            opt: Z3 Optimizer instance.
            G: Networkx directed gate graph.
            specs_obj: Specifications instance controlling constraints.
            mode: Extraction iteration rule ('multi' or 'single').
            penalty: Optional Z3 variable tracking the penalty score.
        """

        return MultiPartitionIterationEngine.extract_multiple_subgraphs(
            opt, G, specs_obj, mode=mode, penalty=penalty
        )

    @staticmethod
    def select_best_partition(all_partitions: List[Any], mode: str = "multi") -> Tuple:

        """
        Sorts and selects the optimal partition balancing cost and modularity size.

        Args:
            all_partitions: Discovered subgraphs.
            mode: The active selection hierarchy.
        """

        return MultiPartitionIterationEngine.select_best_partition(
            all_partitions, mode=mode
        )

    @staticmethod
    def datatype_model_initialization(
        graph: nx.DiGraph,
        weight_key: str,
        input_dict: Dict[int, str],
        gate_dict: Dict[int, str],
        output_dict: Dict[int, str],
        constant_dict: Dict[int, str],
        opt: Optimize,
        num_outputs: int,
        num_gates: int,
    ) -> Tuple[DatatypeSortRef, DatatypeSortRef, Dict[int, Any], Dict[Tuple[int, int], Any], int]:
        
        """
        Establishes a formally typed BitVector/Datatype environment for topological mapping.

        Args:
            graph: Original network graph.
            weight_key: Dictionary key defining weights.
            input_dict, gate_dict, output_dict, constant_dict: Topology mapping elements.
            opt: Z3 Optimizer instance.
            num_outputs, num_gates: Size metadata for BitVector configuration.

        Returns:
            Tuple: (NodeSort, EdgeSort, node_variables, edge_variables, BitVector_width)
        """

        return BitvectorTopologyManagement.datatype_model_initialization(
            graph,
            weight_key,
            input_dict,
            gate_dict,
            output_dict,
            constant_dict,
            opt,
            num_outputs,
            num_gates,
        )

    @staticmethod
    def datatype_signal_propagation_constraints(
        graph: nx.DiGraph, nodes: Dict[int, Any], Node: DatatypeSortRef, NUM_BITS: int
    ) -> Tuple[Any, Any, Any]:

        """
        Enforces binary representation of entry/exit points (bandwidth).

        Args:
            graph: Directed topology graph.
            nodes: Symbolic mapping of gates.
            Node: The Z3 Datatype reference for Nodes.
            NUM_BITS: Target architecture bit vector width.
        """
        
        return BitvectorTopologyManagement.datatype_signal_propagation_constraints(
            graph, nodes, Node, NUM_BITS
        )

    @staticmethod
    def datatype_convexity_and_structural_constraints(
        graph: nx.DiGraph, nodes: Dict[int, Any], Node: DatatypeSortRef, opt: Optimize
    ) -> None:

        """
        Applies convexity checking against Datatype logic structures to prevent logic gaps.

        Args:
            graph: Topologic network graph.
            nodes: Dictionary mapping integers to Node datatypes.
            Node: Datatype definition for nodes.
            opt: Z3 optimizer instance.
        """
        
        BitvectorTopologyManagement.datatype_convexity_and_structural_constraints(
            graph, nodes, Node, opt
        )

    @staticmethod
    def datatype_optimization_and_selection_constraints(
        opt: Optimize,
        max_nodes: Any,
        graph: nx.DiGraph,
        gate_dict: Dict[int, str],
        imax: Optional[int] = None,
        omax: Optional[int] = None,
        unique_incoming_edges: Optional[Any] = None,
        unique_outgoing_edges: Optional[Any] = None,
        apply_io_limits: bool = False,
    ) -> List[str]:

        """
        Runs optimization across bitvector representations and fetches formal model structures.

        Args:
            opt: Z3 optimizer instance.
            max_nodes: The expression identifying maximum possible logic density.
            graph: Directed network topology.
            gate_dict: Mapping for gate string resolutions.
            imax, omax: Hardware port limits.
            unique_incoming_edges, unique_outgoing_edges: Edge vectors for boundaries.
            apply_io_limits: True if constraints need to restrict boundary width.
        """
        
        return (
            BitvectorTopologyManagement.datatype_optimization_and_selection_constraints(
                opt,
                max_nodes,
                graph,
                gate_dict,
                imax,
                omax,
                unique_incoming_edges,
                unique_outgoing_edges,
                apply_io_limits,
            )
        )

    @staticmethod
    def datatype_feasibility_and_filtering_constraints(
        edges: Dict[Tuple[int, int], Any],
        Node: DatatypeSortRef,
        Edge: DatatypeSortRef,
        NUM_BITS: int,
        feasibility_threshold: int,
        sum_mode: bool = False,
    ) -> ExprRef:

        """
        Enforces feasibility thresholds symbolically against datatype models.

        Args:
            edges: Dict connecting tuples of Nodes to Edge Datatypes.
            Node, Edge: Datatype sorts.
            NUM_BITS: BitVector limit.
            feasibility_threshold: Value to validate cuts against.
            sum_mode: Whether to test global aggregation vs discrete threshold.
        """
        
        return (
            BitvectorTopologyManagement.datatype_feasibility_and_filtering_constraints(
                edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode
            )
        )

    @staticmethod
    def datatype_parent_child_constraints(
        graph: nx.DiGraph, nodes: Dict[int, Any], Node: DatatypeSortRef, opt: Optimize
    ) -> None:

        """
        Enforces strict logical integrity for signal paths (Child-Consistency) ensuring entire downstream logic is captured.

        Args:
            graph: Circuit topology graph.
            nodes: Map of indexed symbolic nodes.
            Node: The Node Z3 Datatype.
            opt: Z3 optimizer instance.
        """
        
        BitvectorTopologyManagement.datatype_parent_child_constraints(
            graph, nodes, Node, opt
        )
