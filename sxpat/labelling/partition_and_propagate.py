from __future__ import annotations
from collections import defaultdict


import networkx as nx
import itertools
from itertools import islice


# MARCO-COMMENT: 
# (This is not a requirement, just a suggestion in case you are interested)
# If you want, you can expand and improve the typing of your code;
# the way to this in python is through type annotations.
# 
# These annotations do not force a type (like in C), but are helpful for 
# development and for the users of your code; if you IDE supports it, it
# may even allow for some autocomplete or better hints.
# 
# Type annotations have many features, such as generic types, but can also
# be used more simply though concrete types.
# 
# An example of using type annotations for generic types can be seen in 
# the UnionFind class.
from typing import (
    TypeVar,      
    Generic,      
    Dict,         
    List,        
    Set,          
    Tuple,        
    Iterable,     
    Mapping,    
    DefaultDict, 
)
T = TypeVar('T')


NodeID = str
SubID = str
OutNodeID = str
NodeTag = str
NodeWeight = int

# 
# Once you start using type annotations with an IDE that understands them, 
# you will see that in many cases the type annotations get propagated.
# 
# From the example I gave you, I think you will be able to understand how 
# type annotations work, if you are interested in exploring more of what they
# allow you to do you can find more in the documentation
# (https://docs.python.org/3.8/library/typing.html), or if you have specific
# questions/doubts you can always ask me.

# MARCO-COMMENT:
# (This is not a requirement, just a suggestion in case you are interested)
# When working with data you do not plan to change, it is usually better
# to use immutable data structures, to make it clear that it is not planned for change
# and to prevent accidental modifications; depending on the data structure and 
# its use-case it could also bring an improvement in performance (less memory, faster operations, etc.).
# 
# In python you will see very performance improvement (if any), but the approach
# is still beneficial for readability and development.
# 
# An example would be in the get_subgraph_inputs(...) function: instead of using a set()
# for sub_nodes, you could use a frozenset().


# MARCO-REVIEW (2026-04-24 11:45)
# - ALL GOOD
# Union find class
class UnionFind(Generic[T]):
    def __init__(self, nodes: Iterable[T]):
        self.parent = {node: node for node in nodes}
        # MARCO-COMMENT: Here self.parent gets the implicit type of dict[T,T],
        #                but if you prefer you can make the annotation explicit.
        # self.parent: Dict[T, T] = {node: node for node in nodes}

    # get root and use path compression optimization
    def find(self, i: T) -> T:
        root=i
        while self.parent[root]!=root:
            root = self.parent[root]
        while self.parent[i] != root:
            new_p = self.parent[i]
            self.parent[i] = root
            i = new_p
        return root

    # if u and v belongs to different union,let v point to u
    def union(self, u: T, v: T) -> None:
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        self.parent[root_v] = root_u

# MARCO-REVIEW (2026-04-24 13:55)
# - a few more high-level comments would be helpful (places marked below)
# - rest is all good
def label_nodes(graph: nx.DiGraph[NodeID]
                ) -> DefaultDict[SubID,List[NodeID]]:
    """
    use union find label nodes
    """
    uf = UnionFind(graph.nodes)
    
    # MARCO-MARK: add a brief high-level comment of the block
    for node in graph.nodes:
        if graph.out_degree(node) <= 1: 
            continue
        
        children = [child for child in graph.successors(node) 
                    if not graph.nodes[child].get("label", "").startswith("out")]
        
        if len(children) > 1:
            first_child = children[0]
            for other_child in islice(children, 1, None):
                uf.union(first_child, other_child)

    # 2. map UnionFind to Graph and  Subgraph dictionary
    nodes_by_subid = defaultdict(list)
    
    for node in graph.nodes:
        label = graph.nodes[node].get("label", "")
        
        # do not combine Primary In/Out 
        if label.startswith("out") or label.startswith("in"):
            sub_id = node
        else:
            sub_id = uf.find(node)
        
        graph.nodes[node]['subgraph_id'] = sub_id

        nodes_by_subid[sub_id].append(node)
        
    return nodes_by_subid

