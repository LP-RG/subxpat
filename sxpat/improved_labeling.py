from __future__ import annotations
from typing import Dict, List, Tuple
import itertools as it
from sxpat.solving.QbfSolver import QbfSolver

import networkx as nx
from time import perf_counter
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
from sxpat.utils.timer import Timer
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
from sxpat.solving.Z3Solver import Z3FuncBitVecSolver, Z3FuncIntSolver, Z3DirectIntSolver, Z3DirectBitVecSolver

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
    Class for Labelling nodes using the define method approach.
    Replaces Labelling_explicit with  new improved version.
    @author Thibaud Babin
    """

     

    @staticmethod
    def define( s_graph: SGraph, specs: Specifications, accs=[], is_case2: bool = False) -> tuple[PGraph, CGraph]:
        """ 
        Method given by Lorenzo with the addition of adding additional constraints if is_case2 flag is set
        Args:  
            s_graph: Original circuit graph
            specs: Specifications for Labelling
            accs: Node to label
            is_case2: Flag to indicate if additional constraints for case2 should be added
        Returns:
            A tuple containing the template graph and the constraint graph

        @authors: Lorenzo Spada, Thibaud Babin
        """
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
        constraint_nodes = []
        nodes_to_place_hold = []
        
        #adding additional constraints  in case of case2
        if is_case2:
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

    @staticmethod
    def compute_node_weight(
        e_graph: IOGraph,
        s_graph: SGraph,
        node_name: str,
        specs: Specifications,
        weights: dict[str, int],
        weighted: set[str],
        MODE_VECTOR: list[bool] = [],
        solver = QbfSolver
        ) -> int:
        """
        Compute the weight of a node using optimizations varying on how the mode vector is set
        MODE_VECTOR[MODE0] -> all case1 patterns nodes are equal (~25% of nodes skipped)
        MODE_VECTOR[MODE1] -> if a node is a case2 bottom node, we do reduced search space define on it
        MODE_VECTOR[MODE2] -> We consider that the bottom node of any case2 is the maximum of its two top nodes
        MODE_VECTOR[MODE3] -> We consider that case3 nodes are all equal
        MODE 0 can be combined with any of the other modes.
        set to [FALSE, FALSE, FALSE,FALSE] to just label normally
        Args:
            e_graph: exact graph, IOGraph
            s_graph: approximate graph, also IOGraph (encountered error while creating SGraph from Annotated graph)
            node_name: name of the node we are Labelling, str
            specs: Specifications object (straightforward)
            MODE_VECTOR: set of optimizations we want to apply, list of booleans 
            solver : what solver we are using to solve the question for a node
        Returns:
            an int representing the weight of that node
        @author: Thibaud Babin
         """
        if node_name in weighted:
            return weights.get(node_name, -1)
        
        # Check available optimizations and their viability
        #this is in case we have an overlapping case1 and case2
        #TODO every time we encounter a case 1 or a case2, recursively check its neighbors and
        # form a cluster of connected case1 and case2 nodes
        # this way, for MODES 1,3,03 we can solve a whole cluster by knowing only one node
        #currrent implementation is just a bit less efficient than this it might compute one or two more nodes 
        #than necessary in a cluster
        mode0_case1_available = False
        mode3_case2_available = False
        mode3_case2_nodes = []
        mode3_nodes_weighted = []
        
        # Check MODE0 case1 optimization
        if MODE_VECTOR[MODE0]:
            is_case1_result = Labelling.is_case1_idx_check(s_graph, node_name, weighted, weights)
            if is_case1_result[IS_CASE1_IDX]:
                mode0_case1_available = True
        
        # Check MODE3 case2 optimization  
        if MODE_VECTOR[MODE3]:
            in_case_2 = Labelling.node_in_case2(s_graph, node_name)
            if in_case_2[IS_CASE2_IDX]:
                case2_data = in_case_2[CASE2_NODES_IDX]
                if isinstance(case2_data, tuple) and len(case2_data) == 2:        
                    node_obj, predecessors = case2_data
                    mode3_case2_nodes = [node_obj] + list(predecessors)
                else:
                    mode3_case2_nodes = list(case2_data) if case2_data else []
                
                mode3_nodes_weighted = [node for node in mode3_case2_nodes if node.name in weighted]
                            
                if mode3_nodes_weighted:  # MODE3 case2 optimization is viable
                    mode3_case2_available = True

        if mode0_case1_available and mode3_case2_available:
            # Both optimizations available -> choose MODE3 because reusing weight is faster than solving
        
            error_value = weights[mode3_nodes_weighted[0].name]
            
            # Jump optimization for unweighted nodes in the same case2 group
            nodes_not_weighted = [node for node in mode3_case2_nodes
                                if node.name not in weighted and node.name != node_name]
            for node in nodes_not_weighted:
                print(f"node {node.name} has been jumped we can go faster")
                weights[node.name] = error_value
                weighted.add(node.name)
                
            weights[node_name] = error_value
            weighted.add(node_name)
            print(f"MODE3 was able to jump {len(nodes_not_weighted)} nodes")
            return error_value
            
        # MODE3 case2 optimization only
        elif mode3_case2_available:
            
            error_value = weights[mode3_nodes_weighted[0].name]
            
            nodes_not_weighted = [node for node in mode3_case2_nodes
                                if node.name not in weighted and node.name != node_name]
            for node in nodes_not_weighted:
                print(f"node {node.name} has been jumped we can go faster")
                weights[node.name] = error_value
                weighted.add(node.name)
                
            weights[node_name] = error_value
            weighted.add(node_name)
            print(f"MODE3 was able to jump {len(nodes_not_weighted)} nodes")
            return error_value
        
        # MODE0 case1 optimization only
        elif mode0_case1_available:
            
            if is_case1_result[WEIGHT_IDX] >= 0:
                error_value = is_case1_result[WEIGHT_IDX]
            else:
                error_value = Labelling.solve_node_directly(e_graph, s_graph, node_name, specs, solver)
                
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
            
            weights[node_name] = error_value
            weighted.add(node_name)
            return error_value
        
        # MODE1/MODE2 case2 handling
        elif MODE_VECTOR[MODE1] or MODE_VECTOR[MODE2]:
            is_case2 = Labelling.is_case2_idx_bottom(s_graph, node_name)
            
            if is_case2:
                predecessors = list(s_graph.predecessors(node_name))
                pred_weights = []
                for pred in predecessors:
                    if pred.name not in weighted:
                        pred_weight = Labelling.compute_node_weight(
                            e_graph, s_graph, pred.name, specs, weights, weighted, MODE_VECTOR, solver
                        )
                    else:
                        pred_weight = weights.get(pred.name, -1)
                    pred_weights.append(pred_weight)
                
                if MODE_VECTOR[MODE1]:
                    template_graph, constraint_graph = Labelling.define(
                        s_graph, specs, accs=[node_name], is_case2=True
                    )
                    error_value = 0
                    status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
                    if status == "sat":
                        error_value = model["weight"]
                    
                    max_pred_weight = max(pred_weights) if pred_weights else -1
                    if status == "unsat" or error_value < max_pred_weight:
                        error_value = max_pred_weight
                else:
                    error_value = max(pred_weights) if pred_weights else -1
            else:
                error_value = Labelling.solve_node_directly(e_graph, s_graph, node_name, specs, solver)
            
            weights[node_name] = error_value
            weighted.add(node_name)
            return error_value
        
        else:
            
            error_value = Labelling.solve_node_directly(e_graph, s_graph, node_name, specs, solver)
            weights[node_name] = error_value
            weighted.add(node_name)
            return error_value

    @staticmethod
    def solve_node_directly(e_graph: IOGraph, s_graph: SGraph, node_name: str,
                            specs: Specifications,
                            solver) -> int:
        """
        Solve a single node directly using the solver.
        helper function for compute_node_weight function
        Args:
            e_graph: exact graph (IOGraph)
            s_graph: approximated graph (SGraph)
            node_name: node we are solving (str)
            specs: Specifications object we are giving to the solver
            solver: solver we are using to solve the node
        Returns:
            the weight of the node as an int, -1 if it was unsat
        @author : Thibaud Babin
        """
        try: 
            template_graph, constraint_graph = Labelling.define(
                s_graph, specs, accs=[node_name], is_case2=False
            )
            
            status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
            
            if status == "sat":
                return model["weight"]
            else:
                return -1
                
        except Exception as e:
            print(f"Error solving node {node_name}: {e}")
            return -1
        
    @staticmethod
    def labelling_improved(
        exact_benchmark: AnnotatedGraph,
        approximate_benchmark: AnnotatedGraph,
        #added default value for specs
        specs : Specifications = Specifications("", "", False, False, 0, 10, 10, 1, 5, 3, False, 0,
                                                 False,0, 0,0,0,1, 10, 10, 10, 0,0,0,60.0, 
                                                 False, False, False),
        MODE_VECTOR: list[bool] = [],
        solver = QbfSolver
    ) -> tuple[dict[str, int], dict[str, int]]:
        """
        Improved Labelling function that handles that sets ups the improved node Labelling process
        MODE_VECTOR[MODE0] -> all case1 patterns nodes are equal (~25% of nodes skipped)
        MODE_VECTOR[MODE1] -> if a node is a case2 bottom node, we do reduced search space define on it
        MODE_VECTOR[MODE2] -> We consider that the bottom node of any case2 is the maximum of its two top nodes
        MODE_VECTOR[MODE3] -> We consider that case3 nodes are all equal
        MODE 0 can be combined with any of the other modes.
        set to [FALSE, FALSE, FALSE,FALSE] to just label normally
        Args:
            exact_benchmark_name : name of the exact circuit (str)
            approximate_benchmark_name : name of the approximate benchmark
            specs: Specifications object that will be given to the server
            MODE_VECTOR: set of optimizations we want to apply, list of booleans 
            solver : solver we are using
        Returns:
            a tuple containing a dictionnary of node names associated to their weight and a dictionnary
            containing node names associated to the time it took to weight them
        @author : Thibaud Babin
        """
        #print(f" ================================== DEBUG for MODE VECTOR {MODE_VECTOR} ================================== ")
        # start1 = perf_counter()
        # start = perf_counter()
        # print(f"debug: exact benchmark name : {exact_benchmark_name}")
        # exact = AnnotatedGraph(exact_benchmark_name, is_clean= False)
        # end = perf_counter()
        # print(f"DEBUG: TIME TO LOAD EXACT GRAPH 1 {end - start:.4f} seconds")
        # start = perf_counter()
        #print(f"debug: exact approximate name : {exact_benchmark_name}")

        #approximate = AnnotatedGraph(approximate_benchmark, is_clean= False)

        #print(f"DEBUG: TIME TO LOAD EXACT GRAPH 2 {end - start:.4f} seconds")

        s_graph = iograph_from_legacy(approximate_benchmark)
        io_graph = iograph_from_legacy(exact_benchmark)
        #end1 = perf_counter()
        # time1 = end1 - start1
        # print(f"DEBUG TIME TO LOAD GRAPHS {time1:.4f} seconds")

        weights = {}
        time_node = {}
        weighted = set()

        # Get internal nodes
        internal_nodes = [
            node.name for node in s_graph.nodes
            if node.name not in s_graph.outputs_names
            and node.name not in s_graph.inputs_names
        ]
        # Process each node
        #TODO iterate in every output and every ancestor of output until partial cutoff
        # start = perf_counter()
        #timer, process_nodes_timed = Timer.from_function(process_nodes)
        Labelling.process_nodes(MODE_VECTOR, solver, s_graph, io_graph, specs, weights, time_node, weighted, internal_nodes)
        # print(f"DEBUG PROCESS NODES TIME SUM NODES {sum_time:.4f} seconds")
        # print(f"DEBUG PROCESS NODES TIME SUM NODES AND PRE-PROCESS TIME {sum_time + time1:.4f} seconds")
        # print(f"DEBUG PROCESS NODES TIME WITH CLOCK TIMER {time2:.4f} seconds")
        # print(f" ================================== DEBUG for MODE VECTOR {MODE_VECTOR} ================================== ")

        return (weights, time_node)
    @staticmethod
    def process_nodes(MODE_VECTOR,
                    solver, 
                    s_graph,
                    io_graph, 
                    specs_obj, 
                    weights, 
                    time_node, 
                    weighted, 
                    internal_nodes):
        """
        helper function that simply calls compute_node_weight for every node that isn't weighted 
        Args:
            MODE_VECTOR: set of optimizations we want to apply, list of booleans
            solver : solver we are using
            s_graph: approximated graph 
            io_graph: exact graph
            specs: Specifications object that will be given to the solver#
            weigths: dictionnary of nodes associated to their weights
            time_node: dictionnary of nodes associated to their process time
            weighted: set of nodes that have been weighted
            internal_nodes: nodes that we are Labelling
        Returns:
           Nothing, just modifies weightsm weighted and node_times argument
        Thibaud Babin
        """
        #print(f"Processing order: {internal_nodes[:10]}") 
        for node_name in internal_nodes:
            if node_name not in weighted:

                timer, compute_node_weight_timed = Timer.from_function(Labelling.compute_node_weight)
                compute_node_weight_timed(
                    io_graph, s_graph, node_name, specs_obj, weights, weighted, MODE_VECTOR, solver
                )
                node_time = timer.latest
                time_node[node_name] = node_time

    @staticmethod
    def is_case2_idx_bottom(s_graph : SGraph, node: str) -> bool:
        """
        method that checks wether a node is the bottom node of a case2 pattern
        Args:
            s_graph: Original circuit graph
            node: Name of the node to evaluate

        Returns:
            if the node is a case2 pattern occurence (and if it is the bottom node of the pattern )
        @author : Thibaud Babin
        """
        return len(s_graph.predecessors(node)) == 2 and all(map(lambda item: len(s_graph.successors(item)) == 1, s_graph.predecessors(node)))


    @staticmethod
    def is_case1_idx_check(s_graph: SGraph, node: str, weighted: set[str], weights: dict[str, int] = None) -> tuple[bool, TOP_OR_BOTTOM, int]:
        """
        method that checks wether a node is the bottom node of a case1 pattern
        Args:
            s_graph: Original circuit graph
            node: Name of the node to evaluate

        Returns:
            if the node is a case1 pattern occurence, wich kind it is (top or bottom node of the case)
            and the weight if any of the two nodes is in weighted, (if weight is negative
            it should be computed with the solver)
        @author: Thibaud Babin
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


    @staticmethod
    def node_in_case2(s_graph : SGraph, node_name: str) -> tuple[bool, Iterable[Node]] :
        """
        function that says wether a node is in a  case 2 pattern
        Ags:
            s_graph : graph
            node_name: name of the node we are evaluating
        Returns:
            a Tuple saying if the node is a case2 and the nodes in the case2 if it is
        @author: Thibaud Babin
        """
        if Labelling.is_case2_idx_bottom(s_graph, node_name):
            node = s_graph.__getitem__(node_name)
            #if node is any of the two top nodes
            return (True,(node, s_graph.predecessors(node_name)))
        elif len(s_graph.successors(node_name)) == 1 and Labelling.is_case2_idx_bottom(s_graph,  s_graph.successors(node_name)[0].name):
            #if node is the bottom node
            bottom_node = s_graph.successors(node_name) [0]
            return (True, (bottom_node, s_graph.predecessors(bottom_node)) )
        else :
            return (False, []) 
    @staticmethod
    def Labelling_using_normal(exact_benchmark_name: str,
        approximate_benchmark: str,
        min_Labelling: bool,
        partial_Labelling: bool,
        partial_cutoff: int,
        parallel: bool = False,
        solver: Z3solver = Z3DirectIntSolver
    ) -> tuple[dict[str, int], dict[str, int]]:
        """
        function that does the labelling normally without any of the checks for the improvements. Used as a control
        when benchmarking the improved node Labelling function
        """
        exact = AnnotatedGraph(exact_benchmark_name, is_clean= False)
        approximate = AnnotatedGraph(approximate_benchmark, is_clean= False)
        s_graph = iograph_from_legacy(approximate)
        io_graph = iograph_from_legacy(exact)
        # s_graph = GraphVizPorter.from_file("/mnt/c/Users/tibob/subxpat/input/weighted/abs_diff_i4_o2_1744127512.gv")
        # io_graph = GraphVizPorter.from_file("/mnt/c/Users/tibob/subxpat/input/weighted/abs_diff_i4_o2_1744127512.gv")

        specs_obj = Specifications("", "", False, False, 0, 10, 10, 1, 5, 3, False, 0, False,0, 0,0,0,1, 10, 10, 10, 0,0,0,60.0, False, False, False)
        weights = {}
        node_times =  {}
        weighted = set()

        internal_nodes = [
            node.name for node in s_graph.nodes
            if node.name not in s_graph.outputs_names
            and node.name not in s_graph.inputs_names

        ]
        for node_name in internal_nodes:
            if node_name not in weighted:
                timer, compute_node_weight_timed = Timer.from_function(Labelling.compute_weights_trivial)

                compute_node_weight_timed(              
                io_graph, s_graph,node_name, specs_obj,weights, weighted, solver
                )
                node_time_trivial = timer.latest
                node_times[node_name] = node_time_trivial
        return (weights, node_times)
    
    def compute_weights_trivial(
        e_graph: IOGraph,
        s_graph: SGraph,
        node_name: str,
        specs: Specifications,
        weights: dict[str, int],
        weighted: set[str],
        solver
        ) -> int:
        
        template_graph, constraint_graph = Labelling.define(
                s_graph, specs, accs=[node_name]
            )
        
        error_value = 0
        status, model = solver.solve([e_graph, template_graph, constraint_graph], specs)
        if status == "sat":
            error_value = model["weight"]
        weights[node_name] = error_value
        weighted.add(node_name)
        return weights[node_name]
    