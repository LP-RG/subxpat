from __future__ import annotations
from typing import Mapping
from collections import defaultdict


import networkx as nx
import itertools
from itertools import islice

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
    # the out put of primary output nodes
    elif op.startswith('out'):
        return inputs[0]
    return 0

class Subgraph:
    def __init__(self, sub_id, members, inputs, outputs):
        self.sub_id = sub_id
        self.members = members    # Nodes within the subgraph
        self.inputs = inputs      
        self.outputs = outputs    
        self.truth_table = {}     # Truth table
        self.matrix = [[] for _ in range(len(inputs))]   # Ms Propagation Matrix Ms
        self.input_tags = {}      # {in_node: 'S'/'NS'/'NM'}
        self.input_weights = {}   # {in_node: weight_value}

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
                 gate_in_values = [values[p] for p in preds if p in values]

                 op = graph.nodes[node].get("label")
                 
                 values[node] = apply_logic(op, gate_in_values)

            res_out = tuple(values.get(out, 0) for out in self.outputs)
            self.truth_table[combo] = res_out
    
    def calculate_weight_and_local_tag(self, in_idx, out_tags, out_weights, already_nm=False):
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
        self.input_weights[in_node] = max_weight
            
        return max_weight, local_tag

    # # TODO:这个函数可能需要删除或者改变
    # # Analyze monotonicity and generate matrix Ms
    # def derive_ms(self): #derive_propagation_matrix

    #     #  创造空的M矩阵 
    #     #  Create an empty Ms matrix
    #     num_in = len(self.inputs)
    #     num_out = len(self.outputs)

    #     self.matrix = [[0] * num_out for i in range(num_in)] 

    #     # store the different between different output
    #     diff_sets = [[set() for _ in range(num_out)] for _ in range(num_in)]
    #     # 如果真的要根据情况来存的话，这里需要存所有的情况，因为后需要比较
    #     for combo, out_v1 in self.truth_table.items():
    #          for i in range(num_in):
    #              if combo[i] == 0:
    #                  twin_list = list(combo)
    #                  twin_list[i] = 1
    #                  twin_combo = tuple(twin_list)
    #                  out_v2 = self.truth_table[twin_combo]

    #                  for j in range(num_out):
    #                      diff = out_v2[j] - out_v1[j]

    #                      if diff != 0:
    #                          diff_sets[i][j].add(diff)

    #     # TODO: the logic has problem
    #     for i in range(num_in):
    #          for j in range(num_out):
    #              s = diff_sets[i][j]
    #              #  Fill in with monotonicity
    #              if 1 in s: self.matrix[i][j] = 1
    #              elif -1 in s:           self.matrix[i][j] = 1



def compute(graph: nx.digraph.DiGraph) -> Mapping[str, int]:

    # TODO: Xiaozihan
    # Implement the "partition and propagate" algorithm


    # --- 1. 初始化 ---
    # --- 1. Initialization ---
    uf = UnionFind(graph.nodes)
    TI_LIMIT = 10
    nodes_by_subid = defaultdict(list) #用于记录最终的subid:[这个subgraph所有node]

    # --- 2.Node Labeling ---

    # ID Assignment: If two nodes n' and n'' are "children" of the same node, assign them to the same subgraph ID.
    for node in graph.nodes:

        #for node doesn't has out edge or only has one
        if graph.out_degree(node) <= 1: 
            continue
        
        # # Get child nodes, but filter out PO nodes whose tags start with "out".

        children = [child for child in graph.successors(node) 
                if not graph.nodes[child].get("label", "").startswith("out")]
        
        if len(children) > 1:
            first_child = children[0]
            for other_child in islice(children, 1, None):
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

        label = graph.nodes[node].get("label", "")
    
        # TODO：fix the problem
        # Special handling for the main output node: It's in its own group
        if label.startswith("out") or label.startswith("in"):
            graph.nodes[node]['subgraph_id'] = node  # 自己一个ID
            continue  # 不加入 nodes_by_subid

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
        subId_u = graph.nodes[u]['subgraph_id']
        subId_v = graph.nodes[v]['subgraph_id']
         
        #  所以就是primary out put只有inputs；而primary input 只有outputs
        if subId_u != subId_v:
            inputs_of_subgraph[subId_v].add(u)
            outputs_of_subgraph[subId_u].add(v)


    # step 2: Derivation of the propagation matrix (section 3.3)
    all_subgraph_objects = {} # 用来存储实例化后的对象，所有计算结果，方便后面计算 #store all subgraph objects(created by subgraph class)


    #only calculate the nodes except primary input and primary output
    for sub_id, nodes_in_group in nodes_by_subid.items():
    #  Find all nodes of sub_id and input/output node of the graph
         sub_inputs = sorted(list(inputs_of_subgraph[sub_id]))
         sub_outputs = sorted(list(outputs_of_subgraph[sub_id]))
         
        #  print(f"the input of {sub_id} is {sub_inputs}./n")
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
    sub_id_graph = nx.DiGraph()

    for sub_id, sg in all_subgraph_objects.items():

        sub_id_graph.add_node(sub_id)

        for in_node in sg.inputs:

            parent_sub_id = graph.nodes[in_node].get('subgraph_id')

            if parent_sub_id is not None and parent_sub_id != sub_id:
                    # if the input is primary input, the nodes are not in all_subgraph_objects
                    if parent_sub_id not in sub_id_graph:
                        sub_id_graph.add_node(parent_sub_id)
                        
                    sub_id_graph.add_edge(parent_sub_id,sub_id)
       
        for out_node in sg.outputs:
        
            for successor in graph.successors(out_node):
                child_sub_id = graph.nodes[successor].get('subgraph_id')
            
                if child_sub_id is not None and child_sub_id != sub_id:
                    # if the output is primary output, the nodes are not in all_subgraph_objects
                    if child_sub_id not in sub_id_graph:
                        sub_id_graph.add_node(child_sub_id)
                    sub_id_graph.add_edge(sub_id, child_sub_id)
    
    
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

    
    #3.3 start Propagation the label and monotonicity 
    for sub_id in sorted_sub_id_list:

        # print(f"\n--- 正在传播子图: {sub_id} ---")
        # for out_node in sg.outputs:
        #     print(f"  检查输出口 {out_node} 的当前权重: {graph.nodes[out_node]['weight']}")

        # if the sub_id is primary input or output
        if sub_id not in all_subgraph_objects:
            continue

        sg = all_subgraph_objects[sub_id]#use sub_id to get subgraph object
        
        # get all the tags and weights of output
        out_tags = {out: graph.nodes[out].get('monotonicity', 'S') for out in sg.outputs}
        out_weights = {out: graph.nodes[out].get('weight', 0) for out in sg.outputs}

        has_global_nm = 'NM' in out_tags.values() #if output node has "NM"

        for in_idx, in_node in enumerate(sg.inputs):
        
             # 1. Check for special case 1: Fan-out(if the node point to different group)
             is_fanout = graph.nodes[in_node].get('weight', 0) > 0
        
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

        # print("\n==== 实时子图矩阵监测 ====")
        # for sid, sg in all_subgraph_objects.items():
        #     print(f"子图 {sid} 的 Ms 矩阵: {sg.matrix}")
        


    # TODO:working
    # step 4: Subgraph simulation for internal nodes
    # --- Step 4: 内部节点权重仿真 ---
    for sid, sg in all_subgraph_objects.items():

        local_nodes = set(sg.members) | set(sg.inputs) | set(sg.outputs)
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

    return weights, sub_id_graph, all_subgraph_objects


