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
        OptimizationConstraints.add_io_limits(
            opt, imax, omax, partition_input_edges, partition_output_edges
        )

    @staticmethod
    def add_maximization(
        opt: Optimize,
        gate_literals: Dict[int, BoolRef],
        gate_weight: Optional[Dict[int, int]],
    ) -> None:
        OptimizationConstraints.add_maximization(opt, gate_literals, gate_weight)

    @staticmethod
    def exclude_skipped_nodes(opt: Optimize, graph: nx.DiGraph) -> None:
        OptimizationConstraints.exclude_skipped_nodes(opt, graph)

    @staticmethod
    def check_convexity(
        opt: Optimize, G: nx.DiGraph, gate_dict: Dict[int, str]
    ) -> List[str]:
        return OptimizationConstraints.check_convexity(opt, G, gate_dict)

    @staticmethod
    def validate_selection_convexity(G: nx.DiGraph, node_partition: List[int]) -> None:
        OptimizationConstraints.validate_selection_convexity(G, node_partition)

    @staticmethod
    def add_sensitivity_budget(
        opt: Optimize,
        edge_w: Dict[int, int],
        edge_constraint: Dict[int, BoolRef],
        sensitivity_t: int,
    ) -> None:
        SensitivityBudgetConstraints.add_budget_constraints(
            opt, edge_w, edge_constraint, sensitivity_t
        )

    @staticmethod
    def prepare_gate_weights(
        G: nx.DiGraph, tmp_graph: nx.DiGraph, gate_dict: Dict[int, str], weight_key: str
    ) -> Dict[int, int]:
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
        return ModelInitialization.prepare_circuit_model(tmp_graph, constant_dict)

    @staticmethod
    def build_gate_graph(
        tmp_graph: nx.DiGraph, constant_dict: Dict[int, str]
    ) -> nx.DiGraph:
        return ModelInitialization.build_gate_graph(tmp_graph, constant_dict)

    @staticmethod
    def add_boundary_conditions(
        opt: Optimize,
        input_literals: Dict[int, BoolRef],
        output_literals: Dict[int, BoolRef],
    ) -> None:
        ModelInitialization.add_boundary_conditions(
            opt, input_literals, output_literals
        )

    @staticmethod
    def extract_gate_weights(
        G: nx.DiGraph, tmp_graph: nx.DiGraph, gate_dict: Dict[int, str], weight_key: str
    ) -> Dict[int, int]:
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
        return MultiPartitionIterationEngine.extract_multiple_subgraphs(
            opt, G, specs_obj, mode=mode, penalty=penalty
        )

    @staticmethod
    def select_best_partition(all_partitions: List[Any], mode: str = "multi") -> Tuple:
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
    ) -> Tuple[
        DatatypeSortRef,
        DatatypeSortRef,
        Dict[int, Any],
        Dict[Tuple[int, int], Any],
        int,
    ]:
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
        return BitvectorTopologyManagement.datatype_signal_propagation_constraints(
            graph, nodes, Node, NUM_BITS
        )

    @staticmethod
    def datatype_convexity_and_structural_constraints(
        graph: nx.DiGraph, nodes: Dict[int, Any], Node: DatatypeSortRef, opt: Optimize
    ) -> None:
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
        return (
            BitvectorTopologyManagement.datatype_feasibility_and_filtering_constraints(
                edges, Node, Edge, NUM_BITS, feasibility_threshold, sum_mode
            )
        )

    @staticmethod
    def datatype_parent_child_constraints(
        graph: nx.DiGraph, 
        nodes: Dict[int, Any], 
        Node: DatatypeSortRef, 
        opt: Optimize
    ) -> None:
        BitvectorTopologyManagement.datatype_parent_child_constraints(
            graph, nodes, Node, opt
        )
