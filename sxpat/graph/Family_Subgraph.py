from __future__ import annotations
import networkx as nx
import itertools as it
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import sys
from typing import Dict
from typing import List
from typing import Tuple
from pathlib import Path
project_root = Path(__file__).parent.parent.parent  # Go up to subxpat root
sys.path.insert(0, str(project_root))
from typing import Dict, List, Sequence, Tuple, Union
from collections import defaultdict, Counter
from itertools import combinations
import itertools as it
from sxpat.graph import *
from sxpat.converting.legacy import iograph_from_legacy
from sxpat.converting.porters import GraphVizPorter
import subprocess
from typing import List, Dict, Set, Any
from itertools import combinations_with_replacement

# Import sxpat modules
from sxpat.graph import *
from sxpat.converting.legacy import iograph_from_legacy
from sxpat.converting.porters import GraphVizPorter
from sxpat.converting import set_prefix
from sxpat.specifications import ConstantsType, Specifications  
from sxpat.utils.collections import flat, iterable_replace, pairwise

# Import Node classes - ABSOLUTE imports instead of relative
from sxpat.graph.Node import (
    Expression, Extras, Node, Operation, Constant, GlobalTask,
    BoolVariable, PlaceHolder, Target, Constraint,
    OperationNode, ConstantNode, GlobalTaskNode, ExpressionNode,
    And, Or, Not, Xor
)
try:
    from error import UndefinedNodeError
except ImportError:
    # If error.py doesn't exist or can't be found, define a dummy class
    class UndefinedNodeError(Exception):
        pass
import os
from pickle import Pickler, Unpickler
class Node_constraints():
    def __init__(self, max_pred_amount: int, max_succ_amount: int)-> None :
        self.max_pred_amount = max_pred_amount
        self.max_succ_amount = max_succ_amount
    def respect_constraints(self, node : Node, graph : IOGraph) -> bool:
        predecessor_num = len(graph.predecessors(node))
        successors_num = len(graph.successors(node))
        
            # print(f"\n===========DEBUG RESPECT CONSTRAINTS====================")
            # print(f"node {node.name} has {predecessor_num} predecessors and {successors_num} successor")
            # print(f"max amount succ : {self.max_succ_amount}, max pred amount {self.max_pred_amount}")
        if self.max_pred_amount == 10:
            #print("entered condition pred ")
            return len(graph.successors(node)) == self.max_succ_amount
        elif self.max_succ_amount == 10:
            #print("entered condition succ ")
            return len(graph.predecessors(node)) == self.max_pred_amount
        else :
            return successors_num == self.max_succ_amount and predecessor_num == self.max_pred_amount

                