# MARCO-REVIEW (2026-04-24 14:05)
# - ALL GOOD
# use nodes_by_subid to create a graph
def build_sub_id_graph(graph:nx.DiGraph[NodeID], 
                       nodes_by_subid:DefaultDict[SubID,List[NodeID]]
                       )->nx.DiGraph[SubID]:
    # create empty graph
    sub_id_graph = nx.DiGraph()
    # add nodes
    sub_id_graph.add_nodes_from(nodes_by_subid.keys())
    
    # add edges
    for u, v in graph.edges:
        sid_u = graph.nodes[u]['subgraph_id']
        sid_v = graph.nodes[v]['subgraph_id']
        
        if sid_u != sid_v:
            sub_id_graph.add_edge(sid_u, sid_v)
            
    return sub_id_graph

# MARCO-REVIEW (2026-04-24 14:15)
# - some questions (see below)
# - the rest is all good
# Use strongly connected components to find circle and merge circle
def merge_cycles(
        graph:nx.DiGraph[NodeID], 
        nodes_by_subid:DefaultDict[SubID,List[NodeID]]
        )->DefaultDict[SubID,List[NodeID]]:
    
    sub_id_graph = build_sub_id_graph(graph, nodes_by_subid)
    
    # 1. find all scc 
    # the results is like [{A, B}, {C}, {D, E, F}] A-F is the id of each node in sub_id_graph
    sccs = list(nx.strongly_connected_components(sub_id_graph))
    
    # 2. if the length of  SCC > 1，it has circle
    for scc in sccs:
        if len(scc) > 1:
            # MARCO-QUESTION: How do you make sure that the scc_list[0] is the id of the subgraph?
            #                 Couldn't it be that you have some other node at position 0?
            scc_list = list(scc)
            main_id = scc_list[0]
            
            # union other sub id
            for secondary_id in scc_list[1:]:
                # A. move all the nodes to main_id
                nodes_by_subid[main_id].extend(nodes_by_subid[secondary_id])
                
                # B. renew subgraph_id of each node
                for node in nodes_by_subid[secondary_id]:
                    graph.nodes[node]['subgraph_id'] = main_id
                
                # C.delete secondary_id
                del nodes_by_subid[secondary_id]
                
    return nodes_by_subid

# MARCO-REVIEW (2026-04-24 14:20)
# - ALL GOOD
# find all input nodes of nodes_in_sub
# def get_subgraph_inputs(nodes_in_sub, graph:nx.DiGraph[str]):
#     """
#     The input set for computing the subgraph is all nodes that are not inside the subgraph but point to nodes inside the subgraph.

#     """
#     sub_nodes = set(nodes_in_sub)
#     inputs = set()
#     for node in sub_nodes:
#         for pred in graph.predecessors(node):
#             if pred not in sub_nodes:
#                 inputs.add(pred)
#     return inputs


# MARCO-REVIEW (2026-04-24 14:30)
# - ALL GOOD
def get_all_subgraph_boundaries(graph:nx.DiGraph[NodeID],
                                nodes_by_subid:DefaultDict[SubID,List[NodeID]]
                                )->Tuple[DefaultDict[SubID,Set[NodeID]],
                                         DefaultDict[SubID,Set[NodeID]]]:
    """
    Traverse the entire graph in one go and calculate the input and output sets of all subgraphs.

    inputs_map: {sid: {all external nodes pointing to this group}}
    """
    inputs_map = defaultdict(set)
    outputs_map = defaultdict(set)
    
    for u, v in graph.edges:
        sid_u = graph.nodes[u]['subgraph_id']
        sid_v = graph.nodes[v]['subgraph_id']
         
        if sid_u != sid_v:

            inputs_map[sid_v].add(u)
            outputs_map[sid_u].add(u)
            
    return inputs_map, outputs_map

