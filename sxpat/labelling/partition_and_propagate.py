from __future__ import annotations
from typing import Mapping
from collections import defaultdict

import networkx as nx


def compute(graph: nx.digraph.DiGraph) -> Mapping[str, int]:

    # TODO: Xiaozihan
    # Implement the "partition and propagate" algorithm


    # step 1: Graph partitioning (section 3.2)
    # --- 准备工作：初始化并查集 ---
    parent = {node: node for node in graph.nodes}
    TI_LIMIT = 10

    def find(i):
        if parent[i] == i:
            return i
        # Path compression
        parent[i] = find(parent[i])
        return parent[i]

    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

        # Phase 1: Initial clustering based on "common ancestor"
    for node in graph.nodes:
        children = list(graph.successors(node))
        
        if len(children) > 1:
            first_child = children[0]
            for other_child in children[1:]:
                union(first_child, other_child)

    # find the input/output of each group
    subgraph_inputs = defaultdict(set)#Record all input groups
    subgraph_outputs = defaultdict(set)
    for u, v in graph.edges:
        root_u = find(u)
        root_v = find(v)
    if root_u != root_v:
        subgraph_inputs[root_v].add(u)
        subgraph_outputs[root_u].add(u)

    # 补充：电路的主输出节点 (Primary Outputs)
    for node in graph.nodes:
        if node.startswith('out'):
            root_out = find(node)
            subgraph_outputs[root_out].add(node)
    

    # if the input of a group is greater than 10
    for node in graph.nodes:
        root = find(node)
        if len(subgraph_inputs[root]) > TI_LIMIT:
            graph.nodes[node]['subgraph_id'] = node 
        else:
            graph.nodes[node]['subgraph_id'] = root 

    # 注意：这里我们还没处理 T_I < 10 的限制，那是 Step 1 的增强版
    # 我们先确保这一步能跑通
           #Node Labeling: Traverse every node in the graph.

           # ID Assignment: If two nodes n' and n'' are "children" of the same node, assign them to the same subgraph ID.

           # Merging and Removing Cycles: Iteratively merge subsets with the same ID, ensuring the partitioned graph is acyclic.


        # Phase 2: Forced splitting of "infeasible" subgraphs

            #Check the input count: Count the external input edges corresponding to each subgraph ID.

            # Brute-force decomposition: If the input count |I_s| > T_I of a subgraph, directly de compose all nodes in this subgraph, returning it to a state of "one node per subgraph". (This can be improved.)

    # step 2: Derivation of the propagation matrix (section 3.3)
    ...

    # step 3: Propagation
    ...

    # step 4: Subgraph simulation for internal nodes
    ...

    # return the mapping from names to weights
    return {}



if __name__ == "__main__":
    # 1. 创建一个空图
    test_graph = nx.DiGraph()
    
    # 2. 手动添加边 (父亲 -> 孩子)
    # P 有两个孩子 A 和 B，它们是亲兄弟
    test_graph.add_edge("P", "A")
    test_graph.add_edge("P", "B")
    
    # 添加一个无关的边
    test_graph.add_edge("X", "C")
    test_graph.add_edge("X", "B")
    
    print("开始运行微型测试...")
    # 3. 调用你刚写好的 compute 函数
    # 注意：为了测试，你可能需要让 compute 返回 partition 字典而不是空字典
    results = compute(test_graph)
    
    # 我们在这里手动打印一下并查集的结果
    # 假设你在 compute 里定义了 partition 变量
    # (为了测试，你可以临时让 compute return partition)