# from test_circuit_simple import (
#     create_test_1_single_not_gate,
#     create_test_2_and_gate,
#     create_test_3_xor_gate,
#     create_test_4_fanout,
#     create_test_5_series,
#     create_test_6_complex
# )

# # 创建所有测试
# test_cases = [
#     ("TEST 1: 单个NOT门", create_test_1_single_not_gate()),
#     ("TEST 2: AND门", create_test_2_and_gate()),
#     ("TEST 3: XOR门（非单调）", create_test_3_xor_gate()),
#     ("TEST 4: 扇出电路", create_test_4_fanout()),
#     ("TEST 5: 串联电路", create_test_5_series()),
#     ("TEST 6: 较复杂电路", create_test_6_complex()),
# ]


# for name, G in test_cases:
#     weights = compute(G)
#     print(f"{name}: {weights}")

# def run_advanced_tests():
#     # --- TEST 1: NOT Gate (验证负单调性 -1) ---
#     print("\n" + "="*40)
#     print("TEST 1: NOT Gate (Negative Monotonicity)")
#     G1 = nx.DiGraph()
#     G1.add_node('in0', label='input')
#     G1.add_node('gate1', label='not')
#     G1.add_node('out0', label='out0')
#     G1.add_edges_from([('in0', 'gate1'), ('gate1', 'out0')])
    
#     w1, _, objs1 = compute(G1)
#     print(f"Ms Matrix: {objs1['gate1_root'].matrix if 'gate1_root' in objs1 else 'Check ID'}")
#     print(f"Weights: {w1}")

#     # --- TEST 2: XOR Gate (验证非单调性 NM) ---
#     print("\n" + "="*40)
#     print("TEST 2: XOR Gate (Non-monotonicity)")
#     G2 = nx.DiGraph()
#     G2.add_node('in0', label='input')
#     G2.add_node('in1', label='input')
#     G2.add_node('gate1', label='xor')
#     G2.add_node('out0', label='out0')
#     G2.add_edges_from([('in0', 'gate1'), ('in1', 'gate1'), ('gate1', 'out0')])
    
#     w2, _, objs2 = compute(G2)
#     # 这里的 Ms 应该是 [1] 或 [-1]，但 monotonicity 属性应为 'NM'
#     print(f"Weights: {w2}")
#     print(f"in0 Monotonicity: {G2.nodes['in0'].get('monotonicity')}")

#     # --- TEST 3: Reconvergent Fan-out (验证 Equation 14 的分支叠加) ---
#     # in0 分成两路，一路经过 NOT，两路最后汇总到 AND
#     # 这种结构非常考验权重累加逻辑
#     print("\n" + "="*40)
#     print("TEST 3: Fan-out Reconvergent Path")
#     G3 = nx.DiGraph()
#     G3.add_node('in0', label='input')
#     G3.add_node('branch_a', label='and') # 用 AND 当 buffer
#     G3.add_node('branch_b', label='not') # 负向路径
#     G3.add_node('final_gate', label='and')
#     G3.add_node('out0', label='out0')
    
#     G3.add_edges_from([
#         ('in0', 'branch_a'), ('in0', 'branch_b'),
#         ('branch_a', 'final_gate'), ('branch_b', 'final_gate'),
#         ('final_gate', 'out0')
#     ])
    
#     w3, _, _ = compute(G3)
#     print(f"Weights: {w3}")

# # 执行测试
# run_advanced_tests()