# MARCO-REVIEW (2026-04-24 14:45)
# - ALL GOOD
# - a few comments (see below)
def greedy_merge(graph:nx.DiGraph[NodeID], 
                 nodes_by_subid:DefaultDict[SubID,List[NodeID]],
                 inputs_map:DefaultDict[SubID,Set[NodeID]]
                 )->DefaultDict[SubID,List[NodeID]]:
    
    # 1. Initial construction of the metagraph
    sub_id_graph = build_sub_id_graph(graph, nodes_by_subid)

    # 2.Store the input set of each subgraph into the metagraph node.
    for sid in sub_id_graph.nodes:
        sub_id_graph.nodes[sid]['inputs'] = inputs_map[sid]

    changed = True
    while changed:
        changed = False
        
        # Traverse the edges of the graph and look for merging opportunities.
        #use list to avoid delete the edges
        for u, v in list(sub_id_graph.edges):
            # if has deleted u or v
            if not sub_id_graph.has_node(u) or not sub_id_graph.has_node(v):
                continue

            # if it is input or output node(we do not merge primary input/output into othe subgraph node)
            u_is_boundary = str(u).startswith('in') or str(u).startswith('out')
            v_is_boundary = str(v).startswith('in') or str(v).startswith('out')
            
            if u_is_boundary or v_is_boundary:
                continue
            
            inputs_u = sub_id_graph.nodes[u]['inputs']
            inputs_v = sub_id_graph.nodes[v]['inputs']
            
            # calculate the inputs after merge
            nodes_u = frozenset(nodes_by_subid[u])
            nodes_v = frozenset(nodes_by_subid[v])

            inputs_merged = (inputs_u | inputs_v) - (nodes_u | nodes_v)
            

            if len(inputs_merged) <= max(len(inputs_u), len(inputs_v)):
                
                # --- Perform the merge (merge v into u) ---
                
                # 1. Update main graph attributes
                for node in nodes_by_subid[v]:
                    graph.nodes[node]['subgraph_id'] = u
                
                # 2. Update group dictionary
                nodes_by_subid[u].extend(nodes_by_subid[v])
                del nodes_by_subid[v]
                
                # 3. Merge the information of v into u
                # Update u's inputs
                sub_id_graph.nodes[u]['inputs'] = inputs_merged
                

                # Reconnect the edges (connect all of v's neighbors to u).
                # MARCO-COMMENT: Why are you casting this to a list? for this use-case you can simply loop over the .successors(v)
                for successor in list(sub_id_graph.successors(v)):
                    if successor != u:
                        sub_id_graph.add_edge(u, successor)
                for predecessor in list(sub_id_graph.predecessors(v)):
                    if predecessor != u:
                        sub_id_graph.add_edge(predecessor, u)
                
                # Remove v from the metagraph
                sub_id_graph.remove_node(v)

                changed = True
                # MARCO-COMMENT: Why do you break here? Is it for performance, for correctness, or for some other reason?
                #Beacause the whole graph has changed(we merge some subgraph), we start the whole progress in new graph
                break 
    
    return nodes_by_subid

# MARCO-REVIEW (2026-04-24 14:50)
# - ALL GOOD
def apply_constraints(graph:nx.DiGraph[NodeID], 
                      nodes_by_subid:DefaultDict[SubID,List[NodeID]],
                      TI_LIMIT:int,
                      inputs_map:DefaultDict[SubID,Set[NodeID]]
                      )-> DefaultDict[SubID,List[NodeID]]:
    """
    Check the input nodes of each subgraph; if the number exceed TI_LIMIT, break the group down into individual nodes.
    """
    new_nodes_by_subid = defaultdict(list)
    
    for sid, nodes in nodes_by_subid.items():

        if len(inputs_map[sid]) > TI_LIMIT:

            for node in nodes:
                graph.nodes[node]['subgraph_id'] = node
                new_nodes_by_subid[node].append(node)

        else:

            for node in nodes:
                graph.nodes[node]['subgraph_id'] = sid
                new_nodes_by_subid[sid].append(node)
                
    return new_nodes_by_subid

# input:op is string; bits is list of 0/1 [0,1]
def apply_logic(op:str,
                inputs:List[int]
                )-> int:
    if op == 'and':
        return 1 if all(inputs) else 0
    elif op == 'or':
        return 1 if any(inputs) else 0
    elif op == 'not':
        return 0 if inputs[0] == 1 else 1
    elif op == 'xor':
        return sum(inputs) % 2
    # the out put of primary output nodes
    elif op.startswith('out'):
        return inputs[0]
    return 0

