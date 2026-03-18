from __future__ import annotations
from typing import Mapping
from collections import defaultdict


import networkx as nx
import itertools

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

# TODO:do you need any other gate?
# input:op is string; bits is list of 0/1 [0,1]
def apply_logic(op, inputs):
    if op == 'and':
        return 1 if all(inputs) else 0
    elif op == 'or':
        return 1 if any(inputs) else 0
    elif op == 'not':
        return 0 if inputs[0] == 1 else 1
    elif op == 'xor':
        return sum(inputs) % 2
    return 0

class Subgraph:
    def __init__(self, sub_id, members, inputs, outputs):
        self.sub_id = sub_id
        self.members = members    # 子图内的节点 # Nodes within the subgraph
        self.inputs = inputs      
        self.outputs = outputs    
        self.truth_table = {}     # 真值表 Truth table
        self.matrix = []          # 传播矩阵 Ms Propagation Matrix Ms

    def build_truth_table(self, graph):
        # add output node
        nodes_to_simulate = set(self.members) | set(self.outputs)
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
                 gate_in_values = [[values[p] for p in preds if p in values]]

                 op = graph.nodes[node].get("label")
                 values[node] = apply_logic(op, gate_in_values)

            res_out = tuple(values.get(out, 0) for out in self.outputs)
            self.truth_table[combo] = res_out


    # Analyze monotonicity and generate matrix Ms
    def derive_ms(self): #derive_propagation_matrix

        #  创造空的M矩阵 
        #  Create an empty Ms matrix
        num_in = len(self.inputs)
        num_out = len(self.outputs)

        self.matrix = [[0] * num_out for i in range(num_in)] 

        # store the different between different output
        diff_sets = [[set() for _ in range(num_out)] for _ in range(num_in)]
        # 如果真的要根据情况来存的话，这里需要存所有的情况，因为后需要比较
        for combo, out_v1 in self.truth_table.items():
             for i in range(num_in):
                 if combo[i] == 0:
                     twin_list = list(combo)
                     twin_list[i] = 1
                     twin_combo = tuple(twin_list)
                     out_v2 = self.truth_table[twin_combo]

                     for j in range(num_out):
                         diff = out_v2[j] - out_v1[j]

                         if diff != 0:
                             diff_sets[i][j].add(diff)

        # TODO: the logic has problem
        for i in range(num_in):
             for j in range(num_out):
                 s = diff_sets[i][j]
                 #  Fill in with monotonicity
                 if 1 in s: self.matrix[i][j] = 1
                 elif -1 in s:           self.matrix[i][j] = 1


# def simulate_local(graph, sg, input_combo):
#     """算出子图内所有节点在特定输入下的值"""
#     values = dict(zip(sg.inputs, input_combo))
#     # 按照子图内部的拓扑序计算
#     sub_g = graph.subgraph(sg.members)
#     for n in nx.topological_sort(sub_g):
#         if n in sg.inputs: continue
#         preds = list(graph.predecessors(n))
#         in_vals = [values[p] for p in preds if p in values]
#         op = graph.nodes[n].get('label')
#         values[n] = apply_logic(op, in_vals)
#     return values

# def resimulate_downstream(graph, sg, start_node, values):
#     """从起始节点开始，仅在子图内部重新计算受影响的节点"""
#     sub_g = graph.subgraph(sg.members)
#     # 只需处理在拓扑序中排在 start_node 之后的节点
#     sorted_nodes = list(nx.topological_sort(sub_g))
#     start_idx = sorted_nodes.index(start_node)
    