class Family_Subgraph():
    #TODO adapt class to allow more "levels": add an argument num levels, and for each level after 2 redo the connections
    #but only with the last level 
    """
    a two-level subgraph
    
    Attributes:
        nodes (List[Node]): List of nodes in the subgraph.
        edges (List[Tuple[Node, Node]]): List of edges in the subgraph.
        name (str): Name of the subgraph.
    """
    def __init__(self, name: str, max_nodes_level:int) -> None:
        self.name = name
        self.max_nodes_level = max_nodes_level

    def is_redundant(self, graph: Graph) -> bool:
        """
    Check if the graph contains redundant operations.
    A graph is redundant if multiple outputs perform the same operation on the same inputs.
    """
        output_operations = {}
        
        for node in graph.nodes:
            if hasattr(node, 'name') and node.name.startswith('o'):
                if hasattr(node, 'operands') and node.operands:
                    operation_signature = (type(node).__name__, tuple(sorted(node.operands)))
                    
                    if operation_signature in output_operations:
                        return True
                    
                    output_operations[operation_signature] = node
    
        return False

    def graph_to_networkx(self, graph: IOGraph) -> nx.DiGraph:
        """Convert IOGraph to NetworkX for isomorphism checking.
        Args:
            graph (IOGraph): The graph to convert.
        Returns:
            nx.DiGraph: A directed graph representation of the IOGraph.
            """
        nx_graph = nx.DiGraph()
        
        for node in graph.nodes:
            node_type = type(node).__name__
            nx_graph.add_node(node.name, node_type=None)
        
        for node in graph.nodes:
            if isinstance(node, Operation) and node.operands:
                for operand in node.operands:
                    nx_graph.add_edge(operand, node.name)
        
        return nx_graph
    
    def are_graphs_isomorphic(self, graph1: IOGraph, graph2: IOGraph) -> bool:
        """Check if two graphs are structurally identical (isomorphic).
        Args:
            graph1 (IOGraph): First graph to compare.
            graph2 (IOGraph): Second graph to compare.
        Returns:
            bool: True if the graphs are isomorphic, False otherwise.
        
        """
        nx_graph1 = self.graph_to_networkx(graph1)
        nx_graph2 = self.graph_to_networkx(graph2)
        
        return nx.is_isomorphic(nx_graph1, nx_graph2, 
                               node_match=lambda x, y: x['node_type'] == y['node_type'])
    
    def remove_isomorphic_duplicates(self, graphs: List[IOGraph]) -> List[IOGraph]:
        """Remove isomorphic duplicates from a list of graphs.
        Args:
            graphs (List[IOGraph]): List of IOGraph objects to check for isomorphism. 

        Returns:
            List[IOGraph]: A list of unique IOGraph objects, with duplicates removed.
        """
        unique_graphs = []
        
        for graph in graphs:
            is_duplicate = False
            for unique_graph in unique_graphs:
                if self.are_graphs_isomorphic(graph, unique_graph):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_graphs.append(graph)
        
        return unique_graphs
    
    def is_graph_connected(self, graph: IOGraph) -> bool:
        """
        Check if the graph is connected (all nodes are reachable).
        Args:
            graph (IOGraph): The graph to check.
        Returns:
            bool: True if the graph is connected, False otherwise.
        """
        nxGraph = self.graph_to_networkx(graph)
        return nx.is_connected(nxGraph.to_undirected())

    def remove_hash_duplicates(self,graph : IOGraph, seen_graphs : Dict[nx.DiGraph, IOGraph]) -> None:
        """
        Remove isomorphic duplicates from the list of graphs.
        This method uses NetworkX weisfeiler_lehman_graph_hash to check for isomorphism
        Args:
            graph (IOGraph): The graph to check for duplicates.
            seen_graphs (dict[nx.DiGraph, IOGraph]): Dictionary to store unique graphs by their hash.
        Outputs:
            None: The input list is modified in place to remove redundant graphs.
        """
        nx_graph = self.graph_to_networkx(graph)
        graph_hash = nx.weisfeiler_lehman_graph_hash(
            nx_graph, 
            node_attr=None)
        
        if graph_hash not in seen_graphs:
            seen_graphs[graph_hash] = graph
        

    
    def redundancy_check(self, graphs: List[IOGraph]) -> None:
        """
        Check if the subgraph is redundant in the context of the given graphs.
        remove from the list all graphs that are redundant with this subgraph.
        Args:
            graphs (list[IOGraph]): List of IOGraph objects to check for redundancy.
        Outputs:
            None: The input list is modified in place to remove redundant graphs.
        """
        for graph in graphs.copy():
            if self.is_redundant(graph):
                graphs.remove(graph)


    # def generate_unique_connection_patterns(num_inputs: int, num_outputs: int):

    #     connections = []
        
    #     for i in range(num_inputs):
    #         connections.append((i,))
        
    #     for i in range(num_inputs):
    #         for j in range(i + 1, num_inputs):
    #             connections.append((i, j))
        
    #     for pattern in combinations_with_replacement(connections, num_outputs):
    #         yield pattern


    def generate_family(self, combination: Tuple[int, int]) -> List[IOGraph]:
        """
        functions that all possible unique graphs for a certain "family" ie a given number of nodes
        at the input and a certain number of nodes at the output 
        inputs: combination: a tuple of two integers, the first being the number of inputs and the second being the number of outputs
        outputs: a list of IOGraph objects representing the generated graphs for that family
        """
        input_nodes: List[Node] = []
        num_inputs, num_outputs = combination
        valid_graphs = []
        seen_graphs: Dict[str, IOGraph] = {}  
                
        for i in range(num_inputs):
            input_nodes.append(BoolVariable(name=f'i{i}', weight=None, in_subgraph=False))
                
        total_base_connections = num_inputs + (num_inputs * (num_inputs - 1) // 2)
        print("number of possible connections for combination %s: %d", combination,
            num_outputs * total_base_connections)
                
        base_connections = []
        for inp_idx in range(num_inputs):
            base_connections.append([inp_idx])
        for inp1_idx in range(num_inputs):
            for inp2_idx in range(inp1_idx + 1, num_inputs):
                base_connections.append([inp1_idx, inp2_idx])
                
        tuple_connections = [tuple(sorted(conn)) for conn in base_connections]
                
        for pattern in combinations_with_replacement(tuple_connections, num_outputs):
            output_connections = [list(conn) for conn in pattern]
            
            used_inputs = set()
            for connections in output_connections:
                used_inputs.update(connections)
                        
            if len(used_inputs) != num_inputs:
                continue
                        
            all_nodes = input_nodes.copy()
                        
            for output_idx, input_indices in enumerate(output_connections):
                operand_names = tuple(f'i{idx}' for idx in input_indices)
                if len(input_indices) == 1:
                    # For single input, create a Not node or direct connection
                    output_node = Not(name=f'o{output_idx}', operands=operand_names, weight= 1)
                else:
                    # For multiple inputs, create AND gate
                    output_node = And(name=f'o{output_idx}', operands=operand_names, weight= 1, in_subgraph=False)
                                
                all_nodes.append(output_node)
                        
            input_names = [f'i{i}' for i in range(num_inputs)]
            output_names = [f'o{i}' for i in range(num_outputs)]
                        
            graph = IOGraph(
                nodes=all_nodes,
                inputs_names=input_names,
                outputs_names=output_names
            )
                        
            if self.is_graph_connected(graph):
                self.remove_hash_duplicates(graph, seen_graphs)
                
        return list(seen_graphs.values())
    
    def generate_subgraphs(self) -> List[List[IOGraph]]:
        """
        Generate all possible subgraphs of the family.
        
        Returns:
            list[list[IOGraph]]: A list of lists of generated subgraphs.
        """
        families_collection = []
        
        possible_combinations = []
        for num_inputs in range(1, self.max_nodes_level + 1):
            for num_outputs in range(1, self.max_nodes_level + 1):
                possible_combinations.append((num_inputs, num_outputs))
        possible_combinations = [combo for combo in possible_combinations if combo[0] <= combo[1] * 2]
        
        for combination in possible_combinations:
            print(f"Generating family for combination: {combination}")
            graph_family = self.generate_family(combination)
            self.redundancy_check(graph_family)
            print(f"Generated {len(graph_family)} graphs for combination {combination}")
            
            if graph_family:
                families_collection.append(graph_family)
        return families_collection
        
    def get_all_graphs_flat(self) -> List[IOGraph]:
        """
        Helper method to get all graphs as a flat list (not nested).
        Useful if you need individual graphs rather than families.
        
        Returns:
            list[IOGraph]: A flat list of all generated graphs.
        """
        families = self.generate_subgraphs()
        all_graphs = []
        
        for family in families:
            all_graphs.extend(family)
        return all_graphs
        
    def __repr__(self) -> str:
            return f"Family_Subgraph(name={self.name}, max_nodes_level={self.max_nodes_level})"
    

    def all_instances_of_subgraph(self, small_graph: IOGraph, big_graph : IOGraph ) -> Dict[IOGraph, dict]:
        """
        Find all instances of the subgraph within a larger graph.
        
        Args:
            graph (IOGraph): The larger graph to search within.
        
        Returns:
            List[IOGraph]: A list of IOGraph objects representing each instance of the subgraph found.
        """
        results = {}
        small_graph_nx = self.graph_to_networkx(small_graph)
        constraints_dict = {}
        seen_node_sets = set()
        for node in small_graph.nodes:
            pred = len(small_graph.predecessors(node))
            succ = len(small_graph.successors(node))
            if pred == 0: pred = 10
            if succ == 0: succ = 10
            constraints_dict[node.name] = Node_constraints(pred, succ)
            #print(f" node {node.name} can have at most {pred} predecessor nodes and at most {succ} successor nodes ")

        big_graph_nx = self.graph_to_networkx(big_graph)
        isomorphic_subgraphs: List[Dict[str, str]] = list(
            nx.algorithms.isomorphism.DiGraphMatcher(
            big_graph_nx, 
            small_graph_nx,
            node_match=lambda x, y: x['node_type'] == y['node_type']
            ).subgraph_isomorphisms_iter())
        #print(f"\n number of subgraphs found : {len(isomorphic_subgraphs)}")
        valid_matches = 0
    
        for i, mapping_dict in enumerate(isomorphic_subgraphs):
            #print(f"\nChecking subgraph instance {i+1}: {mapping_dict}")
            stop = False
            for idx,  key in enumerate(mapping_dict.keys()):
                constraint_node : Node_constraints = constraints_dict[mapping_dict[key]]
                if not constraint_node.respect_constraints(big_graph.__getitem__(key), big_graph):
                    #print(f"Instance {idx+ 1} of structure {i+1} matches the template structure")
                    stop = True
                    break
                    #print(f"==========DEBUG FAILED PATTERN===============")
                    #print(f" Instance {idx+ 1} of structure {i+1} was not compatible jumping to next iteration...")
                    #print(f"number of predecessors expected {constraint_node.max_pred_amount}")
                    #print(f"number of successors expected {constraint_node.max_succ_amount}")
                    
            if not stop:
                #print(f"DEBUG NUMBER OF VALID MATCHES FOUND SO FAR : {valid_matches}")
                valid_matches += 1
                
                matched_node_names = set(mapping_dict.keys())
                node_names_tuple = tuple(sorted(matched_node_names))
                if node_names_tuple in seen_node_sets:
                    continue 
                seen_node_sets.add(node_names_tuple)
                actual_inputs = []
                actual_outputs = []
                
                for big_name in matched_node_names:
                    external_predecessors = [pred.name for pred in big_graph.predecessors(big_name) 
                                        if pred.name not in matched_node_names]
                    external_successors = [succ.name for succ in big_graph.successors(big_name) 
                                        if succ.name not in matched_node_names]                    
                    if external_predecessors or not list(big_graph.predecessors(big_name)):
                        actual_inputs.append(big_name)
                        
                    if external_successors or not list(big_graph.successors(big_name)):
                        actual_outputs.append(big_name)
                
                node_types_dict = {}
                recreated_nodes = []
                
                for big_node_name in matched_node_names:
                    original_node = big_graph[big_node_name]
                    node_type = type(original_node).__name__
                    node_types_dict[big_node_name] = node_type
                    
                    if big_node_name in actual_inputs:
                        recreated_node = BoolVariable(
                            name=big_node_name,
                            weight=getattr(original_node, 'weight', 1),
                            in_subgraph=getattr(original_node, 'in_subgraph', False)
                        )
                    else:
                        operands = tuple(pred.name for pred in big_graph.predecessors(big_node_name) 
                                    if pred.name in matched_node_names)
                        
                        if isinstance(original_node, Not):
                            recreated_node = Not(
                                name=big_node_name,
                                operands=operands,
                                weight=getattr(original_node, 'weight', 1),
                                in_subgraph=getattr(original_node, 'in_subgraph', False)
                            )
                        elif isinstance(original_node, And):
                            recreated_node = And(
                                name=big_node_name,
                                operands=operands,
                                weight=getattr(original_node, 'weight', 1),
                                in_subgraph=getattr(original_node, 'in_subgraph', False)
                            )
                        elif isinstance(original_node, Or):
                            recreated_node = Or(
                                name=big_node_name,
                                operands=operands,
                                weight=getattr(original_node, 'weight', 1),
                                in_subgraph=getattr(original_node, 'in_subgraph', False)
                            )
                        elif isinstance(original_node, Xor):
                            recreated_node = Xor(
                                name=big_node_name,
                                operands=operands,
                                weight=getattr(original_node, 'weight', 1),
                                in_subgraph=getattr(original_node, 'in_subgraph', False)
                            )
                        else:
                            try:
                                recreated_node = type(original_node)(
                                    name=big_node_name,
                                    operands=operands,
                                    weight=getattr(original_node, 'weight', 1),
                                    in_subgraph=getattr(original_node, 'in_subgraph', False)
                                )
                            except:
                                recreated_node = BoolVariable(
                                    name=big_node_name,
                                    weight=getattr(original_node, 'weight', 1),
                                    in_subgraph=getattr(original_node, 'in_subgraph', False)
                                )
                    
                    recreated_nodes.append(recreated_node)
                
                recreated_subgraph = IOGraph(
                    nodes=recreated_nodes,
                    inputs_names=actual_inputs,
                    outputs_names=actual_outputs
                )
                
                results[recreated_subgraph] = node_types_dict
                
                # print(f"Added instance: {[node.name for node in recreated_nodes]}")
                # print(f"  Inputs: {actual_inputs}")
                # print(f"  Outputs: {actual_outputs}")
                # print(f"  Node types: {node_types_dict}")
            else: 
                continue

        print(f"\nTotal valid template instances found for generic method: {len(results)} out of {len(isomorphic_subgraphs)} potential matches")
        #print( results.values())
        return results  # Return dict instead of list

    
    def find_pattern_case1(self, graph: IOGraph) -> Dict[IOGraph, dict]:
        """
        Case 1: A -> B (one input, one output)
        Find nodes where A has exactly one successor B, and B has exactly one predecessor A
        """
        results = {}
        
        for node in graph.nodes:
            successors = list(graph.successors(node))
            
            if len(successors) == 1:
                top_node_dict: Dict[str, str] = {}
                successor = successors[0]
                predecessors = list(graph.predecessors(successor))
                if len(predecessors) == 1 and predecessors[0] == node:
                    top_node_type = type(node).__name__
                    top_node_dict[node.name] = top_node_type
                    input_node = BoolVariable(
                        name=node.name,
                        weight=getattr(node, 'weight', 1),
                        in_subgraph=getattr(node, 'in_subgraph', False)
                    )
                    
                    if isinstance(successor, Not):
                        output_node = Not(
                            name=successor.name,
                            operands=(node.name,),
                            weight=getattr(successor, 'weight', 1),
                            in_subgraph=getattr(successor, 'in_subgraph', False)
                        )
                    elif isinstance(successor, And):
                        output_node = And(
                            name=successor.name,
                            operands=(node.name,),
                            weight=getattr(successor, 'weight', 1),
                            in_subgraph=getattr(successor, 'in_subgraph', False)
                        )
                    else:
                        try:
                            output_node = type(successor)(
                                name=successor.name,
                                operands=(node.name,),
                                weight=getattr(successor, 'weight', 1),
                                in_subgraph=getattr(successor, 'in_subgraph', False)
                            )
                        except:
                            output_node = BoolVariable(
                                name=successor.name,
                                weight=getattr(successor, 'weight', 1),
                                in_subgraph=getattr(successor, 'in_subgraph', False)
                            )
                    
                    pattern_nodes = [input_node, output_node]
                    pattern_graph = IOGraph(
                        nodes=pattern_nodes,
                        inputs_names=[node.name],
                        outputs_names=[successor.name]
                    )
                    results[pattern_graph] = top_node_dict
        
        print(f"Total Case 1 patterns found: {len(list(results.keys()))}")
        return results


    def find_pattern_case2(self, graph: IOGraph) -> Dict[IOGraph, dict]:
        """
        Case 2: Multiple top nodes -> One bottom node
        - Top nodes can have any number of inputs (doesn't matter)
        - Each top node has exactly one successor (the bottom node)
        - Bottom node can ONLY have the top nodes as predecessors
        - Bottom node can have any number of successors
        """
        result_dict = {}
        
        for bottom_node in graph.nodes:
            predecessors = list(graph.predecessors(bottom_node))
            if not predecessors:
                continue
            valid_case2 = True
            top_nodes = []
            top_nodes_dict: Dict[str, str] = {}

            
            for pred in predecessors:
                pred_successors = list(graph.successors(pred))
                if len(pred_successors) != 1 or pred_successors[0] != bottom_node:
                    valid_case2 = False
                    break
                top_nodes.append(pred)
            
            if valid_case2 and len(top_nodes) >= 2: 
                
                pattern_nodes = []
                top_node_names = []
                for i, top_node in enumerate(top_nodes):
                    top_node_type = type(top_node).__name__
                    top_nodes_dict[top_node.name] = top_node_type
                    new_top_node = BoolVariable(
                        name=top_node.name,
                        weight=getattr(top_node, 'weight', 1),
                        in_subgraph=getattr(top_node, 'in_subgraph', False)
                    )
                    pattern_nodes.append(new_top_node)
                    top_node_names.append(top_node.name)
                if isinstance(bottom_node, And):
                    new_bottom_node = And(
                        name=bottom_node.name,
                        operands=tuple(top_node_names),
                        weight=getattr(bottom_node, 'weight', 1),
                        in_subgraph=getattr(bottom_node, 'in_subgraph', False)
                    )
                elif isinstance(bottom_node, Or):
                    new_bottom_node = Or(
                        name=bottom_node.name,
                        operands=tuple(top_node_names),
                        weight=getattr(bottom_node, 'weight', 1),
                        in_subgraph=getattr(bottom_node, 'in_subgraph', False)
                    )
                elif isinstance(bottom_node, Xor):
                    new_bottom_node = Xor(
                        name=bottom_node.name,
                        operands=tuple(top_node_names),
                        weight=getattr(bottom_node, 'weight', 1),
                        in_subgraph=getattr(bottom_node, 'in_subgraph', False)
                    )
                else:
                    try:
                        new_bottom_node = type(bottom_node)(
                            name=bottom_node.name,
                            operands=tuple(top_node_names),
                            weight=getattr(bottom_node, 'weight', 1),
                            in_subgraph=getattr(bottom_node, 'in_subgraph', False)
                        )
                    except:
                        new_bottom_node = And(
                            name=bottom_node.name,
                            operands=tuple(top_node_names),
                            weight=getattr(bottom_node, 'weight', 1),
                            in_subgraph=getattr(bottom_node, 'in_subgraph', False)
                        )
                
                pattern_nodes.append(new_bottom_node)
                #print(top_node)
                #print( "="*20 +"printing pattern nodes for a subgraph" + "="*20 )
                # for node in pattern_nodes:
                #     print(f"pattern nodes length : {node.name}")
                pattern_graph = IOGraph(
                    nodes=pattern_nodes,
                    inputs_names=top_node_names,  
                    outputs_names=[bottom_node.name]
                )
                result_dict[pattern_graph] = top_nodes_dict
        
        print(f"Total Case 2 patterns found for rigid-made method: {len(list(result_dict.keys()))}")
        return result_dict

    def _extract_iograph_subgraph(self, original_graph: IOGraph, node_names: Set[str]) -> IOGraph:
        """
        Extract a subgraph as IOGraph from the original graph given a set of node names.
        
        Args:
            original_graph (IOGraph): The original graph
            node_names (Set[str]): Set of node names to include in subgraph
            
        Returns:
            IOGraph: The extracted subgraph, or None if invalid
        """
        try:
            subgraph_nodes = []
            for node in original_graph.nodes:
                if node.name in node_names:
                    subgraph_nodes.append(node)
            
            if len(subgraph_nodes) != len(node_names):
                return None  
            
            subgraph_inputs = []
            subgraph_outputs = []
            
            for node_name in node_names:
                node = original_graph[node_name]
                
                external_preds = [pred.name for pred in original_graph.predecessors(node_name)
                                if pred.name not in node_names]
                
                external_succs = [succ.name for succ in original_graph.successors(node_name)
                                if succ.name not in node_names]
                
                if external_preds or not list(original_graph.predecessors(node_name)):
                    subgraph_inputs.append(node_name)
                
                if external_succs or not list(original_graph.successors(node_name)):
                    subgraph_outputs.append(node_name)
            
            return IOGraph(
                nodes=subgraph_nodes,
                inputs_names=subgraph_inputs,
                outputs_names=subgraph_outputs
            )
            
        except Exception as e:
            print(f"    Error extracting subgraph {node_names}: {e}")
            return None
    # def generate_connected_subgraphs_optimized(self, graph: nx.Graph, size: int):
    #     """Optimized version with early pruning and memoization"""
    #     subgraphs = set()
    #     visited_combinations = set()
        
    #     def can_reach_size(current_nodes, target_size) -> Set[Set[str]]: 
    #         """Check if we can possibly reach target size from current nodes"""
    #         if len(current_nodes) >= target_size:
    #             return True
            
    #         # BFS to count reachable nodes
    #         reachable = set(current_nodes)
    #         frontier = set()
    #         for node in current_nodes:
    #             frontier.update(graph.neighbors(node))
    #         frontier -= current_nodes
            
    #         while frontier and len(reachable) < target_size:
    #             next_frontier = set()
    #             for node in frontier:
    #                 reachable.add(node)
    #                 if len(reachable) >= target_size:
    #                     return True
    #                 next_frontier.update(graph.neighbors(node))
    #             frontier = next_frontier - reachable
            
    #         return len(reachable) >= target_size
        
    #     def dfs_with_pruning(current_nodes, boundary_nodes):
    #         current_key = frozenset(current_nodes)
    #         if current_key in visited_combinations:
    #             return
    #         visited_combinations.add(current_key)
            
    #         if len(current_nodes) == size:
    #             subgraphs.add(current_key)
    #             return
            
    #         if not can_reach_size(current_nodes, size):
    #             return  # Pruning: can't reach target size
            
    #         for node in list(boundary_nodes):
    #             new_current = current_nodes | {node}
    #             new_boundary = boundary_nodes | set(graph.neighbors(node))
    #             new_boundary.discard(node)
    #             new_boundary -= current_nodes
                
    #             dfs_with_pruning(new_current, new_boundary)
        
    #     for start_node in graph.nodes():
    #         dfs_with_pruning({start_node}, set(graph.neighbors(start_node)))
        
    #     return subgraphs
    
    # def find_top_common_subgraph_patterns_detailed(
    #         self,
    #         graph: IOGraph,
    #         subgraph_size: int,
    #         top_n: int = 5
    #     ) -> List[Tuple[str, int, Set[str], Dict[str, Any]]]:
    #     """
    #     Find the top N most common connected subgraph patterns with detailed structure info
        
    #     Returns:
    #         List[Tuple[str, int, Set[str], Dict]]: 
    #         List of (pattern_description, count, example_nodes, structure_info) sorted by frequency
    #     """
    #     nx_graph = self.graph_to_networkx(graph)
    #     subgraph_node_sets = self.generate_connected_subgraphs_optimized(nx_graph, subgraph_size)
        
    #     pattern_counts = {}
    #     pattern_examples = {}
    #     pattern_structures = {}
        
    #     for node_set in subgraph_node_sets:
    #         structure_info = self.describe_subgraph_structure(node_set, graph)
    #         pattern_key = structure_info['pattern_signature']
            
    #         if pattern_key in pattern_counts:
    #             pattern_counts[pattern_key] += 1
    #         else:
    #             pattern_counts[pattern_key] = 1
    #             pattern_examples[pattern_key] = node_set
    #             pattern_structures[pattern_key] = structure_info
        
    #     most_common = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
    #     result = []
    #     for pattern_key, count in most_common:
    #         example = pattern_examples[pattern_key]
    #         structure = pattern_structures[pattern_key]
    #         result.append((pattern_key, count, example, structure))
        
    #     return result


def main(gv_folder: str = "generated_graphs_gv", png_folder: str = "generated_graphs_png", max_nodes: int = 7):
    os.makedirs(gv_folder, exist_ok=True)
    os.makedirs(png_folder, exist_ok=True)
    family = Family_Subgraph(name="auto_family", max_nodes_level=max_nodes)
    all_graphs = family.get_all_graphs_flat()
    for idx, io_graph in enumerate(all_graphs):
        print(io_graph)
        gv_path = os.path.join(gv_folder, f"graph_{idx}.gv")
        GraphVizPorter.to_file(io_graph, gv_path)
        png_path = os.path.join(png_folder, f"graph_{idx}.png")
        subprocess.run(["dot", "-Tpng", gv_path, "-o", png_path], check=True)




if __name__ == "__main__":
    main()