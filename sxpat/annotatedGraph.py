from typing import Dict, List, Callable
from sklearn.cluster import SpectralClustering
from colorama import Fore, Style
import time

import networkx as nx
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *

from .config.config import *
from .config import paths as sxpatpaths
from Z3Log.z3solver import Z3solver
from z3 import *

from .templateSpecs import TemplateSpecs

from z_marco.utils import pprint


class AnnotatedGraph(Graph):
    def __init__(self, benchmark_name: str, is_clean: bool = False, partitioning_percentage: int = 50) -> None:
        # Prepare a clean Verilog
        Verilog(benchmark_name)
        # Convert the clean Verilog into a Yosys GV
        convert_verilog_to_gv(benchmark_name)
        # exit()
        super().__init__(benchmark_name, is_clean)
        folder, extension = INPUT_PATH['ver']

        self.set_output_dict(self.sort_dict(self.output_dict))

        self.__partitioning_percentage = partitioning_percentage

        self.__subgraph = None
        self.__subgraph_input_dict = None
        self.__subgraph_output_dict = None
        self.__subgraph_gate_dict = None
        self.__subgraph_fanin_dict = None
        self.__subgraph_fanout_dict = None
        self.__graph_intact_gate_dict = None

        self.__subgraph_num_inputs = None
        self.__subgraph_num_outputs = None
        self.__subgraph_num_gates = None
        self.__subgraph_num_fanin = None
        self.__subgraph_num_fanout = None
        self.__graph_num_intact_gates = None

        self.__add_weights()

        folder, extension = OUTPUT_PATH[GV]
        self.__out_annotated_graph_path = f'{folder}/{self.name}_subgraph.{extension}'

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage

    @property
    def subgraph(self):
        return self.__subgraph

    @subgraph.setter
    def subgraph(self, this_subgraph):
        self.__subgraph = this_subgraph

    @property
    def subgraph_out_path(self):
        return self.__out_annotated_graph_path

    @property
    def subgraph_input_dict(self):
        return self.__subgraph_input_dict

    @subgraph_input_dict.setter
    def subgraph_input_dict(self, this_subgraph_input_dict):
        self.__subgraph_input_dict = this_subgraph_input_dict

    @property
    def subgraph_output_dict(self):
        return self.__subgraph_output_dict

    @subgraph_output_dict.setter
    def subgraph_output_dict(self, this_subgraph_output_dict):
        self.__subgraph_output_dict = this_subgraph_output_dict

    @property
    def subgraph_gate_dict(self):
        return self.__subgraph_gate_dict

    @subgraph_gate_dict.setter
    def subgraph_gate_dict(self, this_subgraph_gate_dict):
        self.__subgraph_gate_dict = this_subgraph_gate_dict

    @property
    def graph_intact_gate_dict(self):
        return self.__graph_intact_gate_dict

    @graph_intact_gate_dict.setter
    def graph_intact_gate_dict(self, this_graph_intact_gate_dict):
        self.__graph_intact_gate_dict = this_graph_intact_gate_dict

    @property
    def subgraph_fanin_dict(self):
        return self.__subgraph_fanin_dict

    @subgraph_fanin_dict.setter
    def subgraph_fanin_dict(self, this_subgraph_fanin_dict):
        self.__subgraph_fanin_dict = this_subgraph_fanin_dict

    @property
    def subgraph_fanout_dict(self):
        return self.__subgraph_fanout_dict

    @subgraph_fanout_dict.setter
    def subgraph_fanout_dict(self, this_subgraph_fanout_dict):
        self.__subgraph_fanout_dict = this_subgraph_fanout_dict

    @property
    def subgraph_num_inputs(self):
        return self.__subgraph_num_inputs

    @subgraph_num_inputs.setter
    def subgraph_num_inputs(self, this_subgraph_num_inputs):
        self.__subgraph_num_inputs = this_subgraph_num_inputs

    @property
    def subgraph_num_outputs(self):
        return self.__subgraph_num_outputs

    @subgraph_num_outputs.setter
    def subgraph_num_outputs(self, this_subgraph_num_outputs):
        self.__subgraph_num_outputs = this_subgraph_num_outputs

    @property
    def subgraph_num_gates(self):
        return self.__subgraph_num_gates

    @subgraph_num_gates.setter
    def subgraph_num_gates(self, this_subgraph_num_gates):
        self.__subgraph_num_gates = this_subgraph_num_gates

    @property
    def subgraph_num_fanin(self):
        return self.__subgraph_num_fanin

    @subgraph_num_fanin.setter
    def subgraph_num_fanin(self, this_subgraph_num_fanin):
        self.__subgraph_num_fanin = this_subgraph_num_fanin

    @property
    def subgraph_num_fanout(self):
        return self.__subgraph_num_fanout

    @subgraph_num_fanout.setter
    def subgraph_num_fanout(self, this_subgraph_num_fanout):
        self.__subgraph_num_fanout = this_subgraph_num_fanout

    def sort_dict(self, this_dict: Dict) -> Dict:
        return dict(sorted(this_dict.items(), key=lambda x: x[0]))

    def __add_weights(self):
        for n in self.graph.nodes:
            self.graph.nodes[n][WEIGHT] = 1
        #
        # for n in self.graph.nodes.items():
        #     print(f'{n = }')
        #
        # exit()

    def __repr__(self):
        return f'An object of class AnnotatedGraph:\n' \
               f'{self.name = }\n' \
               f'{self.subgraph_num_inputs = }\n' \
               f'{self.subgraph_num_outputs = }\n' \
               f'{self.subgraph_num_gates = }\n' \
               f'{self.partitioning_percentage = }\n'

    def extract_subgraph(self, specs_obj: TemplateSpecs):

        if self.num_gates == 0:
            pprint.with_color(Fore.LIGHTYELLOW_EX)(f'No gates are found in the graph! Skipping the subgraph extraction')
            return False
        else:
            if specs_obj.subxpat:
                mode = specs_obj.mode
                if mode == 1:
                    pprint.info2(f"Partition with imax={specs_obj.imax} and omax={specs_obj.omax}. Looking for largest partition")
                    self.subgraph = self.find_subgraph(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")
                elif mode == 2:
                    pprint.info2(f"Partition with sensitivity start... Using imax={specs_obj.imax}, omax={specs_obj.omax},"
                                 f"and min_subgraph_size={specs_obj.min_subgraph_size}")
                    iteration = 1
                    cnt_nodes = 0
                    specs_obj.sensitivity = 1
                    n_outputs = len(self.output_dict)

                    while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                        # specs_obj.sensitivity = iteration
                        pprint.with_color(Fore.LIGHTBLUE_EX)(f"Sugraph iteration {iteration} ")
                        self.subgraph = self.find_subgraph_sensitivity(specs_obj)

                        # Count how many nodes are in the subgraph
                        cnt_nodes = 0
                        for gate_idx in self.gate_dict:
                            if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                                cnt_nodes += 1

                        pprint.success(f" (#ofNodes={cnt_nodes})")

                        iteration += 1
                        specs_obj.sensitivity = 2 ** iteration - 1
                elif mode == 3:
                    pprint.info2(f"Partition with sensitivity start... Using only min_subgraph_size={specs_obj.min_subgraph_size} parameter")
                    iteration = 1
                    cnt_nodes = 0
                    specs_obj.sensitivity = 1
                    n_outputs = len(self.output_dict)

                    while (cnt_nodes < specs_obj.min_subgraph_size and iteration < n_outputs + 1):
                        # specs_obj.sensitivity = iteration
                        pprint.info2(f"Sugraph iteration {iteration}")
                        self.subgraph = self.find_subgraph_sensitivity_no_io_constraints(specs_obj)

                        # Count how many nodes are in the subgraph
                        cnt_nodes = 0
                        for gate_idx in self.gate_dict:
                            if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                                cnt_nodes += 1

                        pprint.success(f" (#ofNodes={cnt_nodes})")

                        iteration += 1
                        specs_obj.sensitivity = 2 ** iteration - 1
                elif mode == 4:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and feasibility constraints. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")
                elif mode == 5:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and hard feasibility constraints. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible_hard(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")
                else:
                    raise Exception('invalid mode!')
            else:
                self.subgraph = self.entire_graph()

            self.export_annotated_graph()

            self.subgraph_input_dict = self.extract_subgraph_inputs()
            self.subgraph_output_dict = self.extract_subgraph_outputs()
            self.subgraph_gate_dict = self.extract_subgraph_gates()
            self.subgraph_fanin_dict = self.extract_subgraph_fanin()
            self.subgraph_fanout_dict = self.extract_subgraph_fanout()
            self.graph_intact_gate_dict = self.extract_graph_intact_gates()

            self.subgraph_num_inputs = len(self.subgraph_input_dict)
            self.subgraph_num_outputs = len(self.subgraph_output_dict)
            self.subgraph_num_gates = len(self.subgraph_gate_dict)
            self.subgraph_num_fanin = len(self.subgraph_fanin_dict)
            self.subgraph_num_fanout = len(self.subgraph_fanout_dict)
            self.graph_num_intact_gates = len(self.__graph_intact_gate_dict)

            if self.subgraph_num_gates == 0:
                return False
            else:
                return True

    def find_subgraph(self, specs_obj: TemplateSpecs):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        # pprint.info2( f'finding a subgraph (imax={imax}, omax={omax}) for {self.name}... ')
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph: nx.DiGraph = self.graph.copy(as_view=False)
        # print(f'{tmp_graph.nodes = }')
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in self.constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in self.constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    exit(0)
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

                # =============================

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges
        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))

            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in self.constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Generate structure with gate weights
        gate_weight = {}
        for gate_idx in G.nodes:
            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[self.gate_dict[gate_idx]][WEIGHT]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        # Find max weight
        max_weight = 0
        for gate_id in gate_weight:
            max_weight = max(max_weight, gate_weight[gate_id])

        # Update gate weights so that gate_weight = max_weight - max_weight
        for gate_id in gate_weight:
            gate_weight[gate_id] = max_weight - gate_weight[
                gate_id] + 1  # + 1 must be removed, I'm leaving it just for the initial debugging phase

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of input/output edges
        opt.add(Sum(partition_input_edges) <= imax)
        opt.add(Sum(partition_output_edges) <= omax)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id] * gate_weight[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT ", end='')
            # print(opt.model())
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition
        else:
            pprint.warning("subgraph not found -> UNSAT")

        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    # print(f'{u = }')
                    # print(f'{v = }')
                    # print(f'{G.nodes = }')
                    # print(f'{G.edges = }')
                    # print(f'{gate_literals = }')
                    # print(f'{node_partition = }')
                    path = nx.shortest_path(G, source=u, target=v)
                    all_nodes_in_partition = True

                    # Check that all the nodes in the shortest path are in the partition
                    for n in path:
                        if n not in node_partition:
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")
                        exit(0)

                except nx.exception.NetworkXNoPath:
                    # print('Here')
                    # except:
                    # pprint.error(f'Node {u} or {v} do not belong to the graph G {G.nodes}')
                    # raise nx.exception.NetworkXNoPath
                    # No path between u and v

                    # print("No path", u, v)
                    pass

        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def find_subgraph_sensitivity(self, specs_obj: TemplateSpecs):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        sensitivity_t = specs_obj.sensitivity

        # pprint.info2( f'finding a subgraph (imax={imax}, omax={omax}) for {self.name}... ')
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{tmp_graph.nodes = }')
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in self.constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in self.constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    exit(0)
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

                # =============================

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges and data structures containing the edge weights
        edge_w = {}
        edge_constraint = {}

        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            if source not in edge_w:
                edge_w[source] = tmp_graph.nodes[self.gate_dict[source]][WEIGHT]

            if source not in edge_constraint:
                edge_constraint[source] = Or(edge_out_holder)
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))
            if predecessor not in edge_w:
                edge_w[predecessor] = tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT]
            if predecessor not in edge_constraint:
                edge_constraint[predecessor] = e_out
            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in self.constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Generate structure with gate weights
        gate_weight = {}
        for gate_idx in G.nodes:
            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[self.gate_dict[gate_idx]][WEIGHT]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        # Find max weight
        max_weight = 0
        for gate_id in gate_weight:
            max_weight = max(max_weight, gate_weight[gate_id])

        # Update gate weights so that gate_weight = max_weight - max_weight
        for gate_id in gate_weight:
            gate_weight[gate_id] = max_weight - gate_weight[
                gate_id] + 1  # + 1 must be removed, I'm leaving it just for the initial debugging phase

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of input/output edges
        opt.add(Sum(partition_input_edges) <= imax)
        opt.add(Sum(partition_output_edges) <= omax)

        sensitivity_constraints = []
        for s in edge_w:
            sensitivity_constraints.append(edge_constraint[s] * edge_w[s])

        opt.add(Sum(sensitivity_constraints) <= sensitivity_t)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT", end='')
            # print(opt.model())
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition
        else:
            pprint.warning("subgraph not found -> UNSAT")

        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    # print(f'{u = }')
                    # print(f'{v = }')
                    # print(f'{G.nodes = }')
                    # print(f'{G.edges = }')
                    # print(f'{gate_literals = }')
                    # print(f'{node_partition = }')
                    path = nx.shortest_path(G, source=u, target=v)
                    all_nodes_in_partition = True

                    # Check that all the nodes in the shortest path are in the partition
                    for n in path:
                        if n not in node_partition:
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")
                        exit(0)

                except nx.exception.NetworkXNoPath:
                    # print('Here')
                    # except:
                    # pprint.error(f'Node {u} or {v} do not belong to the graph G {G.nodes}')
                    # raise nx.exception.NetworkXNoPath
                    # No path between u and v

                    # print("No path", u, v)
                    pass

        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def find_subgraph_sensitivity_no_io_constraints(self, specs_obj: TemplateSpecs):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        sensitivity_t = specs_obj.sensitivity

        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{tmp_graph.nodes = }')
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in self.constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in self.constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    exit(0)
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

                # =============================

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges and data structures containing the edge weights
        edge_w = {}
        edge_constraint = {}

        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            if source not in edge_w:
                edge_w[source] = tmp_graph.nodes[self.gate_dict[source]][WEIGHT]

            if source not in edge_constraint:
                edge_constraint[source] = Or(edge_out_holder)
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))
            if predecessor not in edge_w:
                edge_w[predecessor] = tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT]
            if predecessor not in edge_constraint:
                edge_constraint[predecessor] = e_out
            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in self.constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Generate structure with gate weights
        gate_weight = {}
        for gate_idx in G.nodes:
            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[self.gate_dict[gate_idx]][WEIGHT]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        # Find max weight
        max_weight = 0
        for gate_id in gate_weight:
            max_weight = max(max_weight, gate_weight[gate_id])

        # Update gate weights so that gate_weight = max_weight - max_weight
        for gate_id in gate_weight:
            gate_weight[gate_id] = max_weight - gate_weight[
                gate_id] + 1  # + 1 must be removed, I'm leaving it just for the initial debugging phase

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of input/output edges
        # opt.add(Sum(partition_input_edges) <= imax)
        # opt.add(Sum(partition_output_edges) <= omax)

        sensitivity_constraints = []
        for s in edge_w:
            sensitivity_constraints.append(edge_constraint[s] * edge_w[s])

        opt.add(Sum(sensitivity_constraints) <= sensitivity_t)
        # print(f'{sensitivity_constraints = }')
        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])
        # print(f'{max_func = }')
        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT", end='')
            # print(opt.model())
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition
        else:
            pprint.warning("subgraph not found -> UNSAT")

        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    # print(f'{u = }')
                    # print(f'{v = }')
                    # print(f'{G.nodes = }')
                    # print(f'{G.edges = }')
                    # print(f'{gate_literals = }')
                    # print(f'{node_partition = }')
                    path = nx.shortest_path(G, source=u, target=v)
                    all_nodes_in_partition = True

                    # Check that all the nodes in the shortest path are in the partition
                    for n in path:
                        if n not in node_partition:
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")
                        exit(0)

                except nx.exception.NetworkXNoPath:
                    # print('Here')
                    # except:
                    # pprint.error(f'Node {u} or {v} do not belong to the graph G {G.nodes}')
                    # raise nx.exception.NetworkXNoPath
                    # No path between u and v

                    # print("No path", u, v)
                    pass

        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def find_subgraph_feasible(self, specs_obj: TemplateSpecs):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        omax = specs_obj.omax
        feasibility_treshold = specs_obj.et
        # print(f'{feasibility_treshold = }')

        # pprint.info2(f'finding a subgraph (imax={imax}, omax={omax}) for {self.name}... ')
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{tmp_graph.nodes = }')
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in self.constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in self.constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    exit(0)
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

                # =============================

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges and data structures containing the edge weights
        edge_w = {}
        edge_constraint = {}

        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            if source not in edge_w:
                edge_w[source] = tmp_graph.nodes[self.gate_dict[source]][WEIGHT]

            if source not in edge_constraint:
                edge_constraint[source] = Or(edge_out_holder)
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))
            if predecessor not in edge_w:
                edge_w[predecessor] = tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT]
            if predecessor not in edge_constraint:
                edge_constraint[predecessor] = e_out
            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in self.constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Generate structure with gate weights
        # for n in self.graph.nodes:
        #     print(f'{self.graph.nodes[n][WEIGHT] = }, {n =}')
        # print(f'{self.gate_dict = }')
        gate_weight = {}
        for gate_idx in G.nodes:

            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[self.gate_dict[gate_idx]][WEIGHT]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of output edges
        opt.add(Sum(partition_output_edges) <= omax)

        feasibility_constraints = []
        for s in edge_w:

            if gate_weight[s] <= feasibility_treshold:
                # print(s, "is feasible", gate_weight[s])
                feasibility_constraints.append(edge_constraint[s])

        opt.add(Sum(feasibility_constraints) >= 1)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT", end='')
            # print(opt.model())
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition
        else:
            pprint.warning("subgraph not found -> UNSAT")

        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    # print(f'{u = }')
                    # print(f'{v = }')
                    # print(f'{G.nodes = }')
                    # print(f'{G.edges = }')
                    # print(f'{gate_literals = }')
                    # print(f'{node_partition = }')
                    path = nx.shortest_path(G, source=u, target=v)
                    all_nodes_in_partition = True

                    # Check that all the nodes in the shortest path are in the partition
                    for n in path:
                        if n not in node_partition:
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")
                        exit(0)

                except nx.exception.NetworkXNoPath:
                    # print('Here')
                    # except:
                    # pprint.error(f'Node {u} or {v} do not belong to the graph G {G.nodes}')
                    # raise nx.exception.NetworkXNoPath
                    # No path between u and v

                    # print("No path", u, v)
                    pass

        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def find_subgraph_feasible_hard(self, specs_obj: TemplateSpecs):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        omax = specs_obj.omax
        feasibility_treshold = specs_obj.et
        # print(f'{feasibility_treshold = }')

        # pprint.info2(f'finding a subgraph (imax={imax}, omax={omax}) for {self.name}... ')
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        # print(f'Extracting subgraph...')

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{tmp_graph.nodes = }')
        # Data structures containing the literals
        input_literals = {}  # literals associated to the input nodes
        gate_literals = {}  # literals associated to the gates in the circuit
        output_literals = {}  # literals associated to the output nodes

        # Data structures containing the edges
        input_edges = {}  # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}  # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}  # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []  # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []  # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:  # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals and g_id not in self.constant_dict:  # Not in constant_dict since we don't care about constants
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))

            if 'out' in e[1]:  # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))

        # Generate structures holding edge information
        for e in tmp_graph.edges:
            if 'in' in e[0]:  # Populate input_edges structure
                in_id = int(e[0][2:])

                if in_id not in input_edges:
                    input_edges[in_id] = []
                # input_edges[in_id].append(int(e[1][1:])) # this is a bug for a case where e = (in1, out1)
                # Morteza added ==============
                try:
                    input_edges[in_id].append(int(e[1][1:]))
                except:
                    if re.search('g(\d+)', e[1]):
                        my_id = int(re.search('g(\d+)', e[1]).group(1))
                        input_edges[in_id].append(my_id)
                # =============================

            if 'g' in e[0] and 'g' in e[1]:  # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])

                if ns_id in self.constant_dict:
                    print("ERROR: Constants should only be connected to output nodes")
                    exit(0)
                if ns_id not in gate_edges:
                    gate_edges[ns_id] = []
                # try:
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:  # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                # output_edges[out_id].append(int(e[0][1:]))
                # Morteza added ==============
                try:
                    output_edges[out_id].append(int(e[0][1:]))
                except:
                    my_id = int(re.search('(\d+)', e[0]).group(1))
                    output_edges[out_id].append(my_id)

                # =============================

        # Define input edges
        for source in input_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in input_edges[source]:
                e_in = And(Not(input_literals[source]), gate_literals[destination])

                edge_in_holder.append(e_in)

            partition_input_edges.append(Or(edge_in_holder))

        # Define gate edges and data structures containing the edge weights
        edge_w = {}
        edge_constraint = {}

        for source in gate_edges:
            edge_in_holder = []
            edge_out_holder = []

            for destination in gate_edges[source]:
                e_in = And(Not(gate_literals[source]), gate_literals[destination])
                e_out = And(gate_literals[source], Not(gate_literals[destination]))

                edge_in_holder.append(e_in)
                edge_out_holder.append(e_out)

            partition_input_edges.append(Or(edge_in_holder))
            if source not in edge_w:
                edge_w[source] = tmp_graph.nodes[self.gate_dict[source]][WEIGHT]

            if source not in edge_constraint:
                edge_constraint[source] = Or(edge_out_holder)
            partition_output_edges.append(Or(edge_out_holder))

        # Define output edges
        for output_id in output_edges:
            predecessor = output_edges[output_id][
                0]  # Output nodes have only one predecessor  (it could be a gate or it could be an input)
            if predecessor not in gate_literals:  # This handle cases where input and output are directly connected
                continue
            e_out = And(gate_literals[predecessor], Not(output_literals[output_id]))
            if predecessor not in edge_w:
                edge_w[predecessor] = tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT]
            if predecessor not in edge_constraint:
                edge_constraint[predecessor] = e_out
            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()
        # print(f'{tmp_graph.edges = }')
        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)
        # Morteza added =====================
        for e in tmp_graph.edges:
            if 'g' in str(e[0]):
                source = int(e[0][1:])
                if source in self.constant_dict:
                    continue
                G.add_node(source)
        # ===================================

        # Generate structure with gate weights
        # for n in self.graph.nodes:
        #     print(f'{self.graph.nodes[n][WEIGHT] = }, {n =}')
        # print(f'{self.gate_dict = }')
        gate_weight = {}
        for gate_idx in G.nodes:

            if gate_idx not in gate_weight:
                gate_weight[gate_idx] = tmp_graph.nodes[self.gate_dict[gate_idx]][WEIGHT]
            # print("Gate", gate_idx, " value ", gate_weight[gate_idx])

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G, n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G, n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:  # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])),
                                                  And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:  # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]),
                                                 And(not_ancestors))
                    opt.add(ancestor_condition)

        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of output edges
        opt.add(Sum(partition_output_edges) <= omax)

        feasibility_constraints = []
        for s in edge_w:

            if gate_weight[s] <= feasibility_treshold:
                # print(s, "is feasible", gate_weight[s])
                feasibility_constraints.append(edge_constraint[s])

        opt.add(Sum(feasibility_constraints) == Sum(partition_output_edges))

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT", end='')
            # print(opt.model())
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):  # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)  # Gates inside the partition
        else:
            pprint.warning("subgraph not found -> UNSAT")

        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    # print(f'{u = }')
                    # print(f'{v = }')
                    # print(f'{G.nodes = }')
                    # print(f'{G.edges = }')
                    # print(f'{gate_literals = }')
                    # print(f'{node_partition = }')
                    path = nx.shortest_path(G, source=u, target=v)
                    all_nodes_in_partition = True

                    # Check that all the nodes in the shortest path are in the partition
                    for n in path:
                        if n not in node_partition:
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")
                        exit(0)

                except nx.exception.NetworkXNoPath:
                    # print('Here')
                    # except:
                    # pprint.error(f'Node {u} or {v} do not belong to the graph G {G.nodes}')
                    # raise nx.exception.NetworkXNoPath
                    # No path between u and v

                    # print("No path", u, v)
                    pass

        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def entire_graph(self):
        tmp_graph = self.graph.copy()

        for gate_idx in self.gate_dict:

            tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
            tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED

        return tmp_graph

    def export_annotated_graph(self, filename: str = None):
        """
        exports the subgraph (annotated graph) to a GV (GraphViz) file
        :return:
        """
        # print(f'exporting the annotated subgraph!')
        # print(f'{self.subgraph_out_path = }')
        with open(filename or self.subgraph_out_path, 'w') as f:
            f.write(f"{STRICT} {DIGRAPH} \"{self.name}\" {{\n")
            f.write(f"{NODE} [{STYLE} = {FILLED}, {FILLCOLOR} = {WHITE}]\n")
            for n in self.subgraph.nodes:
                self.export_node(n, f)
            for e in self.subgraph.edges:
                self.export_edge(e, f)
            f.write(f"}}\n")
        folder, extension = OUTPUT_PATH[GV]
        # print(f'{self.subgraph_out_path = }')
        # print(f'{self.name = }')
        subprocess.run(f'dot -Tpng {self.subgraph_out_path} > {folder}/{self.name}_subgraph.png', shell=True)

    # TODO:for external modifications
    def evaluate_subgraph_error(self) -> float:
        """
        This function removes the annotated part (so called the subgraph) of the graph and the evaluates the error (which
        is a metric of choice)
        :return: the computed error
        """
        # 1) read the exact circuit
        # 2) create a copy of the self.graph and remove the annotated nodes, and consider it as an approximate graph
        return 0.0

    # TODO: fix checks!
    # The checks are done on the original graph instead of the annotated graph!
    def export_node(self, n, file_handler: io.TextIOBase):
        """
        exports node n as a line of file that is identified by file_hanlder
        :param n: the label of node n
        :param file_handler: the file object
        :return: nothing
        """
        if self.is_cleaned_pi(n) or self.is_cleaned_po(n):
            if WEIGHT in self.subgraph.nodes[n]:
                label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\""
            else:
                label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\""

            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            elif COLOR in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        elif self.is_cleaned_gate(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\\n{self.subgraph.nodes[n][WEIGHT]}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        elif self.is_cleaned_constant(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            if WEIGHT in self.subgraph.nodes[n]:
                weight = f'{WEIGHT} = {self.subgraph.nodes[n][WEIGHT]}'
            else:
                weight = f'{WEIGHT} = -1'
        else:
            pprint.error(f'ERROR!!! a problem occurred while exporting an annotated graph {self.__out_annotated_graph_path}')
            exit()
        line = f"{n} [{label}, {shape}, {color}, {weight}];\n"
        file_handler.write(line)

    def color_subgraph_node(self, n, this_color):
        """
        changes the color of node n to this_color.
        :param n: the label of node n
        :param this_color: the desired color
        :return: nothing
        """
        self.subgraph.nodes[n][COLOR] = this_color

    def is_subgraph_member(self, n):
        """
        checks whether node n belongs to the subgraph
        :param n: a node
        :return: True if node n belongs to the subgraph, otherwise returns False
        """
        if SUBGRAPH in self.subgraph.nodes[n]:
            if self.subgraph.nodes[n][SUBGRAPH] == 1:
                return True
            else:
                return False
        else:
            return False

    def is_subgraph_fanin(self, n):
        """
        checks whether node n is in the fanin logic of the subgraph
        :param n: a node
        :return: True if node n is in the fanin logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if self.is_subgraph_member(sn):
                    return True
        else:
            return False

    def is_subgraph_fanout(self, n):
        """
        checks whether node n is in the fanout logic of the subgraph
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            predecessors = list(self.subgraph.predecessors(n))
            for pn in predecessors:
                if self.is_subgraph_member(pn):
                    return True
        else:
            return False

    def is_subgraph_output(self, n):
        """
        checks whether node n is an output node of the subgraph; an output node is node that has an outgoing edge
        from the subgraph.
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if not self.is_subgraph_member(sn):
                    return True
        return False

    # TODO:
    # This part should generate a comment in verilog expressing:
    # Annotated subgraph inputs

    def is_subgraph_input(self, n):
        """
        checks whether node n is an input node of the subgraph; an input node is a (non-member) node that has an ingoing edge
        to the subgraph.
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
        if not self.is_subgraph_member(n):
            successors = list(self.subgraph.successors(n))
            for sn in successors:
                if self.is_subgraph_member(sn):
                    return True

        return False

    def extract_subgraph_gates(self) -> Dict[int, str]:
        """
        extracts subgraph gates and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: gate_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_gates_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())

        for n in self.subgraph.nodes:
            if SUBGRAPH in self.subgraph.nodes[n] and self.subgraph.nodes[n][SUBGRAPH] == 1:
                s_gates_dict[graph_gate_list.index(n)] = n

        return s_gates_dict

    def extract_graph_intact_gates(self):
        """
        extracts non-subgraph gates and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: gate_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_gates_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())

        for n in graph_gate_list:
            if not self.is_subgraph_member(n):
                s_gates_dict[graph_gate_list.index(n)] = n

        return s_gates_dict

    def extract_subgraph_inputs(self):
        """
        extracts subgraph inputs (non-member nodes) and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: subgraph_input_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        s_input_dict: Dict[int, str] = {}
        idx = 0
        for n in self.graph.nodes:
            if self.is_subgraph_input(n):
                s_input_dict[idx] = n
                idx += 1
        return s_input_dict

    def extract_subgraph_outputs(self):
        """
        extracts subgraph outputs and stores them in a dictionary where keys are indices and values are gate labels
        :return: a dictionary; ex: subgraph_output_dict = {gate_idx0: gate_label0, ..., gate_idxn: gate_labeln}
        """
        tmp_output_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_output(n):
                tmp_output_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, BLUE)
        # print(f'{tmp_output_dict = }')
        return tmp_output_dict

    # TODO
    # Deprecated
    def extract_subgraph_fanin(self):
        tmp_fanin_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_fanin(n):
                tmp_fanin_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, OLIVE)
        return tmp_fanin_dict

    def extract_subgraph_fanout(self):
        tmp_fanout_dict: Dict[int, str] = {}
        graph_gate_list: List[str] = list(self.gate_dict.values())
        idx = 0
        for n in self.subgraph.nodes:
            if self.is_subgraph_fanout(n):
                tmp_fanout_dict[idx] = n
                idx += 1
                self.color_subgraph_node(n, WHITE)
        return tmp_fanout_dict