class Subgraph:
    #define the type
    sub_id: str                                   
    members: List[NodeID]                          
    inputs: List[NodeID]                           
    outputs: List[NodeID]                          
    
    # truth_table：{(in1_val, in2_val, ...): (out1_val, out2_val, ...)}
    truth_table: Dict[Tuple[int, ...], Tuple[int, ...]]
    
    # eg:matrix[0] = [1, -1, 0] 
    matrix: List[List[int]]
    
    # eg: {'input_node_1': 'S', 'input_node_2': 'NM'}
    input_tags: Dict[str, str]
    
    # eg:{'input_node_1': 5, 'input_node_2': 3}
    input_weights: Dict[str, int]

    def __init__(self,
                 sub_id:str,
                 members:List[NodeID],
                 inputs:List[NodeID],
                 outputs:List[NodeID]):
        self.sub_id = sub_id
        self.members = members    # Nodes within the subgraph
        self.inputs = inputs      
        self.outputs = outputs    
        self.truth_table = {}     # Truth table
        self.matrix = [[] for _ in range(len(inputs))]   # Ms Propagation Matrix Ms
        self.input_tags = {}      # {in_node: 'S'/'NS'/'NM'}
        self.input_weights = {}   # {in_node: weight_value}

    def build_truth_table(self,
                          graph:nx.DiGraph[NodeID]
                          )-> None:
        # add output node
        nodes_to_simulate = frozenset(self.members) | frozenset(self.outputs)

        sub_g = graph.subgraph(nodes_to_simulate)

        sorted_nodes = list(nx.topological_sort(sub_g))

        # 2. 遍历：利用 itertools.product 产生所有 0/1 序列 
        #2. Traversal: Use itertools.product to generate all 0/1 sequences.
        
        # repeat=len(self.inputs) 会自动根据输入个数生成 000, 001...
        #`repeat=len(self.inputs)` will automatically generate 000, 001, ... based on the number of inputs.
        for combo in itertools.product([0, 1], repeat=len(self.inputs)):

            # zip input id and its number
            values = dict(zip(self.inputs, combo))

            for node in sorted_nodes:
         
                 preds = list(graph.predecessors(node))
                 gate_in_values = [values[p] for p in preds if p in values]

                 op = graph.nodes[node].get("label")
                 
                 values[node] = apply_logic(op, gate_in_values)

            res_out = tuple(values.get(out, 0) for out in self.outputs)
            self.truth_table[combo] = res_out
    
    # MARCO-REVIEW (2026-04-24 16:50)
    # - some comments to be discussed (see below)
    def calculate_weight_and_local_tag(self,
                                       in_idx:int,
                                       out_tags:Dict[OutNodeID, NodeTag],out_weights:Dict[OutNodeID, NodeWeight],already_nm:bool=False
                                       )->Tuple[NodeWeight,NodeTag]:
        
        in_node = self.inputs[in_idx]
        max_weight = 0
    
        # 优化：只有在尚未确诊为 NM 时，才需要建立追踪器
        # A tracker is only needed when NM has not yet been diagnosed.It is created to calculate the NM,S,NS
        diff_tracker = None
        if not already_nm:
            diff_tracker = {out: set() for out in self.outputs}
        
        # use truth table to calculate the result after input(1->0)
        for combo_1, out_vals_1 in self.truth_table.items():
            # if the input node is 0,continue
            if combo_1[in_idx] != 1:
                continue


            # if the input node is 1,we change it to 0,
            combo_0_list = list(combo_1)
            combo_0_list[in_idx] = 0
            combo_0 = tuple(combo_0_list)
            
            out_vals_0 = self.truth_table[combo_0]
            
            base_sum = 0
            ns_pos_group = 0 #store the ns output nodes weight which increase
            ns_neg_group = 0 #store the ns output nodes weight which decrease
    
            for j, out_node in enumerate(self.outputs):
                diff = out_vals_1[j] - out_vals_0[j]


                # if we know the input node is nm, Skip state tracking and calculate weight directly
                if not already_nm:
                    diff_tracker[out_node].add(diff)
                
                if diff == 0:
                    continue 
                    
                tag = out_tags[out_node]
                w = out_weights[out_node]
                
                # --- Weight Calculation ---
                if tag == 'S':
                    base_sum += w * diff
                elif tag == 'NM':
                    # MARCO-COMMENT: I am not sure about this, but maybe I am remembering a bit wrong.
                    #                We can discuss about this next meeting.
                    base_sum += w * abs(diff)
                elif tag == 'NS':
                    partial_product = w * diff
                    if partial_product > 0:
                        ns_pos_group += partial_product
                    else:
                        ns_neg_group += partial_product
                        
            impact_pos = abs(base_sum + ns_pos_group)
            impact_neg = abs(base_sum + ns_neg_group)
            combo_max_impact = max(impact_pos, impact_neg)
            
            if combo_max_impact >= max_weight:
                max_weight = combo_max_impact
                self.matrix[in_idx]= [out_vals_1[j] - out_vals_0[j] for j in range(len(self.outputs))] #store the ms_matrix
                

        # --- get the Local Tag ---
        if already_nm:
            local_tag = 'NM' 
        else:  
            local_tag = 'S' 
            for out_node, diffs in diff_tracker.items():
                if 1 in diffs and -1 in diffs:
                    local_tag = 'NM'
                    break 
                elif (0 in diffs and 1 in diffs) or (0 in diffs and -1 in diffs):
                    if local_tag == 'S': 
                        local_tag = 'NS'

        self.input_tags[in_node] = local_tag
        # MARCO-COMMENT: From the code above, max_weight is always positive, is this correct?
        self.input_weights[in_node] = max_weight
            
        return max_weight, local_tag




