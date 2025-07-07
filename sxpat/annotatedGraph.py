from typing import Dict, List
from colorama import Fore
import time
import datetime  # precautionary measure
import networkx as nx
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *

from .config.config import *
from z3 import *

from .specifications import Specifications, TemplateType

from sxpat.utils.utils import pprint


class AnnotatedGraph(Graph):
    def __init__(self, benchmark_name: str, is_clean: bool = False) -> None:
        # Prepare a clean Verilog
        Verilog(benchmark_name)
        # Convert the clean Verilog into a Yosys GV
        convert_verilog_to_gv(benchmark_name)

        super().__init__(benchmark_name, is_clean)
        folder, extension = INPUT_PATH['ver']

        self.set_output_dict(self.sort_dict(self.output_dict))

        self.__subgraph_candidates = []
        self.__subgraph = None
        self.__subgraph_input_dict: Dict[int, str] = None
        self.__subgraph_output_dict: Dict[int, str] = None
        self.__subgraph_gate_dict: Dict[int, str] = None
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
    def subgraph_candidates(self):
        return self.__subgraph_candidates

    @subgraph_candidates.setter
    def subgraph_candidates(self, this_candidates):
        self.__subgraph_candidates = this_candidates

    @property
    def subgraph(self):
        return self.__subgraph

    @subgraph.setter
    def subgraph(self, this_subgraph):
        self.__subgraph = this_subgraph

    @property
    def subgraph_out_path(self):
        return self.__out_annotated_graph_path

    @subgraph_out_path.setter
    def subgraph_out_path(self, this_subgraph_out_path):
        self.__out_annotated_graph_path = this_subgraph_out_path

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

    def get_subgraph_name(self, specs_obj: Specifications):
        """
        returns: a unique gv file name for this experiment (that is determined by specs_obj)
        """
        _, extension = OUTPUT_PATH[GV]

        # TODO: Morteza: this naming convention is not generic enough,
        # I will try to add every type of specification of the experiment into the name so it wouldn't get overwritten
        # new fields that are added:
        # for subxpat_v2 => et_partitioning
        # for all num_of_models, omax, imax
        # as a precautionary measure, we also add the time stamp at the end of every generated file

        # So we change the names from "grid_adder_i6_o4_10X20_et10_subxpat_v2_mode4_SOP1" to
        # 'grid_adder_i6_o4_10X20_et10_subxpat_v2_desc_fef1_sef1_mode4_omax1_imax3_kucTrue_SOP1_time20240403:214107'

        # let's divide our nomenclature into X parts: head (common), technique_specific, tail (common)

        head = f'grid_{specs_obj.current_benchmark}_{specs_obj.lpp}X{specs_obj.pit if specs_obj.template is TemplateType.SHARED else specs_obj.ppo}_et{specs_obj.et}_'

        tool_name = {
            (False, TemplateType.NON_SHARED): XPAT,
            (False, TemplateType.SHARED): SHARED_XPAT,
            (True, TemplateType.NON_SHARED): SUBXPAT,
            (True, TemplateType.SHARED): SHARED_SUBXPAT,
        }[(specs_obj.subxpat, specs_obj.template)]

        technique_specific = f'{tool_name}_{specs_obj.error_partitioning.value}_'

        tail = f'mode{specs_obj.extraction_mode}_omax{specs_obj.omax}_imax{specs_obj.imax}_'
        tail += f'{specs_obj.template_name}_time'

        # Get the current date and time
        current_time = datetime.datetime.now()
        # Format the date and time to create a unique identifier
        time_stamp = current_time.strftime("%Y%m%d:%H%M%S")

        name = head + technique_specific + tail + time_stamp

        return f'{name}.{extension}'

    def get_subgraph_path(self, specs: Specifications):
        """
        returns: the path where the grid .gv file should be stored
        """
        folder, _ = OUTPUT_PATH[GV]
        path = f'{folder}/{self.get_subgraph_name(specs)}'
        return path

    def __add_weights(self):
        for n in self.graph.nodes:
            self.graph.nodes[n][WEIGHT] = 1

    def __repr__(self):
        return f'An object of class AnnotatedGraph:\n' \
               f'{self.name = }\n' \
               f'{self.subgraph_num_inputs = }\n' \
               f'{self.subgraph_num_outputs = }\n' \
               f'{self.subgraph_num_gates = }\n'

    def extract_subgraph(self, specs_obj: Specifications):

        if self.num_gates == 0:
            pprint.with_color(Fore.LIGHTYELLOW_EX)(f'No gates are found in the graph! Skipping the subgraph extraction')
            return False
        else:
            if specs_obj.requires_subgraph_extraction:
                if specs_obj.extraction_mode == 1:
                    pprint.info2(f"Partition with imax={specs_obj.imax} and omax={specs_obj.omax}. Looking for largest partition")
                    self.subgraph = self.find_subgraph(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 2:
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

                elif specs_obj.extraction_mode == 3:
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

                elif specs_obj.extraction_mode == 4:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and feasibility constraints. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible(specs_obj)  # Cristian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 5:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and hard feasibility constraints. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible_hard(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 55:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and hard constraints, imax, omax, assumptions, and BitVec, DataType. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1
                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 6:
                    pprint.info2(f"Partition with hard constraints, imax={specs_obj.imax}, omax={specs_obj.omax}, assumptions, and BitVec, DataType. Looking for largest partition for smallest possible threshold")

                    self.subgraph = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold(specs_obj)

                    # log count
                    cnt_nodes = sum(
                        self.subgraph.nodes[gate_name][SUBGRAPH] == 1
                        for gate_name in self.gate_dict.values()
                    )
                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 100:
                    pprint.info2(f"Test with no imax, omax")
                    self.subgraph = self.slash_to_kill(specs_obj)
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1
                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 11:
                    pprint.info2(f"Partition with omax={specs_obj.omax} and soft feasibility constraints. Looking for largest partition")
                    self.subgraph = self.find_subgraph_feasible_soft(specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                    pprint.success(f" (#ofNodes={cnt_nodes})")

                elif specs_obj.extraction_mode == 12:
                    if self.subgraph_candidates:
                        pprint.info2(
                            f"Selecting the next subgraph candidate")
                        self.subgraph = self.form_subgraph_from_partition()
                    else:
                        pprint.info2(
                            f"Partition with omax={specs_obj.omax} and soft feasibility constraints on subgraph outputs. Looking for largest partition")
                        self.subgraph = self.find_subgraph_feasible_soft_outputs(
                            specs_obj)  # Critian's subgraph extraction
                    cnt_nodes = 0
                    for gate_idx in self.gate_dict:
                        if self.subgraph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] == 1:
                            cnt_nodes += 1

                else:
                    raise Exception('invalid extraction mode!')
            else:
                self.subgraph = self.entire_graph()

            # Set new name for the subgraph
            self.subgraph_out_path = self.get_subgraph_path(specs_obj)
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

            return self.subgraph_num_gates != 0

    def find_subgraph(self, specs_obj: Specifications):
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
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
            opt.add(Sum(partition_output_edges) <= omax)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id] * gate_weight[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)
        # ====================================================================================================

        node_partition = []
        if opt.check() == sat:
            pprint.success("subgraph found -> SAT ", end='')
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

    def find_subgraph_sensitivity(self, specs_obj: Specifications):
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
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
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
        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)
        # ====================================================================================================
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

    def find_subgraph_sensitivity_no_io_constraints(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
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

        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)
        # ====================================================================================================

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

    def find_subgraph_feasible(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
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

        # Add constraints on the number of input/output edges
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
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
        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)
        # ====================================================================================================
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

    def find_subgraph_feasible_hard(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
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

        # Add constraints on the number of input/output edges
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
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

        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)
        # ====================================================================================================

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

    def find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        # loose bound but since it's logarithmic it's still ok
        NUM_BITS = self.num_outputs + math.ceil(math.log2(self.num_gates))

        omax = specs_obj.omax
        imax = specs_obj.imax
        feasibility_threshold = specs_obj.et

        opt = Optimize()

        Node = Datatype('Node')
        Node.declare('mk_node', ('id', BitVecSort(NUM_BITS)), ('weight', BitVecSort(NUM_BITS)), ('in_subgraph', BoolSort()))
        Node = Node.create()

        # Define a custom datatype for Edge
        Edge = Datatype('Edge')
        Edge.declare('mk_edge', ('source', Node), ('target', Node))
        Edge = Edge.create()

        nodes = {}
        edges = []

        for in_idx in self.input_dict:
            node_label = self.input_dict[in_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(in_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(in_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        for g_idx in self.gate_dict:
            node_label = self.gate_dict[g_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(g_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(g_idx, NUM_BITS))
            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            if weight == -1:
                opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for o_idx in self.output_dict:
            node_label = self.output_dict[o_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(o_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(o_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for c_idx in self.constant_dict:
            node_label = self.constant_dict[c_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(c_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(c_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for src, des in self.graph.edges:
            edge = Edge.mk_edge(nodes[src], nodes[des])
            opt.add(Edge.source(edge) == nodes[src])
            opt.add(Edge.target(edge) == nodes[des])
            edges.append(edge)

        unique_outgoing_edges = []
        unique_incoming_edges = []

        for node_label in nodes:
            node = nodes[node_label]
            outgoing_conditions = []
            incoming_conditions = []

            for src, des in self.graph.edges(node_label):
                if src == node_label:
                    outgoing_conditions.append(And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))))
                if src == node_label:
                    incoming_conditions.append(And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])))

            if outgoing_conditions:
                unique_outgoing_edges.append(If(Or(outgoing_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))
            if incoming_conditions:
                unique_incoming_edges.append(If(Or(incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))

        # incoming_edges = [If(And(Not(Node.in_subgraph(Edge.source(edge))), Node.in_subgraph(Edge.target(edge))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        # outgoint_edges = [If(And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        max_nodes = [If(Node.in_subgraph(node), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)) for node in nodes.values()]

        # max_nodes = [  for edge in edges]
        # max_nodes = [BitVecVal(ToInt(Node.in_subgraph(node)), NUM_BITS) for node in nodes.values()]

        descendants = {}
        ancestors = {}
        for node in nodes:
            if node not in descendants:
                descendants[node] = list(nx.descendants(self.graph, node))
            if node not in ancestors:
                ancestors[node] = list(nx.ancestors(self.graph, node))

        for src in nodes:
            for des in self.graph.successors(src):
                if len(descendants[des]) > 0:
                    not_descendants = [Not(Node.in_subgraph(nodes[l])) for l in descendants[des]]
                    not_descendants.append(Not(Node.in_subgraph(nodes[des])))
                    descendant_condition = Implies(
                        And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))),
                        And(not_descendants)
                    )
                    opt.add(descendant_condition)
                if len(ancestors[src]) > 0:
                    not_ancestors = [Not(Node.in_subgraph(nodes[l])) for l in ancestors[src]]
                    not_ancestors.append(Not(Node.in_subgraph(nodes[src])))
                    ancestor_condition = Implies(
                        And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])),
                        And(not_ancestors)
                    )
                    opt.add(ancestor_condition)

        opt.add(Sum(unique_incoming_edges) <= imax)
        opt.add(Sum(unique_outgoing_edges) <= omax)

        feasibility_constraints = [
            Implies(
                And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),
                Node.weight(Edge.source(edge)) <= BitVecVal(feasibility_threshold, NUM_BITS)
            )
            for edge in edges
        ]

        opt.add(And(feasibility_constraints))

        opt.maximize(Sum(max_nodes))

        # inputs = Int('inputs')
        # outputs = Int('outputs')
        # num_nodes = Int('num_nodes')
        #
        # num_nodes = BitVec('num_nodes', NUM_BITS)
        # inputs = BitVec('inputs', NUM_BITS)
        # outputs = BitVec('outputs', NUM_BITS)

        # feasibility_constraints = [
        #     Implies(Node.in_subgraph(node), Node.weight(node) <= BitVecVal(feasibility_threshold, NUM_BITS)) for node in
        #     nodes.values()
        # ]

        sat_time_s = time.time()
        res = opt.check()

        node_partition = []
        if res == sat:
            n_nodes = 0
            pprint.success("subgraph found -> SAT", end='')
            m = opt.model()
            # print(f'{m = }')
            for t in m.decls():
                # print(f'{type(t) = }')
                # print(f'{t = }')
                if str(t).startswith('g'):  # Look only the literals associate to the gates
                    if is_true(m[t]):
                        node_partition.append(str(t))
                        n_nodes += 1
            # pprint.success(f"(NumOfNodes = {n_nodes})")
        else:
            pprint.warning("subgraph not found -> UNSAT")

        sat_time_e = time.time()

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{node_partition = }')
        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    path = nx.shortest_path(tmp_graph, source=u, target=v)
                    all_nodes_in_partition = True

                    for n in path:
                        if n not in node_partition:
                            # print(f'{node_partition = }')
                            # print(f'{n = }')
                            # print(f'{path = }')
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")

                        exit(0)

                except nx.exception.NetworkXNoPath:
                    pass

        node_partition_idx = [int(re.search('g(\d+)', node).group(1)) for node in node_partition]
        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition_idx:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE

        return tmp_graph

    def get_null_subgraph(self) -> nx.DiGraph:
        """Returns a graph with subgraph information for the null subgraph"""
        subgraph = self.graph.copy()
        for gate_name in self.gate_dict.values():
            subgraph.nodes[gate_name][SUBGRAPH] = 0
            subgraph.nodes[gate_name][COLOR] = WHITE
        return subgraph

    def find_subgraph_feasible_hard_limited_inputs_datatype_bitvec_minthreshold(self, specs_obj: Specifications) -> nx.DiGraph:
        # store parameters that will be updated
        saved_et = specs_obj.et

        # get graph weights, then min/max (bounded)
        weights = sorted(frozenset(
            weight
            for gate_name in self.gate_dict.values()
            if (weight := self.graph.nodes[gate_name][WEIGHT]) >= 0
        ))
        if len(weights) == 0: return self.get_null_subgraph()
        min_weight = max(0, min(weights))
        max_weight = min(saved_et, max(weights))

        # use linear partition to find best match in weights
        partition_step = (max_weight - min_weight) / (8 - 1)
        linear_partition = [min_weight + partition_step * i for i in range(8)]
        actual_partition = sorted(frozenset(
            min(weights, key=lambda w: abs(w - p))
            for p in linear_partition
        ))

        # find subgraph
        # NOTE: given that the node with the smallest weight is a valid subgraph, this loop should only iterate once
        for (i, specs_obj.et) in enumerate(actual_partition):
            found_subgraph = self.find_subgraph_feasible_hard_limited_inputs_datatype_bitvec(specs_obj)  # Critian's subgraph extraction
            cnt_nodes = sum(
                found_subgraph.nodes[gate_name][SUBGRAPH] == 1
                for gate_name in self.gate_dict.values()
            )
            if cnt_nodes > 0: break

        # restore updated parameters
        specs_obj.et = saved_et

        return found_subgraph

    def slash_to_kill(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """

        # loose bound but since it's logarithmic it's still ok
        NUM_BITS = self.num_outputs + math.ceil(math.log2(self.num_gates))

        omax = specs_obj.omax
        imax = specs_obj.imax
        feasibility_threshold = specs_obj.et

        opt = Optimize()

        Node = Datatype('Node')
        Node.declare('mk_node', ('id', BitVecSort(NUM_BITS)), ('weight', BitVecSort(NUM_BITS)), ('in_subgraph', BoolSort()))
        Node = Node.create()

        # Define a custom datatype for Edge
        Edge = Datatype('Edge')
        Edge.declare('mk_edge', ('source', Node), ('target', Node))
        Edge = Edge.create()

        nodes = {}
        edges = []

        for in_idx in self.input_dict:
            node_label = self.input_dict[in_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(in_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(in_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node

        for g_idx in self.gate_dict:
            node_label = self.gate_dict[g_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(g_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(g_idx, NUM_BITS))
            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            if weight == -1:
                opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for o_idx in self.output_dict:
            node_label = self.output_dict[o_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(o_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(o_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for c_idx in self.constant_dict:
            node_label = self.constant_dict[c_idx]
            weight = self.graph.nodes[node_label][WEIGHT]
            node = Node.mk_node(BitVecVal(c_idx, NUM_BITS), BitVecVal(weight, NUM_BITS), Bool(f'{node_label}'))
            opt.add(Node.id(node) == BitVecVal(c_idx, NUM_BITS))

            opt.add(Node.weight(node) == BitVecVal(weight, NUM_BITS))
            opt.add(Node.in_subgraph(node) == BoolVal(False))
            nodes[node_label] = node
        #
        for src, des in self.graph.edges:
            edge = Edge.mk_edge(nodes[src], nodes[des])
            opt.add(Edge.source(edge) == nodes[src])
            opt.add(Edge.target(edge) == nodes[des])
            edges.append(edge)

        unique_outgoing_edges = []
        unique_incoming_edges = []

        for node_label in nodes:
            node = nodes[node_label]
            outgoing_conditions = []
            incoming_conditions = []

            for src, des in self.graph.edges(node_label):
                if src == node_label:
                    outgoing_conditions.append(And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))))
                if src == node_label:
                    incoming_conditions.append(And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])))

            if outgoing_conditions:
                unique_outgoing_edges.append(If(Or(outgoing_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))
            if incoming_conditions:
                unique_incoming_edges.append(If(Or(incoming_conditions), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)))

        # incoming_edges = [If(And(Not(Node.in_subgraph(Edge.source(edge))), Node.in_subgraph(Edge.target(edge))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        # outgoint_edges = [If(And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS))
        #                   for edge in edges]
        max_nodes = [If(Node.in_subgraph(node), BitVecVal(1, NUM_BITS), BitVecVal(0, NUM_BITS)) for node in nodes.values()]

        # max_nodes = [  for edge in edges]
        # max_nodes = [BitVecVal(ToInt(Node.in_subgraph(node)), NUM_BITS) for node in nodes.values()]

        descendants = {}
        ancestors = {}
        for node in nodes:
            if node not in descendants:
                descendants[node] = list(nx.descendants(self.graph, node))
            if node not in ancestors:
                ancestors[node] = list(nx.ancestors(self.graph, node))

        for src in nodes:
            for des in self.graph.successors(src):
                if len(descendants[des]) > 0:
                    not_descendants = [Not(Node.in_subgraph(nodes[l])) for l in descendants[des]]
                    not_descendants.append(Not(Node.in_subgraph(nodes[des])))
                    descendant_condition = Implies(
                        And(Node.in_subgraph(nodes[src]), Not(Node.in_subgraph(nodes[des]))),
                        And(not_descendants)
                    )
                    opt.add(descendant_condition)
                if len(ancestors[src]) > 0:
                    not_ancestors = [Not(Node.in_subgraph(nodes[l])) for l in ancestors[src]]
                    not_ancestors.append(Not(Node.in_subgraph(nodes[src])))
                    ancestor_condition = Implies(
                        And(Not(Node.in_subgraph(nodes[src])), Node.in_subgraph(nodes[des])),
                        And(not_ancestors)
                    )
                    opt.add(ancestor_condition)

        for parent in nodes:
            children = list(self.graph.successors(parent))
            if not children:
                continue
            in_subgraph_children = [Node.in_subgraph(nodes[child]) for child in children]

            # If parent is in the subgraph and at least one child is in, then all children must be in
            opt.add(
                Implies(
                    And(
                        Node.in_subgraph(nodes[parent]),
                        Or(in_subgraph_children)
                    ),
                    And(in_subgraph_children)
                )
            )

        feasibility_sum = Sum([
            If(
                And(Node.in_subgraph(Edge.source(edge)), Not(Node.in_subgraph(Edge.target(edge)))),
                Node.weight(Edge.source(edge)),
                BitVecVal(0, NUM_BITS)
            )
            for edge in edges
        ])

        opt.add(feasibility_sum <= BitVecVal(feasibility_threshold, NUM_BITS))

        opt.maximize(Sum(max_nodes))

        # inputs = Int('inputs')
        # outputs = Int('outputs')
        # num_nodes = Int('num_nodes')
        #
        # num_nodes = BitVec('num_nodes', NUM_BITS)
        # inputs = BitVec('inputs', NUM_BITS)
        # outputs = BitVec('outputs', NUM_BITS)

        # feasibility_constraints = [
        #     Implies(Node.in_subgraph(node), Node.weight(node) <= BitVecVal(feasibility_threshold, NUM_BITS)) for node in
        #     nodes.values()
        # ]

        sat_time_s = time.time()
        res = opt.check()

        node_partition = []
        if res == sat:
            n_nodes = 0
            pprint.success("subgraph found -> SAT", end='')
            m = opt.model()
            # print(f'{m = }')
            for t in m.decls():
                # print(f'{type(t) = }')
                # print(f'{t = }')
                if str(t).startswith('g'):  # Look only the literals associate to the gates
                    if is_true(m[t]):
                        node_partition.append(str(t))
                        n_nodes += 1
            # pprint.success(f"(NumOfNodes = {n_nodes})")
        else:
            pprint.warning("subgraph not found -> UNSAT")

        sat_time_e = time.time()

        tmp_graph = self.graph.copy(as_view=False)
        # print(f'{node_partition = }')
        # Check partition convexity
        for i in range(len(node_partition) - 1):
            for j in range(i + 1, len(node_partition)):
                u = node_partition[i]
                v = node_partition[j]
                try:
                    path = nx.shortest_path(tmp_graph, source=u, target=v)
                    all_nodes_in_partition = True

                    for n in path:
                        if n not in node_partition:
                            # print(f'{node_partition = }')
                            # print(f'{n = }')
                            # print(f'{path = }')
                            all_nodes_in_partition = False

                    if not all_nodes_in_partition:
                        print("Partition is not convex")

                        exit(0)

                except nx.exception.NetworkXNoPath:
                    pass

        node_partition_idx = [int(re.search('g(\d+)', node).group(1)) for node in node_partition]
        for gate_idx in self.gate_dict:
            # print(f'{gate_idx = }')
            if gate_idx in node_partition_idx:
                # print(f'{gate_idx} is in the node_partition')
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE

        return tmp_graph

    def find_subgraph_feasible_soft(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        feasibility_treshold = specs_obj.et

        tmp_graph = self.graph.copy(as_view=False)

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

        # Add constraints on the number of input/output edges
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
            opt.add(Sum(partition_output_edges) <= omax)

        feasibility_constraints = []
        for s in edge_w:
            if gate_weight[s] <= feasibility_treshold and gate_weight[s] != -1:
                print(s, "is feasible", gate_weight[s])
                feasibility_constraints.append(edge_constraint[s])
        opt.add(Sum(feasibility_constraints) >= 1)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])
        # Add function to maximize to the solver

        opt.maximize(Sum(max_func))

        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)

        # ====================================================================================================

        # =========================== Coming up with a penalty for each subgraph =============================
        penalty = Int('penalty')

        output_individual_penalty = []
        penalty_coefficient = 1
        for s in edge_w:
            if gate_weight[s] > feasibility_treshold:
                output_individual_penalty.append(If(gate_literals[s],
                                                    penalty_coefficient * (gate_weight[s] - feasibility_treshold),
                                                    0))
        opt.add(penalty == Sum(output_individual_penalty))
        opt.add_soft(Sum(output_individual_penalty) <= 2 * feasibility_treshold, weight=1)

        # ========================================================

        # opt.add(Sum(max_func) > 1)
        # ======================== Check for multiple subgraphs =======================================
        all_partitions = {}
        count = specs_obj.num_subgraphs
        while count > 0:
            node_partition = []
            pprint.info1(f'Attempt {count}: ', end='')
            c = opt.check()
            if c == sat:
                pprint.success(f"subgraph found -> SAT")
                # print(opt.model())
                m = opt.model()
                # print(f'{m = }')
                for t in m.decls():
                    if 'penalty' in str(t):
                        print(f'{t} = {m[t]}')
                    if 'g' not in str(t):  # Look only the literals associate to the gates
                        continue
                    if is_true(m[t]):
                        gate_id = int(str(t)[2:])
                        node_partition.append(gate_id)  # Gates inside the partition

            else:
                pprint.warning("subgraph not found -> UNSAT")
                count = 0
            # Check partition convexity
            for i in range(len(node_partition) - 1):
                for j in range(i + 1, len(node_partition)):
                    u = node_partition[i]
                    v = node_partition[j]
                    try:
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
                        pass

            # ========================================================================
            if c == sat:
                block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g' in d.name()]
                opt.add(Not(And(block_clause)))
                current_penalty = m[penalty].as_long()
                print(f'{current_penalty}, {node_partition}')
                all_partitions[count] = (current_penalty, node_partition)
            count -= 1
        # ================================================================
        # =======================Pick the Subgraph with the lowest penalty ==============================
        if all_partitions:
            sorted_partitions = dict(
                sorted(
                    all_partitions.items(),
                    key=lambda item: (-len(item[1][1]), item[1][0])
                )
            )

            for par in sorted_partitions:
                print(f'{sorted_partitions[par] = }')
            penalty, node_partition = next(iter(sorted_partitions.values()))
            print(f'{penalty, node_partition}')

        # ================================================================

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

    def find_subgraph_feasible_soft_outputs(self, specs_obj: Specifications):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        imax = specs_obj.imax
        omax = specs_obj.omax
        feasibility_treshold = specs_obj.et

        tmp_graph = self.graph.copy(as_view=False)

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
        partition_output_edges_penalty = []

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
            # print(f'{gate_literals[source] = }')
            # print(f'{tmp_graph.nodes[self.gate_dict[source]][WEIGHT] = }')
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
            if tmp_graph.nodes[self.gate_dict[source]][WEIGHT] > feasibility_treshold:
                this_output_penalty = tmp_graph.nodes[self.gate_dict[source]][WEIGHT] - feasibility_treshold
                partition_output_edges_penalty.append(Or(edge_out_holder) * this_output_penalty)
            # else:
            #     partition_output_edges_penalty.append(Or(edge_out_holder) * IntVal(0))

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

            if tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT] > feasibility_treshold:
                this_output_penalty = tmp_graph.nodes[self.gate_dict[predecessor]][WEIGHT] - feasibility_treshold
                partition_output_edges_penalty.append(e_out * this_output_penalty)
            # else:
            #     partition_output_edges_penalty.append(e_out * IntVal(0))

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

        # Add constraints on the number of input/output edges
        if imax is not None:
            opt.add(Sum(partition_input_edges) <= imax)
        if omax is not None:
            opt.add(Sum(partition_output_edges) <= omax)

        feasibility_constraints = []
        for s in edge_w:
            if gate_weight[s] <= feasibility_treshold and gate_weight[s] != -1:
                # print(s, "is feasible", gate_weight[s])
                feasibility_constraints.append(edge_constraint[s])
        opt.add(Sum(feasibility_constraints) >= 1)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])
        # Add function to maximize to the solver

        opt.maximize(Sum(max_func))

        # =========================== Skipping the nodes that are not labeled ================================
        skipped_nodes = []
        for node in self.graph.nodes:
            if self.graph.nodes[node][WEIGHT] == -1:
                if node.startswith('g'):
                    node_literal = f'{node[0:1]}_{node[1:]}'
                elif node.startswith('in'):
                    node_literal = f'{node[0:2]}_{node[2:]}'
                elif node.startswith('out'):
                    node_literal = f'{node[0:3]}_{node[3:]}'
                else:
                    print(f'Node is neither input, output, nor gate')
                    raise
                skipped_nodes.append(Bool(node_literal))
        skipped_nodes_constraints = [node_literal == False for node_literal in skipped_nodes]
        opt.add(skipped_nodes_constraints)

        # ====================================================================================================

        # =========================== Coming up with a penalty for each subgraph =============================
        penalty_output = Int('penalty_output')
        penalty_gate = Int('penalty_gate')

        output_individual_penalty = []
        penalty_coefficient = 1
        for s in edge_w:
            if gate_weight[s] > feasibility_treshold:
                output_individual_penalty.append(If(gate_literals[s],
                                                    penalty_coefficient * (gate_weight[s] - feasibility_treshold),
                                                    0))

        opt.add(penalty_output == Sum(partition_output_edges_penalty))
        # Why IntVal(1)? => Because sometimes the Sum results into an integer "Python number (e.g., int)", but we need a "Z3 number (e.g., ArithRef)"
        opt.add_soft(IntVal(1) * Sum(partition_output_edges_penalty) <= omax * feasibility_treshold, weight=100)
        opt.add(penalty_gate == Sum(output_individual_penalty))
        opt.add_soft(IntVal(1) * Sum(output_individual_penalty) <= omax * feasibility_treshold, weight=1)

        # ========================================================
        # ======================== Check for multiple subgraphs =======================================
        all_partitions = {}
        count = specs_obj.num_subgraphs
        while count > 0:
            node_partition = []
            pprint.info1(f'Attempt {specs_obj.num_subgraphs - count + 1}: ', end='')
            c = opt.check()
            if c == sat:
                pprint.success(f"subgraph found -> SAT")
                # print(opt.model())
                m = opt.model()
                # print(f'{m = }')
                for t in m.decls():
                    if 'penalty_output' in str(t):
                        # print(f'{t} = {m[t]}')
                        penalty_output = m[t].as_long()
                        pass
                    if 'penalty_gate' in str(t):
                        # print(f'{t} = {m[t]}')
                        penalty_gate = m[t].as_long()
                    if 'g' not in str(t):  # Look only the literals associate to the gates
                        continue
                    if is_true(m[t]):
                        gate_id = int(str(t)[2:])
                        node_partition.append(gate_id)  # Gates inside the partition

            else:
                pprint.warning("subgraph not found -> UNSAT")
                count = 0
            # Check partition convexity
            for i in range(len(node_partition) - 1):
                for j in range(i + 1, len(node_partition)):
                    u = node_partition[i]
                    v = node_partition[j]
                    try:
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
                        pass

            # ========================================================================
            if c == sat:
                block_clause = [d() == True if m[d] else d() == False for d in m.decls() if 'g_' in d.name()]
                opt.add(Not(And(block_clause)))

                all_partitions[count] = (penalty_output, penalty_gate, node_partition)
            count -= 1
        # ================================================================
        # =======================Pick the Subgraph with the lowest penalty ==============================2
        sorted_partitions = {}
        if all_partitions:
            sorted_partitions = dict(
                sorted(
                    all_partitions.items(),
                    key=lambda item: (-len(item[1][2]), item[1][0], item[1][1])
                )
            )

            for par in sorted_partitions:
                print(f'{sorted_partitions[par] = }')

            first_key = next(iter(sorted_partitions))
            penalty_output, penalty_gate, node_partition = sorted_partitions.pop(first_key)

        # ================================================================
        self.subgraph_candidates = sorted_partitions

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