#     for i in range(start_idx + 1, len(sorted_nodes)):
#         n = sorted_nodes[i]
#         preds = list(graph.predecessors(n))
#         in_vals = [values[p] for p in preds if p in values]
#         op = graph.nodes[n].get('label')
#         values[n] = apply_logic(op, in_vals)
#     return values

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

    # ERROR：Primary Outputs(if those outputs has no input????)
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

    # step 3: Propagation

    # create sorted subgraph id list
    # create a graph only with the sub_id node and all the input and output edge
    sub_id_graph = nx.DiGraph()

    for sub_id, sg in all_subgraph_objects.items():
        sub_id_graph.add_node(sub_id)

        for in_node in sg.inputs:

            preds = list(graph.predecessors(in_node))

            for p in preds:
                # get the parent subgraph id
                parent_sub_id=graph.nodes[p].get('subgraph_id')

                if parent_sub_id and parent_sub_id != sub_id:
                    sub_id_graph.add_edge(parent_sub_id,sub_id)
    
    # get the sorted subgraph list, use it to calculate the weight of each subgraph
    sorted_sub_id_list=list(reversed(list(nx.topological_sort(sub_id_graph))))


    nx.set_node_attributes(graph, 0, 'weight')

    for node in graph.nodes:
        label = graph.nodes[node].get("label", "")
        
        if label.startswith("out"):
            # assume all the primary output nodes is outXXX
            bit_index = int(label.replace("out", ""))

            #out0=1, out1=2, out2=4, out3=8...
            graph.nodes[node]['weight'] = 1 << bit_index

    
    for sub_id in sorted_sub_id_list:

        if sub_id not in all_subgraph_objects:
            continue

        sg = all_subgraph_objects[sub_id]

        # 1.  get W_out
        w_out = [graph.nodes[out_node]['weight'] for out_node in sg.outputs]

        # 2. calculate (W_in)
        # W_in[i] = sum( |M[i][j]| * W_out[j] )
        for i, in_node in enumerate(sg.inputs):
             
             current_in_weight = 0

             for j in range(len(sg.outputs)):
                current_in_weight += sg.matrix[i][j] * w_out[j]
            
             graph.nodes[in_node]['weight'] += current_in_weight


    # step 4: Subgraph simulation for internal nodes

    # # --- Step 4: 内部节点权重仿真 ---
    # for sid, sg in all_subgraph_objects.items():
    #     local_nodes = set(sg.members) | set(sg.inputs) | set(sg.outputs)
    #     sub_g = graph.subgraph(local_nodes)
    #     sorted_local = list(nx.topological_sort(sub_g))
    #     w_out_vals = [graph.nodes[on]['weight'] for on in sg.outputs]
        
    #     internal_nodes = [n for n in sg.members]
        
    #     for node in internal_nodes:
    #         max_impact = 0
    #         for combo in itertools.product([0, 1], repeat=len(sg.inputs)):
    #             # 局部仿真
    #             vals = {n: 0 for n in local_nodes}
    #             vals.update(dict(zip(sg.inputs, combo)))
    #             for n in sorted_local:
    #                 if n in sg.inputs: continue
    #                 ps = [p for p in graph.predecessors(n) if p in vals]
    #                 if ps:
    #                     vals[n] = apply_logic(graph.nodes[n].get('label'), [vals[p] for p in ps])
                
    #             # 翻转仿真
    #             flipped_vals = vals.copy()
    #             flipped_vals[node] = 1 - vals[node]
    #             # 重新计算 downstream
    #             start_idx = sorted_local.index(node)
    #             for i in range(start_idx + 1, len(sorted_local)):
    #                 n = sorted_local[i]
    #                 ps = [p for p in graph.predecessors(n) if p in flipped_vals]
    #                 if ps:
    #                     flipped_vals[n] = apply_logic(graph.nodes[n].get('label'), [flipped_vals[p] for p in ps])
                
    #             # 影响累加
    #             impact = sum(w_out_vals[j] for j, on in enumerate(sg.outputs) if vals[on] != flipped_vals[on])
    #             max_impact = max(max_impact, impact)
            
    #         graph.nodes[node]['weight'] = max_impact

    return nx.get_node_attributes(graph, 'weight')

    return nx.get_node_attributes(graph, 'weight')

    # step 4: Subgraph simulation for internal nodes
    ...

    # return the mapping from names to weights
    # partition_results = {
    #     'node_to_subid': nx.get_node_attributes(graph, 'subgraph_id'),
    #     'sub_inputs': inputs_of_subgraph,
    #     'sub_outputs': outputs_of_subgraph
    # }
    # return partition_results

