from __future__ import annotations
from typing import Mapping
from collections import defaultdict

import networkx as nx

# Union find
# get root and use path compression optimization
def get_root(i, p_map):
    root = i
    while p_map[root] != root:
        root = p_map[root]
    while p_map[i] != root:
        new_p = p_map[i]
        p_map[i] = root
        i = new_p
    return root

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
    parent = {node: node for node in graph.nodes}
    TI_LIMIT = 10
    
    # 核心：维护一个用于“无环检测”的缩略图
    condensed_G = nx.DiGraph(graph.edges())

# Union find method
    # 2. Safe Union
    def safe_union(u, v):
        root_u = get_root(u, parent)
        root_v = get_root(v, parent)
        
        if root_u == root_v:
            return True
        
        # --- 确保合并不会产生环---
        # 如果 root_u 能走到 root_v，合并它们会让原本的“上下游”变成“组内循环”
        if nx.has_path(condensed_G, root_u, root_v) or nx.has_path(condensed_G, root_v, root_u):
            return False # 拒绝合并，保护拓扑结构
        
        # 合并
        parent[root_u] = root_v
        

        # 使用 contracted_nodes 让 root_v 继承 root_u 的所有外交关系（边）
        # 这样下一次 nx.has_path 就能检测到这一整组人的依赖关系
        nx.contracted_nodes(condensed_G, root_v, root_u, self_loops=False, copy=False)
        return True


    #Node Labeling: Traverse every node in the graph.
    # ID Assignment: If two nodes n' and n'' are "children" of the same node, assign them to the same subgraph ID.

    # Merging and Removing Cycles: Iteratively merge subsets with the same ID, ensuring the partitioned graph is acyclic.
    for node in graph.nodes:

        if graph.out_degree(node) == 0: # Total output regardless
            continue
            
        children = list(graph.successors(node))
        if len(children) > 1:
            first_child = children[0]
            for other_child in children[1:]:
                safe_union(first_child, other_child)

    # Phase 2: Forced splitting of "infeasible" subgraphs

    #Check the input count: Count the external input edges corresponding to each subgraph ID.        
    # find the input of each group
    subgraph_inputs = defaultdict(set)#Record all input groups
    for u, v in graph.edges:
         root_u = get_root(u, parent)
         root_v = get_root(v,parent)
         if root_u != root_v:
             subgraph_inputs[root_v].add(u)

     # Brute-force decomposition: If the input count |I_s| > T_I of a subgraph, directly de compose all nodes in this subgraph, returning it to a state of "one node per subgraph". (This can be improved.)
    # TODO:思考其他策略
    # 这里是不是会重复？
    for node in graph.nodes:
        root = get_root(node, parent)
        
        if len(subgraph_inputs[root]) > TI_LIMIT:
             parent[node] = node
             graph.nodes[node]['subgraph_id'] = node
        else:
             graph.nodes[node]['subgraph_id'] = root

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
    # Get all subgraph_id
    all_subgraph_ids = set(nx.get_node_attributes(graph, 'subgraph_id').value())

    # For every subgrapg,we need to calculate the matrix?how to store the matrix
    for sub_id in all_subgraph_ids:
    # 1. 找出所有属于这个 sub_id 的节点
    #  Find all nodes of sub_id and input/output node of the graph
         nodes_in_sub = [n for n in graph.nodes if graph.nodes[n]['subgraph_id'] == sub_id]
         sub_inputs = sorted(list(inputs_of_subgraph[sub_id]))
         sub_outputs = sorted(list(outputs_of_subgraph[sub_id]))

    # TODO:Is there any method we can use to find the output from the input?


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
