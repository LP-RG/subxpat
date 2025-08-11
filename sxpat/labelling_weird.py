from __future__ import annotations
from typing import Dict, List, Tuple
import itertools as it
import networkx as nx
from sxpat.graph import *
from sxpat.graph.Node import Xor
from sxpat.specifications import Specifications
from sxpat.converting import set_prefix
from sxpat.utils.collections import iterable_replace
from sxpat.annotatedGraph import AnnotatedGraph
from sxpat.graph import Family_Subgraph
from typing import Dict, Tuple
from sxpat.converting.porters import GraphVizPorter
from enum import Enum
from sxpat.converting import iograph_from_legacy, sgraph_from_legacy
import glob
import os
from typing import Iterable, TypeVar
from typing import Set
from sxpat.templating.Labelling import Labeling

from sxpat.utils.filesystem import FS
import itertools as it
from Z3Log.verilog import Verilog
from Z3Log.graph import Graph
from Z3Log.utils import convert_verilog_to_gv
from Z3Log.config.config import SINGLE, MAXIMIZE, MONOTONIC
import Z3Log.config.path as paths
from Z3Log.z3solver import Z3solver
from sxpat.solving.Z3Solver import Z3IntFuncEncoder, Z3FuncBitVecSolver
from sxpat.converting.porters import GraphVizPorter
from sxpat.converting.utils import set_prefix_new

WEIGHT = 'weight'
#first bit to represent if we assume case1 approximation
MODE0= 0
#lorenzo approximation (2nd bit)
MODE1 = 1
#always max approximation (3rd bit)
MODE2 = 2
#always equal approximation (4th bit)
MODE3 = 3
IS_CASE1_IDX = 0
WEIGHT_IDX = 2
TOP_BOTT_IDX = 1
IS_CASE2_IDX = 0
CASE2_NODES_IDX = 1
class TOP_OR_BOTTOM(Enum):
        TOP = 0
        BOTTOM = 1
        DEFAULT = 2

class Labelling:

    """
    Class for labeling nodes using the define method approach.
    Replaces labeling_explicit with SMT-based template definition.
    """

    @classmethod
    def define(cls, s_graph: SGraph, specs: Specifications, accs=[], is_case2_idx: bool = False) -> tuple[PGraph, CGraph]:
        assert len(accs) == 1, "Must pass the node to label"
        assert accs[0] in s_graph, "Node requested to label must be in the graph"
        if accs[0] not in s_graph:
            raise ValueError(f"Node '{accs[0]}' not found in graph")
        a_graph: SGraph = set_prefix_new(s_graph, 'a_', it.chain(s_graph.inputs_names))
        
        labeled_node = accs[0]
        labeled_node_name = 'a_' + labeled_node
        not_node = Not(f'not_{labeled_node}', operands=(labeled_node_name,))
        
        updated_nodes: dict[str, Node] = dict()
        
        for succ in a_graph.successors(labeled_node_name):
            new_operands = iterable_replace(succ.operands, succ.operands.index(labeled_node_name), not_node.name)
            updated_nodes[succ.name] = succ.copy(operands=new_operands)
        
        # Additional constraint nodes for case2
        constraint_nodes = []
        nodes_to_place_hold = []
        
        if is_case2_idx:
            predecessors = a_graph.predecessors(labeled_node_name)
            if len(predecessors) == 2:
                false_constraints = []
                for i, pred in enumerate(predecessors):
                    #create constraints for the bottom node
                    false_const = BoolConstant(f'false_pred_{i}', value=False)
                    pred_eq = Xor(f'pred_{i}_eq', operands=(pred.name, false_const.name))
                    pred_eq_false = Not(f'pred_{i}_eq_false', operands=(pred_eq.name,))
                    false_constraints.extend([
                        false_const,
                        pred_eq,
                        pred_eq_false,
                        Constraint.of(pred_eq_false)
                    ])
                constraint_nodes.extend(false_constraints)
                nodes_to_place_hold.extend([pred.name for pred in predecessors])
        
        template_graph = PGraph(
            it.chain(
                (
                    n
                    for n in a_graph.nodes
                    if n.name not in updated_nodes
                ),
                (not_node,),
                updated_nodes.values(),
                constraint_nodes 
            ),
            a_graph.inputs_names, 
            a_graph.outputs_names,
            ()
        )
        
        new_nodes = [
            cur_int := ToInt('cur_int', operands=s_graph.outputs_names),
            tem_int := ToInt('tem_int', operands=template_graph.outputs_names),
            abs_diff := AbsDiff('weight', operands=(cur_int.name, tem_int.name)),
            {
            True: Min('minimize_error', operands=(abs_diff.name,)),
            False: Max('maximize_error', operands=(abs_diff.name,))
            }[specs.min_labeling]
        ]
        
        if specs.min_labeling:
            new_nodes.extend([
                zero := IntConstant('Zero', value=0),
                gt := GreaterThan('GT_0', operands=(abs_diff.name, zero.name)),
                Constraint.of(gt),
            ])
        
        constraint_graph = CGraph(
            it.chain(
                (PlaceHolder(name) for name in it.chain(
                    s_graph.outputs_names,
                    template_graph.outputs_names,
                    nodes_to_place_hold
                )),
                new_nodes,
                [Target.of(abs_diff),]
            )
        )
        
        return (template_graph, constraint_graph)

    
