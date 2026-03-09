from __future__ import annotations
from typing import Mapping
from collections import defaultdict

import networkx as nx

# Union find class
class UnionFind:
    def __init__(self, nodes):
        self.parent = {node: node for node in nodes}

    # get root and use path compression optimization
    def find(self, i):
        root=i
        while self.parent[root]!=root:
            root = self.parent[root]
        while self.parent[i] != root:
            new_p = self.parent[i]
            self.parent[i] = root
            i = new_p
        return root

    # if u and v belongs to different union,let v point to u
    def union(self, u, v):
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        self.parent[root_v] = root_u

class Subgraph:
    def __init__(self, sub_id, members, inputs, outputs):
        self.sub_id = sub_id
        self.members = members    # 子图内的节点
        self.inputs = inputs      
        self.outputs = outputs    
        self.truth_table = {}     # 核心数据：真值表
        self.matrix = []          # 核心数据：传播矩阵 Ms

    def build_truth_table(self, graph):
        """生成 2^k 真值表"""
        pass

    def derive_ms(self): #derive_propagation_matrix
        """分析单调性，生成矩阵 Ms"""
        pass

    def propagate(self, out_weights):
        """计算 Win = Ms * Wout"""
        pass


# input:op is string; bits is list of 0/1 [0,1]
def apply_logic(op, bits):
    if op == 'AND':
        return 1 if all(bits) else 0
    elif op == 'OR':
        return 1 if any(bits) else 0
    elif op == 'NOT':
        return 0 if bits[0] == 1 else 1
    elif op == 'XOR':
        return sum(bits) % 2
    return 0


def compute(graph: nx.digraph.DiGraph) -> Mapping[str, int]:

    # TODO: Xiaozihan
    # Implement the "partition and propagate" algorithm


    # --- 1. 初始化 ---
    uf = UnionFind(graph.nodes)
    TI_LIMIT = 10
    nodes_by_subid = defaultdict(list) #用于记录最终的subid:[这个subgraph所有node]

    # --- 2.Node Labeling ---

    # ID Assignment: If two nodes n' and n'' are "children" of the same node, assign them to the same subgraph ID.
    for node in graph.nodes:

        #TODO:this can be changed
        if graph.out_degree(node) == 0: # Total output regardless
            continue
            
        children = list(graph.successors(node))
        if len(children) > 1:
            first_child = children[0]
            for other_child in children[1:]:
                uf.union(first_child, other_child)
     
    # find the input of each group，use to calculate the number of input
    temp_group_inputs = defaultdict(set)
    
    for u, v in graph.edges:
         root_u = uf.find(u)
         root_v = uf.find(v)
         if root_u != root_v:
             temp_group_inputs[root_v].add(u)

     # Brute-force decomposition: If the input count |I_s| > T_I of a subgraph, directly de compose all nodes in this subgraph, returning it to a state of "one node per subgraph". (This can be improved.)
    
    
    # TODO:improve it
    for node in graph.nodes:
        root = uf.find(node)
        
        if len(temp_group_inputs[root]) > TI_LIMIT:
             uf.parent[node]=node
             sub_id = node
        else:
             sub_id = root

        graph.nodes[node]['subgraph_id'] = sub_id
        nodes_by_subid[sub_id].append(node)

    # record the final input and output of every graph
    inputs_of_subgraph = defaultdict(set)
    outputs_of_subgraph = defaultdict(set)

    for u, v in graph.edges:
        root_u = graph.nodes[u]['subgraph_id']
        root_v = graph.nodes[v]['subgraph_id']
        
        if root_u != root_v:
            inputs_of_subgraph[root_v].add(u)
            outputs_of_subgraph[root_u].add(u)

    # Primary Outputs
    for node in graph.nodes:
        if graph.out_degree(node) == 0:
            sub_id = graph.nodes[node]['subgraph_id']
            outputs_of_subgraph[sub_id].add(node)


    # step 2: Derivation of the propagation matrix (section 3.3)
    all_subgraph_objects = {} # 用来存储实例化后的对象，所有计算结果，方便后面计算

    for sub_id, nodes_in_group in nodes_by_subid.items():
    #  Find all nodes of sub_id and input/output node of the graph
         sub_inputs = sorted(list(inputs_of_subgraph[sub_id]))
         sub_outputs = sorted(list(outputs_of_subgraph[sub_id]))

         if not sub_inputs:
            continue
        
        # 2. 实例化你的 Subgraph 类
        # 我们把名单、输入、输出都喂给它
         sg = Subgraph(sub_id, nodes_in_group, sub_inputs, sub_outputs)

         sg.build_truth_table(graph)
         sg.derive_ms()

         all_subgraph_objects[sub_id] = sg
    

    # TODO:Is there any method we can use to find the output value from the input?

    # TODO:Are there any identifiers for Primary Outputs and Primary Input? 
    
    # TODO:Where can I see the graph of the input?


    # step 3: Propagation
    ...

    # step 4: Subgraph simulation for internal nodes
    ...

    # return the mapping from names to weights
    partition_results = {
        'node_to_subid': nx.get_node_attributes(graph, 'subgraph_id'),
        'sub_inputs': inputs_of_subgraph,
        'sub_outputs': outputs_of_subgraph
    }
    return partition_results
