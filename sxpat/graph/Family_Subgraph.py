"""
this file implements a class called Family Subgraph that can generate any given number of pattern
and that implements a function called all_instances_of_subgraph that given an example pattern
finds all occurences of that pattern in a bigger subgraph
I am leaving this here if you need to do any more research 
"""

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
    """
    Represents constraints on the number of predecessors and successors a node can have in a graph.
    Attributes:
        max_pred_amount (int): Maximum allowed number of predecessors for a node.
        max_succ_amount (int): Maximum allowed number of successors for a node.
    Methods:
        respect_constraints(node: Node, graph: IOGraph) -> bool:
            Checks if the given node in the graph respects the specified predecessor and successor constraints.
            Args:
                node (Node): The node to check constraints for.
                graph (IOGraph): The graph containing the node.
            Returns:
                bool: True if the node respects the constraints, False otherwise.
    @ author : Thibaud Babin
    """
    @classmethod
    def __init__(self, max_pred_amount: int, max_succ_amount: int)-> None :
        self.max_pred_amount = max_pred_amount
        self.max_succ_amount = max_succ_amount
    @classmethod
    def respect_constraints(self, node : Node, graph : IOGraph) -> bool:
        """
        Checks if the given node in the graph respects the constraints on the number of predecessors and successors.
        The constraints are defined by `self.max_pred_amount` and `self.max_succ_amount`. If either is set to 10, only the other constraint is checked. Otherwise, both constraints must be satisfied.
        Args:
            node (Node): The node to check constraints for.
            graph (IOGraph): The graph containing the node.
        Returns:
            bool: True if the node respects the constraints, False otherwise.
        @author: Thibaud Babin
        """
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
    @classmethod
    def is_redundant(self, graph: Graph) -> bool:
        """ Determines if the given graph contains redundant operations among its output nodes.
        The method iterates over all nodes in the graph, focusing on nodes whose names start with 'o'
        (assumed to be output nodes). For each output node, it checks if another output node performs
        the same operation (based on the node's type and sorted operands). If such redundancy is found,
        the method returns True.
        Args:
            graph (Graph): The graph object containing nodes to be checked for redundancy.
        Returns:
            bool: True if redundant operations are found among output nodes, False otherwise.
        # Steps:
        # 1. Initialize a dictionary to track unique operation signatures for output nodes.
        # 2. Iterate through all nodes in the graph.
        # 3. For each output node (name starts with 'o'), create an operation signature using its type and operands.
        # 4. If the signature already exists, redundancy is detected and True is returned.
        # 5. Otherwise, store the signature and continue.
        # 6. If no redundancy is found after checking all nodes, return False.
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

    @classmethod
    def graph_to_networkx(self, graph: IOGraph) -> nx.DiGraph:
        """Convert IOGraph to NetworkX for isomorphism checking.
        Args:
            graph (IOGraph): The graph to convert.
        Returns:
            nx.DiGraph: A directed graph representation of the IOGraph.
        @author: Thibaud Babin
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
    @classmethod
    def are_graphs_isomorphic(self, graph1: IOGraph, graph2: IOGraph) -> bool:
        """Check if two graphs are structurally identical (isomorphic).
        Args:
            graph1 (IOGraph): First graph to compare.
            graph2 (IOGraph): Second graph to compare.
        Returns:
            bool: True if the graphs are isomorphic, False otherwise.
        @author: Thibaud Babin
        """
        nx_graph1 = self.graph_to_networkx(graph1)
        nx_graph2 = self.graph_to_networkx(graph2)
        
        return nx.is_isomorphic(nx_graph1, nx_graph2, 
                               node_match=lambda x, y: x['node_type'] == y['node_type'])
    @classmethod
    def remove_isomorphic_duplicates(self, graphs: List[IOGraph]) -> List[IOGraph]:
        """Remove isomorphic duplicates from a list of graphs.
        Args:
            graphs (List[IOGraph]): List of IOGraph objects to check for isomorphism. 

        Returns:
            List[IOGraph]: A list of unique IOGraph objects, with duplicates removed.
        @author : Thibaud Babin
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
    @classmethod
    def is_graph_connected(self, graph: IOGraph) -> bool:
        """
        Check if the graph is connected (all nodes are reachable).
        Args:
            graph (IOGraph): The graph to check.
        Returns:
            bool: True if the graph is connected, False otherwise.
        @author : Thibaud Babin
        """
        nxGraph = self.graph_to_networkx(graph)
        return nx.is_connected(nxGraph.to_undirected())

    @classmethod
    def remove_hash_duplicates(self,graph : IOGraph, seen_graphs : Dict[nx.DiGraph, IOGraph]) -> None:
        """
        Remove isomorphic duplicates from the list of graphs.
        This method uses NetworkX weisfeiler_lehman_graph_hash to check for isomorphism
        Args:
            graph (IOGraph): The graph to check for duplicates.
            seen_graphs (dict[nx.DiGraph, IOGraph]): Dictionary to store unique graphs by their hash.
        Returns:
            None: The input list is modified in place to remove redundant graphs.
        @author: Thibaud Babin
        """
        nx_graph = self.graph_to_networkx(graph)
        graph_hash = nx.weisfeiler_lehman_graph_hash(
            nx_graph, 
            node_attr=None)
        
        if graph_hash not in seen_graphs:
            seen_graphs[graph_hash] = graph
        

    @classmethod
    def redundancy_check(self, graphs: List[IOGraph]) -> None:
        """
        Check if the subgraph is redundant in the context of the given graphs.
        remove from the list all graphs that are redundant with this subgraph.
        Args:
            graphs (list[IOGraph]): List of IOGraph objects to check for redundancy.
        Returns:
            None: The input list is modified in place to remove redundant graphs.
        @author: Thibaud Babin
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

    @classmethod
    def generate_family(self, combination: Tuple[int, int]) -> List[IOGraph]:
        """Generates all possible unique graphs for a given "family", defined by a specific number of input and output nodes.
        For each family, the function creates all valid combinations of connections between input nodes and output nodes,
        ensuring that every input is used at least once. Output nodes are constructed as either NOT gates (for single input)
        or AND gates (for multiple inputs). Only connected graphs are retained, and duplicates are removed using a hash-based approach.
        I made this functio to create patterns and test them against graphs to see how often they would appear
        Args:
            combination (Tuple[int, int]): 
                A tuple containing two integers:
                    - The first integer specifies the number of input nodes.
                    - The second integer specifies the number of output nodes.
        Returns:
            List[IOGraph]: 
                A list of unique, connected IOGraph objects representing all possible graphs for the specified family.
        @author: Thibaud Babin 
        """
        input_nodes: List[Node] = []
        num_inputs, num_outputs = combination
        valid_graphs = []
        seen_graphs: Dict[str, IOGraph] = {}  
                
        for i in range(num_inputs):
            input_nodes.append(BoolVariable(name=f'i{i}', weight=None, in_subgraph=False))
                
        total_base_connections = num_inputs + (num_inputs * (num_inputs - 1) // 2)
        print("number of possible connections for combination :", combination,
            num_outputs * total_base_connections)
                
        #Build all possible base connections between input nodes
        base_connections = []
        # Each input can be connected individually (single input NOT)
        for inp_idx in range(num_inputs):
            base_connections.append([inp_idx])
        # Each pair of inputs can be connected together (for AND gates)
        for inp1_idx in range(num_inputs):
            for inp2_idx in range(inp1_idx + 1, num_inputs):
                base_connections.append([inp1_idx, inp2_idx])
        
        #Convert connections to tuples for easier handling and sorting
        tuple_connections = [tuple(sorted(conn)) for conn in base_connections]
        
        # Generate all possible output connection patterns using combinations_with_replacement
        # Each output node will be assigned a connection pattern
        for pattern in combinations_with_replacement(tuple_connections, num_outputs):
            output_connections = [list(conn) for conn in pattern]
            
            # Step 4: Ensure every input is used at least once in the output connections
            used_inputs = set()
            for connections in output_connections:
                used_inputs.update(connections)
            
            if len(used_inputs) != num_inputs:
                continue  # important, skip patterns that don't use all inputs
            
            # Step 5: Prepare the list of nodes for the graph
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
    @classmethod
    def generate_subgraphs(self, max_nodes: int) -> List[List[IOGraph]]:
        """
        Generate all possible subgraphs of the family.
        
        Returns:
            list[list[IOGraph]]: A list of lists of generated subgraphs.
        @author: Thibaud Babin
        """
        families_collection = []
        
        possible_combinations = []
        for num_inputs in range(1, max_nodes + 1):
            for num_outputs in range(1, max_nodes + 1):
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
    @classmethod
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
            small_graph (IOGraph): The subgraph pattern to search for (a template of the pattern).
            big_graph (IOGraph): The larger graph to search within.

        Returns:
            Dict[IOGraph, dict]: A dictionary mapping each found subgraph instance (as IOGraph)
                                 to a dict of node names and their types.
                                 the inner dict is the correspondence of a gate of a found instance to the gate
                                 of the pattern template given --> to wich gate of the given pattern template does
                                 the one in the found subgraph correspond to
        @author: Thibaud Babin"""
        #honestly now that I reread this after 5 weeks I don't know what I was on when I did that but I barely ¨
        #understand  what I did there I did my best of explaining it
        # Initialize results dictionary to store valid subgraph instances
        results = {}
        
        # Convert the small pattern graph to NetworkX format for isomorphism checking
        small_graph_nx = self.graph_to_networkx(small_graph)
        
        # Create constraints dictionary to store predecessor/successor requirements for each node in the pattern
        constraints_dict = {}
        
        # Track already found node sets to avoid duplicates
        seen_node_sets = set()
        
        # Build constraints for each node in the pattern based on their connectivity
        for node in small_graph.nodes:
            pred = len(small_graph.predecessors(node))
            succ = len(small_graph.successors(node))
            # Use 10 as a sentinel value for nodes with no predecessors/successors (likely inputs/outputs)
            if pred == 0: pred = 10
            if succ == 0: succ = 10
            constraints_dict[node.name] = Node_constraints(pred, succ)
            #print(f" node {node.name} can have at most {pred} predecessor nodes and at most {succ} successor nodes ")

        # Convert the large target graph to NetworkX format
        big_graph_nx = self.graph_to_networkx(big_graph)
        
        # Find all potential structural matches using NetworkX's subgraph isomorphism algorithm
        # This finds matches based on graph topology and node types
        isomorphic_subgraphs: List[Dict[str, str]] = list(
            nx.algorithms.isomorphism.DiGraphMatcher(
            big_graph_nx, 
            small_graph_nx,
            node_match=lambda x, y: x['node_type'] == y['node_type']
            ).subgraph_isomorphisms_iter())
        #print(f"\n number of subgraphs found : {len(isomorphic_subgraphs)}")
        
        # Counter for valid matches that pass all constraints
        valid_matches = 0
    
        # Iterate through each potential structural match to validate it
        for i, mapping_dict in enumerate(isomorphic_subgraphs):
            #print(f"\nChecking subgraph instance {i+1}: {mapping_dict}")
            
            # Flag to indicate if this match should be rejected
            stop = False
            
            # Validate each node in the match against the pattern constraints
            for idx,  key in enumerate(mapping_dict.keys()):
                constraint_node : Node_constraints = constraints_dict[mapping_dict[key]]
                
                # Check if the matched node in the big graph respects the connectivity constraints
                # from the pattern template
                if not constraint_node.respect_constraints(big_graph.__getitem__(key), big_graph):
                    #print(f"Instance {idx+ 1} of structure {i+1} matches the template structure")
                    stop = True
                    break
                    #print(f"==========DEBUG FAILED PATTERN===============")
                    #print(f" Instance {idx+ 1} of structure {i+1} was not compatible jumping to next iteration...")
                    #print(f"number of predecessors expected {constraint_node.max_pred_amount}")
                    #print(f"number of successors expected {constraint_node.max_succ_amount}")
                    
            # If all constraints are satisfied, process this valid match
            if not stop:
                #print(f"DEBUG NUMBER OF VALID MATCHES FOUND SO FAR : {valid_matches}")
                valid_matches += 1
                
                # Get the set of matched node names and check for duplicates
                matched_node_names = set(mapping_dict.keys())
                node_names_tuple = tuple(sorted(matched_node_names))
                
                # Skip if we've already processed this exact set of nodes
                if node_names_tuple in seen_node_sets:
                    continue 
                seen_node_sets.add(node_names_tuple)
                
                # Determine which matched nodes are inputs/outputs of the subgraph instance
                actual_inputs = []
                actual_outputs = []
                
                # For each matched node, check its external connections
                for big_name in matched_node_names:
                    # Find predecessors that are outside the matched subgraph
                    external_predecessors = [pred.name for pred in big_graph.predecessors(big_name) 
                                        if pred.name not in matched_node_names]
                    # Find successors that are outside the matched subgraph
                    external_successors = [succ.name for succ in big_graph.successors(big_name) 
                                        if succ.name not in matched_node_names]                    
                    
                    # A node is an input if it has external predecessors OR no predecessors at all
                    if external_predecessors or not list(big_graph.predecessors(big_name)):
                        actual_inputs.append(big_name)
                        
                    # A node is an output if it has external successors OR no successors at all
                    if external_successors or not list(big_graph.successors(big_name)):
                        actual_outputs.append(big_name)
                
                # Build mapping of node names to their types for the result
                node_types_dict = {}
                
                # List to store the recreated nodes for the new IOGraph
                recreated_nodes = []
                
                # Recreate each matched node as a new node object for the subgraph instance
                for big_node_name in matched_node_names:
                    original_node = big_graph[big_node_name]
                    node_type = type(original_node).__name__
                    node_types_dict[big_node_name] = node_type
                    
                    # Handle input nodes (create as BoolVariable)
                    if big_node_name in actual_inputs:
                        recreated_node = BoolVariable(
                            name=big_node_name,
                            weight=getattr(original_node, 'weight', 1),
                            in_subgraph=getattr(original_node, 'in_subgraph', False)
                        )
                    else:
                        # For non-input nodes, get their operands from within the matched subgraph
                        operands = tuple(pred.name for pred in big_graph.predecessors(big_node_name) 
                                    if pred.name in matched_node_names)
                        
                        # Recreate the appropriate gate type based on the original node
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
                            # Try to create the same type as the original node
                            try:
                                recreated_node = type(original_node)(
                                    name=big_node_name,
                                    operands=operands,
                                    weight=getattr(original_node, 'weight', 1),
                                    in_subgraph=getattr(original_node, 'in_subgraph', False)
                                )
                            except:
                                # Fallback to BoolVariable if recreation fails
                                recreated_node = BoolVariable(
                                    name=big_node_name,
                                    weight=getattr(original_node, 'weight', 1),
                                    in_subgraph=getattr(original_node, 'in_subgraph', False)
                                )
                    
                    recreated_nodes.append(recreated_node)
                
                # Create a new IOGraph instance representing this subgraph match
                recreated_subgraph = IOGraph(
                    nodes=recreated_nodes,
                    inputs_names=actual_inputs,
                    outputs_names=actual_outputs
                )
                
                # Store the recreated subgraph and its node type mapping in results
                results[recreated_subgraph] = node_types_dict
                
                # Debug output (commented out)
                # print(f"Added instance: {[node.name for node in recreated_nodes]}")
                # print(f"  Inputs: {actual_inputs}")
                # print(f"  Outputs: {actual_outputs}")
                # print(f"  Node types: {node_types_dict}")
            else: 
                # Skip this match if constraints were not satisfied
                continue

        print(f"\nTotal valid template instances found for generic method: {len(results)} out of {len(isomorphic_subgraphs)} potential matches")
        #print( results.values())
        
        return results  

    
    def find_pattern_case1(self, graph: IOGraph) -> Dict[IOGraph, dict]:
        """
        finds all occurences of a case1 pattern

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
        finds every occurence of a case2 pattern
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