def compute_node_weight_non_recursive(
    e_graph: IOGraph,
    s_graph: SGraph,
    node_name: str,
    specs: Specifications,
    weights: dict[str, int],
    weighted: set[str],
    MODE_VECTOR: list[bool] = [],
    solver: Z3solver = Z3FuncBitVecSolver
    ) -> int:
    """
    Compute the weight of a node without recursion.
    For case1: Either use brother's weight or solve and share with brother.
    For case2: Skip if dependencies not ready, or solve recursively.
    not really not recursive it is only recursive for some case2 situations
    Returns:
        weight of a node
    """
    if node_name in weighted:
        return weights.get(node_name, -1)

    error_value = -1
    #if we allow the assumption that case1 identity always holds
    if MODE_VECTOR[MODE0]:
        is_case1_result = is_case1_idx_check(s_graph, node_name, weighted)
        #check if it is a case1
        if is_case1_result[IS_CASE1_IDX]:
            #check if its brother has been weighted
            if is_case1_result[WEIGHT_IDX] >= 0:
                error_value = is_case1_result[WEIGHT_IDX]
            else:
                error_value = solve_node_directly(e_graph, s_graph, node_name, specs, solver )
                #solve the weight and give it to itds brother
                if is_case1_result[TOP_BOTT_IDX] == TOP_OR_BOTTOM.TOP:
                    succ_nodes = list(s_graph.successors(node_name))
                    if succ_nodes:
                        brother_name = succ_nodes[0].name
                        weights[brother_name] = error_value
                        weighted.add(brother_name)
                        
                elif is_case1_result[TOP_BOTT_IDX] == TOP_OR_BOTTOM.BOTTOM:
                    pred_nodes = list(s_graph.predecessors(node_name))
                    if pred_nodes:
                        brother_name = pred_nodes[0].name
                        weights[brother_name] = error_value
                        weighted.add(brother_name)
            #add weight and node to visited lists
            weights[node_name] = error_value
            weighted.add(node_name)
            return error_value
    #mode1: Lorenzo's theory (reducede space define)
    #mode2: assumption that bottom node is the max of the top nodes
    if MODE_VECTOR[MODE1] or MODE_VECTOR[MODE2]:
        is_case2 = is_case2_idx_bottom(s_graph, node_name)
        
        if is_case2:
            predecessors = list(s_graph.predecessors(node_name))
            pred_weights = []

            # Get predecessor weights (recursively if needed)
            #check wich ones have already been weighted
            for pred in predecessors:
                if pred.name not in weighted:
                    #if not weighted we first find their weights recursively
                    pred_weight = compute_node_weight_non_recursive(
                        e_graph, s_graph, pred.name, specs, weights, weighted, MODE_VECTOR
                    )
                else:
                    pred_weight = weights.get(pred.name, -1)
                pred_weights.append(pred_weight)
            
            if MODE_VECTOR[MODE1]:  # Lorenzo approximation
                template_graph, constraint_graph = Labelling.define(
                    s_graph, specs, accs=[node_name], is_case2_idx=True
                )

                error_value = 0
                status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
                if status == "sat":
                    error_value = model["weight"]

                max_pred_weight = max(pred_weights) if pred_weights else -1
                if status == "unsat" or error_value < max_pred_weight:
                    error_value = max_pred_weight
            else:
                #if mode 2 it is just the max of the preds
                error_value = max(pred_weights) if pred_weights else -1
        else:
            error_value = solve_node_directly(e_graph, s_graph, node_name, specs, solver)

    # MODE3: Always equal approximation
    elif MODE_VECTOR[MODE3]:
        in_case_2 = node_in_case2(s_graph, node_name)

        if in_case_2[IS_CASE2_IDX]:
            case2_data = in_case_2[CASE2_NODES_IDX]
            case2_nodes = list(case2_data) if case2_data else []
            case2_nodes = []
            if isinstance(case2_data, tuple) and len(case2_data) == 2:
                node_obj, predecessors = case2_data
                case2_nodes.append(node_obj)
                case2_nodes.extend(list(predecessors))
            else:
                case2_nodes = list(case2_data) if case2_data else []
            nodes_weighted = [node for node in case2_nodes if node.name in weighted]
            nodes_not_weighted = [node for node in case2_nodes
                                if node.name not in weighted and node.name != node_name]
            
            if len(nodes_weighted) > 0:
                
                for node in nodes_not_weighted:
                    weights[node.name] = error_value
                    weighted.add(node.name)
            else:
                error_value = solve_node_directly(e_graph, s_graph, node_name, specs, solver)
                for node in nodes_not_weighted:
                    weights[node.name] = error_value
                    weighted.add(node.name)
        else:
            error_value = solve_node_directly(e_graph, s_graph, node_name, specs, solver)

    else:
        error_value = solve_node_directly(e_graph, s_graph, node_name, specs, solver)

    weights[node_name] = error_value
    weighted.add(node_name)
    return error_value

