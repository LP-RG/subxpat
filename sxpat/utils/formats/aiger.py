"""
    @authors: Ilia Zeller

    Aiger files generation, and aiger files loading and parsing to produce IOGraph.
"""

from textwrap import dedent
from sxpat.graph import IOGraph
from sxpat.graph.node import BoolVariable, BoolConstant, And, Not, Identity
import subprocess
import numpy as np
import aigverse as aig
import aigverse.adapters.networkx as aig_nx
import networkx as nx
import os

__all__ = [
            'gen_circuit_digraph',
            'iograph_from_digraph',
        ]

# generates circuit digraph
def gen_circuit_digraph(benchmark_name):
    verilog_path = f'{"./benchmarks/v"}/{benchmark_name}.{"v"}'
    os.makedirs("./aiger/aig_files", exist_ok=True)
    aiger_path = f'{"./aiger/aig_files"}/{benchmark_name}.{"aig"}'

    # synthesize to gate level
    yosys_command = dedent(f"""
        read_verilog {verilog_path};

        # flattening
        synth -flatten;
        opt -purge;       # needed if already flat
        splitnets -ports; # needed if original

        # normalize
        abc -g NAND; # some alternatives we could discuss are: "abc -g NAND,AND", "aigmap"
        opt -purge;

        #
        aigmap;
        write_aiger {aiger_path};
    """)

    process = subprocess.run(['yosys', '-p', yosys_command], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if process.stderr.decode():
        print(f'Error!')
        raise Exception(f'ERROR!!! yosys cannot do its pass on file {verilog_path}\n{process.stderr.decode()}')
    
    # generate ASCII version of aiger file (just for file ispection)
    os.makedirs("./aiger/ascii_aig_files", exist_ok=True)
    ascii_aiger_path = f'{"./aiger/ascii_aig_files"}/{benchmark_name}.{"aig"}'

    yosys_command_ascii = dedent(f"""
        read_verilog {verilog_path};

        # flattening
        synth -flatten;
        opt -purge;       # needed if already flat
        splitnets -ports; # needed if original

        # normalize
        abc -g NAND; # some alternatives we could discuss are: "abc -g NAND,AND", "aigmap"
        opt -purge;

        #
        aigmap;
        write_aiger -ascii {ascii_aiger_path};
    """)

    process = subprocess.run(['yosys', '-p', yosys_command_ascii], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    if process.stderr.decode():
        print(f'Error!')
        raise Exception(f'ERROR!!! yosys cannot do its pass on file {verilog_path}\n{process.stderr.decode()}')
    
    # generate DiGraph
    aig_obj = aig.io.read_aiger_into_aig(aiger_path)
    circuit_digraph = aig_nx.to_networkx(aig_obj)
    return circuit_digraph

def is_topological_order(G, order):
    # Create a position map: node -> index in the given order
    pos = {node: i for i, node in enumerate(order)}
    
    # Check all edges
    for u, v in G.edges():
        if pos[u] >= pos[v]:
            return False
    return True

def topological_sort(G: nx.DiGraph):
    # Sort nodes in topological order
    sorted_G = nx.DiGraph()
    sorted_G.graph = G.graph
    sorted_G.add_nodes_from(nx.topological_sort(G))
    sorted_G.add_edges_from(G.edges(data=True))
    return sorted_G

def extract_inputs_outputs(graph: nx.DiGraph):
    input_dict = {}
    output_dict = {}
    for n in graph.nodes():
        idx = int(graph.nodes[n]['index'])
        node_type = graph.nodes[n]['type']    
        if node_type[1]:  # input
            input_dict[idx] = n
        elif node_type[3]:  # output
            output_dict[idx] = n
    return input_dict, output_dict

def sort_dict(this_dict: dict) -> dict:
    sorted_dict = {}
    this_dict_ids = list(this_dict.keys())
    this_dict_ids.sort()
    for i in this_dict_ids:
        sorted_dict[i] = this_dict[i]
    return sorted_dict

def iograph_from_digraph(benchmark_name, circuit_digraph: nx.DiGraph) -> IOGraph:
    
    graph = circuit_digraph

    if (not is_topological_order(graph, graph.nodes)): 
        graph = topological_sort(graph)

    os.makedirs("./aiger/gv_files", exist_ok=True)
    with open(f'{"./aiger/gv_files"}/{benchmark_name}.{"gv"}', 'w') as f:
        # save in .gv file for graph visualization -> BEFORE NOT GATES INTEGRATION
        f.write('strict digraph GGraph {\n')
        for n in graph.nodes: f.write(f'"{n}" [label="{n}"];\n')
        for u, v in graph.edges: f.write(f'"{u}" -> "{v}";\n')
        f.write('}')

    input_nodes, output_nodes = extract_inputs_outputs(graph)
    input_dict = sort_dict(input_nodes)
    output_dict = sort_dict(output_nodes)

    num_inputs = graph.graph["num_pis"] #num_pis = number of primary inputs.
    num_outputs = graph.graph["num_pos"] #num_pos = number of primary outputs.
    num_AND_gates = graph.graph["num_gates"] #num_gates = number of AND gates.
    num_constants = 0
    
    nodes = []
    for n in graph.nodes.data():
        # "type" -> [const, pi, gate, po]
        if int(n[1]["type"][0]) == 1:
            num_constants += 1
        nodes.append(n)
    
    num_gates = num_AND_gates
    new_nodes = [] #nodes representing both AND and NOT gates
    new_edges = [] #edges (just of regular kind) 
    num_gates = not_gates_integration(graph, nodes, new_nodes, new_edges, num_gates)
    
    not_gates_amount = num_gates - num_AND_gates

    # ASSERT new nodes and edges: expected amount == actual amount
    # int(list(self.__graph.edges)[0][0]) equals to either 0 or 1 -> 0 if node with index number equal to 0 represents an actual gate,
    # 1 if node with index number equal to 0 does not represent a gate and was just inserted by aigverse.
    # From aigverse documentation (https://aigverse.readthedocs.io/en/stable/api/aigverse/adapters/networkx/index.html): 
    # "Note that the constant-0 node is always included in the graph, as index 0, even if it is not referenced by any edges"
    assert len(nodes) - int(list(graph.edges)[0][0]) + not_gates_amount == len(new_nodes)
    assert len(graph.edges.data()) + not_gates_amount == len(new_edges)

    new_graph = nx.DiGraph()
    new_graph.add_nodes_from(new_nodes)
    new_graph.add_edges_from(new_edges)
    graph = new_graph

    # ASSERT topological order is preserved during not_gates_integration() call
    assert is_topological_order(graph, graph.nodes)

    os.makedirs("./aiger/gv_files_NOT", exist_ok=True)
    with open(f'{"./aiger/gv_files_NOT"}/{benchmark_name}.{"gv"}', 'w') as f:
        # save in .gv file for graph visualization -> AFTER NOT GATES INTEGRATION
        f.write('strict digraph GGraph {\n')
        for n in graph.nodes: f.write(f'"{n}" [label="{n}"];\n')
        for u, v in graph.edges: f.write(f'"{u}" -> "{v}";\n')
        f.write('}')

    # Printing some infos
    print("\tNumber of inputs: " + str(num_inputs))
    print("\tNumber of outputs: " + str(num_outputs))
    print("\tNumber of AND gates: " + str(num_AND_gates))
    print("\tNumber of NOT gates: " + str(not_gates_amount))
    print("\tNumber of constants: " + str(num_constants))

    nodes = list()
    inputs_names = list()
    outputs_names = list()
    for (node_index, attrs) in graph.nodes(True):
        # get features
        node_type = attrs.get('type') # "type" -> [const, pi, gate, po]
        operands = graph.predecessors(node_index)

        # create node
        if node_type[1]:  # input
            inputs_names.append(node_index)
            nodes.append(BoolVariable(node_index))
        elif node_type[3]:  # output
            outputs_names.append(node_index)
            nodes.append(Identity(
                node_index,
                operands,
            ))
        elif node_type[2] == 1:  # and
            nodes.append(And(
                node_index,
                operands,
            ))
        elif node_type[2] == 2:  # not
            nodes.append(Not(
                node_index,
                operands,
            ))
        elif node_type[0]:  # constant
            nodes.append(BoolConstant(
                node_index,
                True,
            ))
        else:
            raise RuntimeError(f'Unable to parse node {node_index} from DiGraph (attributes={attrs})')

    # construct graph
    return IOGraph(
        nodes,
        sorted(inputs_names, key=lambda x: int(x)),
        sorted(outputs_names, key=lambda x: int(x)),
    )

    # TODO: maybe gates dicts, and gates fields

# not_gates_integration:
#  - adds NOT gates and their adjacent edges (while keeping topological order!)
#  - increases 'num_gates' to account for NOT gates (-> count all gates, not only AND gates)
#  - NOT gates get indices starting from 'not_gates_index' (= biggest index among all the AND gates ones, incremented by 1)
#  - AND and NOT gates are distinguished by the 'gate' value in their 'type' one-hot encoded vector -> 1 for AND gates, 2 for NOT gates
#  - 'nodes' might contain a node with 'index' 0 that does not represent an actual gate, it's just automatically inserted by aigverse, 
#    this node is not kept, meaning it's not inserted in 'new_nodes', 'new_nodes' only contains nodes representing either AND or NOT gates
def not_gates_integration(graph: nx.DiGraph, nodes: list, new_nodes: list, new_edges: list, num_gates: int) -> int:
    # 'tmp_edges': list to temporary store edges adjacent to newly added NOT gates (only the edges starting from the NOT gate)
    tmp_edges = []
    # 'and_gates_ptr': index "pointing" to a node in 'nodes', set to 0 if node with index number equal to 0 represents an actual gate,
    # otherwise set to 1 if node with index number equal to 0 does not represent a gate and was just inserted by aigverse.
    and_gates_ptr = 1
    if int(list(graph.edges)[0][0]) == 0:
        and_gates_ptr = 0
    not_gates_index = (nodes[len(nodes) - 1][0]) + 1 # biggest AND index + 1 
    # 'prev_node_index': starting node index of edge considered in the previous iteration, used to detect when all edges starting 
    # from a certain node have been visited and the current edge starts from a different node. When this detection happens, if there
    # are edges in 'tmp_edges', these edges are added to 'new_edges'. Edges are inserted this way to keep the same ordering format given 
    # by aigverse (= the nodes and the edges starting nodes have the same ordering).
    prev_node_index = -1

    for e in graph.edges.data():
        if len(tmp_edges) > 0 and int(e[0]) != prev_node_index:
            for tmp_edge in tmp_edges:
                new_edges.append(tmp_edge)
            tmp_edges.clear()
        # "type" -> [regular, inverted]
        if int(e[2]["type"][1]) == 1:
            num_gates += 1
            while and_gates_ptr < len(nodes) and int(nodes[and_gates_ptr][1]["index"]) <= int(e[0]):
                new_nodes.append(nodes[and_gates_ptr])
                and_gates_ptr += 1
            new_nodes.append((not_gates_index, {'index': not_gates_index, 'type': np.array([0, 0, 2, 0], dtype='int8')})) #NOT gate
            prev_node_index = e[0]
            new_edges.append((e[0], not_gates_index))
            tmp_edges.append((not_gates_index, e[1]))
            not_gates_index += 1
        else:
            new_edges.append((e[0], e[1]))
    while and_gates_ptr < len(nodes):
        new_nodes.append(nodes[and_gates_ptr])
        and_gates_ptr += 1
    for tmp_e in tmp_edges:
        new_edges.append(tmp_e)
    return num_gates