# MARCO-REVIEW (2026-04-24 17:45)
# - ALL GOOD
# - I answered some of the questions left in comments (see below at MARCO-ANSWER)
# - I did not check step 4 (it is marked as todo:working)
def compute(graph: nx.DiGraph
            ) -> tuple[Mapping[NodeID, int],nx.DiGraph[SubID]]:

    # TODO: Xiaozihan
    # Implement the "partition and propagate" algorithm

    # --- 1. Initialization ---
    TI_LIMIT = 10

    # --- 2.Node Labeling ---
    
    #2.1label_nodes
    # ID Assignment: If two nodes n' and n'' are "children" of the same node, assign them to the same subgraph ID.

    # nodes_by_subid structure:
    # {
    #     sub_id: [node_id_1, node_id_2, ...], 
    #     ----------------------------------------------
    #     # Key  : The representative ID (Union-Find root or unique identifier)
    #     # Value: A list of all nodes belonging to this subgraph
    # }

    nodes_by_subid = label_nodes(graph)

    #2.2 merge circle
    

    nodes_by_subid = merge_cycles(graph, nodes_by_subid)

    inputs_map, _ = get_all_subgraph_boundaries(graph, nodes_by_subid)
    
    #2.3keep |I_s+t|<=Max(|I_s|,|I_t|)
    nodes_by_subid = greedy_merge(graph, nodes_by_subid,inputs_map)

    #gerdy merge change the nodes by subid,so update inputs_map
    inputs_map, _ = get_all_subgraph_boundaries(graph, nodes_by_subid)
    #2.4 keep |I_s|<= TI_LIMIT 
    nodes_by_subid = apply_constraints(graph, nodes_by_subid, TI_LIMIT,inputs_map)


    # record the final input and output of every graph
    inputs_of_subgraph,outputs_of_subgraph = get_all_subgraph_boundaries(graph, nodes_by_subid)
            


    # step 2: Derivation of the propagation matrix (section 3.3)
    all_subgraph_objects = {} # 用来存储实例化后的对象，所有计算结果，方便后面计算 #store all subgraph objects(created by subgraph class)


    #only calculate the nodes except primary input and primary output
    for sub_id, nodes_in_group in nodes_by_subid.items():
    #  Find all nodes of sub_id and input/output node of the graph
         sub_inputs = sorted(list(inputs_of_subgraph[sub_id]))
         sub_outputs = sorted(list(outputs_of_subgraph[sub_id]))
         
        #  print(f"the input of {sub_id} is {sub_inputs}.")
        #  print(f"the output of {sub_id} is {sub_outputs}.")

         #if the subgraph only has primary nodes/only has primary output nodes
         #Question？有可能存在一个subgraph只存在input和output吗？  
        #  if not sub_inputs or not sub_outputs:
        #     continue
        
        # 2. 实例化你的 Subgraph 类
        # TODO:有没有办法可以优化那些只有一个节点的值？有必要吗
        # create subgraph objects
         sg = Subgraph(sub_id, nodes_in_group, sub_inputs, sub_outputs)

         sg.build_truth_table(graph)

         all_subgraph_objects[sub_id] = sg

    # step 3: Propagation

    #3.1 create sorted subgraph id list
    # create a graph only with the sub_id node and all the outside edges of this subgraph
    # 这个不存在primary input 和 outputnode
    sub_id_graph = build_sub_id_graph(graph, nodes_by_subid)
    
    
    # get the sorted subgraph list, use it to calculate the weight of each subgraph
    # include primary input/inside node/primary output
    sorted_sub_id_list=list(reversed(list(nx.topological_sort(sub_id_graph))))

    # 3.2Initialize the weight of each node and the label of the primary output.
    # add weight 0 to each node
    nx.set_node_attributes(graph, 0, 'weight')

    # give the wright and monotonicity to the primary output nodes
    for node in graph.nodes:
        label = graph.nodes[node].get("label", "")
        
        if label.startswith("out"):
            # assume all the primary output nodes is outXXX
            bit_index = int(label.replace("out", ""))

            #out0=1, out1=2, out2=4, out3=8...
            graph.nodes[node]['weight'] = 1 << bit_index

            # set the monitonicity
            graph.nodes[node]['monotonicity'] = 'S'

            # we didn't add primary output node to sub_id_graph, we need to pass it to the previous node first.
            # Question? can two nodes point to a output node?
            # MARCO-ANSWER: No, a primary output (out###) has exactly one edge going into it.
            #               A node that has an outgoing edge to a primary output has no other outgoing edges.
            preds = list(graph.predecessors(node))

            for p in preds:
                graph.nodes[p]['weight'] = 1 << bit_index
                graph.nodes[p]['monotonicity'] = 'S'
    
    #3.3 start Propagation the label and monotonicity 
    for sub_id in sorted_sub_id_list:

        # if the sub_id is primary input or output
        if sub_id not in all_subgraph_objects:
            continue

        sg = all_subgraph_objects[sub_id]#use sub_id to get subgraph object

        
        
        # get all the tags and weights of output
        out_tags = {out: graph.nodes[out].get('monotonicity') for out in sg.outputs}
        out_weights = {out: graph.nodes[out].get('weight') for out in sg.outputs}

        has_global_nm = 'NM' in out_tags.values() #if output node has "NM"

        for in_idx, in_node in enumerate(sg.inputs):
        
             # 1. Check for special case 1: Fan-out(if the node point to different group)
             is_fanout = graph.nodes[in_node].get('weight') > 0
        
             # 2. if the output node has nm or is_fanout
             already_nm = is_fanout or has_global_nm
        
             # 3. calculate weight and tag（if already_nm == True，we will not calculate nm in the truth table）
             calculated_weight, local_tag = sg.calculate_weight_and_local_tag(
             in_idx, out_tags, out_weights, already_nm
        )
        
             # 4. calculate input Weight node
             graph.nodes[in_node]['weight'] += calculated_weight
        
             # 5. Label input node
             graph.nodes[in_node]['monotonicity'] = local_tag

        


    # step 4: Subgraph simulation for internal nodes
    # --- Step 4: 内部节点权重仿真 ---
    for sid, sg in all_subgraph_objects.items():

        local_nodes = set(sg.members) | set(sg.inputs)
        sub_g = graph.subgraph(local_nodes)
        sorted_local = list(nx.topological_sort(sub_g))

        
        for combo in itertools.product([0, 1], repeat=len(sg.inputs)):  
            # remember the normal output if do not change the value of node
            normal_vals = dict(zip(sg.inputs, combo))
            
            # calculate the value of each node 
            for n in sorted_local:
                if n in sg.inputs: continue
                preds = list(sub_g.predecessors(n))
                in_vals = [normal_vals[p] for p in preds]
                
                op = graph.nodes[n].get('label')
                normal_vals[n] = apply_logic(op, in_vals)

            internal_nodes = [n for n in sg.members]
            for target_node in internal_nodes:
                # --- 步骤 2: 制造翻转 ---
                # --- Step 2: Create a flip ---
                # the value of node will change after the target_node
                flipped_vals = normal_vals.copy()
                flipped_vals[target_node] = 1 - normal_vals[target_node]

                start_idx = sorted_local.index(target_node)
                # --- 步骤 3: 更新 target_node 之后的节点 ---
                # --- Step 3: Update nodes after target_node ---
                for i in range(start_idx + 1, len(sorted_local)):

                    n = sorted_local[i]
                    # 重新计算该节点：它会读取到已经被“污染”的前驱新值
                    # Recalculate the node: It will read the new value of the predecessor that has been flipped.
                    preds = list(sub_g.predecessors(n))
                    new_in_vals = [flipped_vals[p] for p in preds]
                    op = graph.nodes[n].get('label')
                    flipped_vals[n] = apply_logic(op, new_in_vals)
                
                # --- 步骤 4: 计算本次翻转的影响 ---
                # --- Step 4: Calculate the impact of this flip ---
                current_impact = 0
                for j, out_node in enumerate(sg.outputs):
                    if flipped_vals[out_node] != normal_vals[out_node]:
                        out_node_weight = graph.nodes[out_node].get('weight')
                        current_impact += out_node_weight

                old_max = graph.nodes[target_node].get('weight')
                if current_impact > old_max:
                    graph.nodes[target_node]['weight'] = current_impact
                    

    weights = nx.get_node_attributes(graph, 'weight')

    return weights, sub_id_graph