def solve_node_directly(e_graph: IOGraph, s_graph: SGraph, node_name: str,
                        specs: Specifications,
                        solver) -> int:
    """
    Solve a single node directly using the Z3 solver.
    """
    try:
        template_graph, constraint_graph = Labelling.define(
            s_graph, specs, accs=[node_name], is_case2_idx=False
        )
        
        status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
        
        if status == "sat":
            return model["weight"]
        else:
            return -1
            
    except Exception as e:
        print(f"Error solving node {node_name}: {e}")
        return -1

def compute_weights_trivial(
    e_graph: IOGraph,
    s_graph: SGraph,
    node_name: str,
    specs: Specifications,
    weights: dict[str, int],
    weighted: set[str],
    solver
    ) -> int:
    
    template_graph, constraint_graph = Labeling.define(
            s_graph, specs, accs=[node_name]
        )
    
    error_value = 0
    status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
    if status == "sat":
        error_value = model["weight"]
    weights[node_name] = error_value
    weighted.add(node_name)
    return weights[node_name]

    


def labeling_using_define_improved(
    exact_benchmark_name: str,
    approximate_benchmark: str,
    min_labeling: bool,
    partial_labeling: bool,
    partial_cutoff: int,
    parallel: bool = False,
    MODE_VECTOR: list[bool] = [],
    solver: Z3solver = Z3FuncBitVecSolver
) -> dict[str, int]:
    """
    Improved labeling function that handles recursive dependencies.
    """
    exact = AnnotatedGraph(exact_benchmark_name, is_clean= False)
    approximate = AnnotatedGraph(approximate_benchmark, is_clean= False)
    s_graph = iograph_from_legacy(approximate)
    io_graph = iograph_from_legacy(exact)
    
    specs_obj = Specifications("", "", False, False, 0, 10, 10, 1, 5, 3, False, 0, False,0, 0,0,0,1, 10, 10, 10, 0,0,0,60.0, False, False, False)

    weights = {}
    weighted = set()

    # Get internal nodes
    internal_nodes = [
        node.name for node in s_graph.nodes
        if node.name not in s_graph.outputs_names
        and node.name not in s_graph.inputs_names
    ]

    # Process each node
    #TODO iterate in every output and every ancestor of output until partial cutoff
    for node_name in internal_nodes:
        if node_name not in weighted:
            #not "fully recursive", only for nodes that are part of a pattern
            compute_node_weight_non_recursive(
                io_graph, s_graph, node_name, specs_obj, weights, weighted, MODE_VECTOR, solver
            )

    return weights

def labeling_using_normal(exact_benchmark_name: str,
    approximate_benchmark: str,
    min_labeling: bool,
    partial_labeling: bool,
    partial_cutoff: int,
    parallel: bool = False,
    solver: Z3solver = Z3FuncBitVecSolver
) -> dict[str, int]:
    exact = AnnotatedGraph(exact_benchmark_name, is_clean= False)
    approximate = AnnotatedGraph(approximate_benchmark, is_clean= False)
    s_graph = iograph_from_legacy(approximate)
    io_graph = iograph_from_legacy(exact)
    # s_graph = GraphVizPorter.from_file("/mnt/c/Users/tibob/subxpat/input/weighted/abs_diff_i4_o2_1744127512.gv")
    # io_graph = GraphVizPorter.from_file("/mnt/c/Users/tibob/subxpat/input/weighted/abs_diff_i4_o2_1744127512.gv")

    specs_obj = Specifications("", "", False, False, 0, 10, 10, 1, 5, 3, False, 0, False,0, 0,0,0,1, 10, 10, 10, 0,0,0,60.0, False, False, False)
    weights = {}
    weighted = set()

    internal_nodes = [
        node.name for node in s_graph.nodes
        if node.name not in s_graph.outputs_names
        and node.name not in s_graph.inputs_names

    ]
    for node_name in internal_nodes:
        if node_name not in weighted:
            compute_weights_trivial(
               io_graph, s_graph,node_name, specs_obj,weights, weighted, solver
            )
    return weights

def checK_error_case2(s_graph, node_name, error_value) -> int:

    """
    checks if the error obtained from the reduced space search for case2 is correct or not
    if not higher than max of the two top nodes --> error value is correct else it is the max of the two
    Args:
        s_graph: the graph being evaluated
        node_name: the bottom case2 node being evaluated
        error_value: the error_value calculated for the node
    Returns :
        the correct error value
    """

    weigths = [node.weight for node in s_graph.predecessors(node_name)]
    if error_value  < max(weigths):
        return max(weigths)
    else:
        return error_value


def is_case2_idx_bottom(s_graph : SGraph, node: str) -> bool:
    """
    method that checks wether a node is the bottom node of a case2 pattern
    Args:
        s_graph: Original circuit graph
        node: Name of the node to evaluate

    Returns:
        if the node is a case2 pattern occurence (and if it is the bottom node of the pattern )
    """
    return len(s_graph.predecessors(node)) == 2 and all(map(lambda item: len(s_graph.successors(item)) == 1, s_graph.predecessors(node)))



def is_case1_idx_check(s_graph: SGraph, node: str, weighted: set[str], weights: dict[str, int] = None) -> tuple[bool, TOP_OR_BOTTOM, int]:
    """
     method that checks wether a node is the bottom node of a case1 pattern
    Args:
        s_graph: Original circuit graph
        node: Name of the node to evaluate

    Returns:
        if the node is a case1 pattern occurence, wich kind it is and the weight is given, (if weight is negative
        it should be computed with the solver)
    """
    if weights is None:
        weights = {}
        
    weight = -1
    
    predecessors = list(s_graph.predecessors(node))
    successors = list(s_graph.successors(node))
    
    condition_bottom = (len(predecessors) == 1 and 
                       len(list(s_graph.successors(predecessors[0].name))) == 1)
    
    condition_top = (len(successors) == 1 and 
                    len(list(s_graph.predecessors(successors[0].name))) == 1)
    
    if condition_bottom:
        brother_name = predecessors[0].name
        if brother_name in weighted:
            weight = weights.get(brother_name, -1)
        return (True, TOP_OR_BOTTOM.BOTTOM, weight)
        
    elif condition_top:
        brother_name = successors[0].name
        if brother_name in weighted:
            weight = weights.get(brother_name, -1)
        return (True, TOP_OR_BOTTOM.TOP, weight)
        
    else:
        return (False, TOP_OR_BOTTOM.DEFAULT, weight)


def check_case2_pattern(s_graph: SGraph, node_name: str) -> bool:
    """Check if node matches case 2 pattern - needs implementation"""
    node = next((n for n in s_graph.nodes if n.name == node_name), None)
    if not node or not isinstance(node, And):
        return False
    return False


def node_in_case2(s_graph : SGraph, node_name: str) -> tuple[bool, Iterable[Node]] :
    """
    function that says wether a node is in a  case 2 pattern
    Ags:
        s_graph : graph
        node_name: name of the node we are evaluating
    Returns:
        a Tuple saying if the node is a case2 and the nodes in the case2 if it is
    """
    if is_case2_idx_bottom(s_graph, node_name):
        node = s_graph.__getitem__(node_name)
        return (True,(node, s_graph.predecessors(node_name)))
    elif len(s_graph.successors(node_name)) == 1 and is_case2_idx_bottom(s_graph,  s_graph.successors(node_name)[0].name):
        bottom_node = s_graph.successors(node_name) [0]
        return (True, (bottom_node, s_graph.predecessors(bottom_node)) )
    else :
        return (False, []) 