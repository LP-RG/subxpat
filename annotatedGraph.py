from typing import Dict, List, Callable
from sklearn.cluster import SpectralClustering
import networkx as nx
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *
from .config.config import *
from .config import paths as sxpatpaths
from z3 import *
import time

class AnnotatedGraph(Graph):
    def __init__(self, benchmark_name: str, is_clean: bool = False, partitioning_percentage: int = 50, Imax: int = 3, Omax: int = 2) -> None:
        # Prepare a clean Verilog
        Verilog(benchmark_name)
        # Convert the clean Verilog into a Yosys GV
        convert_verilog_to_gv(benchmark_name)
        super().__init__(benchmark_name, is_clean)

        self.__Imax = Imax
        self.__Omax = Omax
        self.set_output_dict(self.sort_dict(self.output_dict))


        self.__partitioning_percentage = partitioning_percentage


        self.__subgraph = self.extract_subgraph(Imax, Omax)

        self.__subgraph_input_dict = self.extract_subgraph_inputs()
        self.__subgraph_output_dict = self.extract_subgraph_outputs()
        self.__subgraph_gate_dict = self.extract_subgraph_gates()
        self.__subgraph_fanin_dict = self.extract_subgraph_fanin()
        self.__subgraph_fanout_dict = self.extract_subgraph_fanout()
        self.__graph_intact_gate_dict = self.extract_graph_intact_gates()

        self.__subgraph_num_inputs = len(self.subgraph_input_dict)
        self.__subgraph_num_outputs = len(self.subgraph_output_dict)
        self.__subgraph_num_gates = len(self.subgraph_gate_dict)
        self.__subgraph_num_fanin = len(self.subgraph_fanin_dict)
        self.__subgraph_num_fanout = len(self.subgraph_fanout_dict)
        self.__graph_num_intact_gates = len(self.__graph_intact_gate_dict)

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

    @property
    def subgraph_out_path(self):
        return self.__out_annotated_graph_path

    @property
    def subgraph_input_dict(self):
        return self.__subgraph_input_dict

    @property
    def subgraph_output_dict(self):
        return self.__subgraph_output_dict

    @property
    def subgraph_gate_dict(self):
        return self.__subgraph_gate_dict

    @property
    def graph_intact_gate_dict(self):
        return self.__graph_intact_gate_dict

    @property
    def subgraph_fanin_dict(self):
        return self.__subgraph_fanin_dict

    @property
    def subgraph_fanout_dict(self):
        return self.__subgraph_fanout_dict

    @property
    def subgraph_num_inputs(self):
        return self.__subgraph_num_inputs

    @property
    def subgraph_num_outputs(self):
        return self.__subgraph_num_outputs

    @property
    def subgraph_num_gates(self):
        return self.__subgraph_num_gates

    @property
    def subgraph_num_fanin(self):
        return self.__subgraph_num_fanin

    @property
    def subgraph_num_fanout(self):
        return self.__subgraph_num_fanout

    def sort_dict(self, this_dict: Dict) -> Dict:
        sorted_dict: type(this_dict) = {}

        for i in range(len(this_dict)):
            sorted_dict[i] = this_dict[i]

        return sorted_dict






    def __repr__(self):
        return f'An object of class AnnotatedGraph:\n' \
               f'{self.name = }\n' \
               f'{self.subgraph_num_inputs = }\n' \
               f'{self.subgraph_num_outputs = }\n' \
               f'{self.subgraph_num_gates = }\n' \
               f'{self.partitioning_percentage = }\n'

    def extract_subgraph(self, I_max, O_max):
        """
        extracts a colored subgraph from the original non-partitioned graph object
        :return: an annotated graph in which the extracted subgraph is colored
        """
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # 2) We might need to consider the labels
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        print("")
        print("----------------- Start Subgraph Extraction -----------------\n\n")
        tmp_graph = self.graph.copy(as_view=False)

        # Data structures containing the literals
        input_literals = {}                     # literals associated to the input nodes
        gate_literals = {}                      # literals associated to the gates in the circuit
        output_literals = {}                    # literals associated to the input nodes

        # Data structures containing the edges 
        input_edges = {}                        # key = input node id, value = array of id. Contains id of gates in the circuit connected with the input node (childs)
        gate_edges = {}                         # key = gate id, value = array of id. Contains the successors gate (childs)
        output_edges = {}                       # key = output node id, value = array of id. Contains id of gates in the circuit connected with the output node (parents)

        # Optimizer
        opt = Optimize()

        # Function to maximize
        max_func = []

        # List of all the partition edges
        partition_input_edges = []              # list of all the input edges ([S'D_1 + S'D_2 + ..., ...])
        partition_output_edges = []             # list of all the output edges ([S_1D' + S_2D' + ..., ...])

        # Input and Output constraints (TODO: make those arguments of the function?)
        #I_max = 3
        #O_max = 3

        # Generate all literals
        for e in tmp_graph.edges:
            if 'in' in e[0]:                    # Generate literal for each input node
                in_id = int(e[0][2:])
                if in_id not in input_literals:
                    input_literals[in_id] = Bool("in_%s" % str(in_id))
            if 'g' in e[0]:                     # Generate literal for each gate in the circuit
                g_id = int(e[0][1:])
                if g_id not in gate_literals:
                    gate_literals[g_id] = Bool("g_%s" % str(g_id))
            
            if 'out' in e[1]:                   # Generate literal for each output node
                out_id = int(e[1][3:])
                if out_id not in output_literals:
                    output_literals[out_id] = Bool("out_%s" % str(out_id))
        
        # Populate data structures containing all the edges
        for e in tmp_graph.edges:
            if 'in' in e[0]:                    # Populate input_edges structure
                in_id = int(e[0][2:])
                if in_id not in input_edges:
                    input_edges[in_id] = []
                input_edges[in_id].append(int(e[1][1:]))

            if 'g' in e[0] and 'g' in e[1]:     # Populate gate_edges structure
                ns_id = int(e[0][1:])
                nd_id = int(e[1][1:])
                
                if ns_id not in gate_edges:       
                    gate_edges[ns_id] = []
                gate_edges[ns_id].append(nd_id)

            if 'out' in e[1]:                   # Populate output_edges structure
                out_id = int(e[1][3:])
                if out_id not in output_edges:
                    output_edges[out_id] = []
                output_edges[out_id].append(int(e[0][1:]))


        #print("Number of input nodes: ", len(input_literals))
        #print("Number of gates in the circuit: ", len(gate_literals))
        #print("Number of output nodes: ", len(output_literals))
            
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
            predecessor = output_edges[output_id][0]    # Output nodes have only one predecessor  
            e_out = And(gate_literals[predecessor],Not(output_literals[output_id]))

            partition_output_edges.append(e_out)

        # Create graph of the cicuit without input and output nodes
        G = nx.DiGraph()

        for e in tmp_graph.edges:
            if 'g' in str(e[0]) and 'g' in str(e[1]):
                source = int(e[0][1:])
                destination = int(e[1][1:])

                G.add_edge(source, destination)

        descendants = {}
        ancestors = {}
        for n in G:
            if n not in descendants:
                descendants[n] = list(nx.descendants(G,n))
            if n not in ancestors:
                ancestors[n] = list(nx.ancestors(G,n))

        # Generate convexity constraints
        for source in gate_edges:
            for destination in gate_edges[source]:
                if len(descendants[destination]) > 0:       # Constraints on output edges
                    not_descendants = [Not(gate_literals[l]) for l in descendants[destination]]
                    not_descendants.append(Not(gate_literals[destination]))
                    descendat_condition = Implies(And(gate_literals[source], Not(gate_literals[destination])), And(not_descendants))
                    opt.add(descendat_condition)
                if len(ancestors[source]) > 0:              # Constraints on input edges
                    not_ancestors = [Not(gate_literals[l]) for l in ancestors[source]]
                    not_ancestors.append(Not(gate_literals[source]))
                    ancestor_condition = Implies(And(Not(gate_literals[source]), gate_literals[destination]), And(not_ancestors))
                    opt.add(ancestor_condition)            
        
        # Set input nodes to False
        for input_node_id in input_literals:
            opt.add(input_literals[input_node_id] == False)

        # Set output nodes to False
        for output_node_id in output_literals:
            opt.add(output_literals[output_node_id] == False)

        # Add constraints on the number of input/output edges
        opt.add(Sum(partition_input_edges)  <= I_max)
        opt.add(Sum(partition_output_edges) <= O_max)

        # Generate function to maximize
        for gate_id in gate_literals:
            max_func.append(gate_literals[gate_id])

        # Add function to maximize to the solver
        opt.maximize(Sum(max_func))

        node_partition = []
        start = time.time()
        if opt.check() == sat:
            print("Subgraph found")
            print(opt)
            m = opt.model()
            for t in m.decls():
                if 'g' not in str(t):                   # Look only the literals associate to the gates
                    continue
                if is_true(m[t]):
                    gate_id = int(str(t)[2:])
                    node_partition.append(gate_id)      # Gates inside the partition
            print("Nodes in subgraph", len(node_partition), " out of ", len(G.nodes))
        else:
            print("Subgraph not found")
            
        end = time.time()
        print("Time: ", end - start)
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
                        #exit(0)

                except nx.exception.NetworkXNoPath:
                    # No path between u and v

                    #print("No path", u, v)
                    pass

        print("\n\n----------------- End Subgraph Extraction -----------------\n\n\n")
        #exit(0)
        # Assign different color to gates in the partition
        for gate_idx in self.gate_dict:
            if gate_idx in node_partition:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 1
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = RED
            else:
                tmp_graph.nodes[self.gate_dict[gate_idx]][SUBGRAPH] = 0
                tmp_graph.nodes[self.gate_dict[gate_idx]][COLOR] = WHITE
        return tmp_graph

    def export_annotated_graph(self):
        """
        exports the subgraph (annotated graph) to a GV (GraphViz) file
        :return:
        """
        with open(self.subgraph_out_path, 'w') as f:
            f.write(f"{STRICT} {DIGRAPH} \"{self.name}\" {{\n")
            f.write(f"{NODE} [{STYLE} = {FILLED}, {FILLCOLOR} = {WHITE}]\n")
            for n in self.subgraph.nodes:
                self.export_node(n, f)
            for e in self.subgraph.edges:
                self.export_edge(e, f)
            f.write(f"}}\n")
        folder, extension = OUTPUT_PATH[GV]
        subprocess.run(f'dot -Tpng {self.subgraph_out_path} > {folder}/{self.name}_subgraph_Imax_{self.__Imax}_Omax_{self.__Omax}.png', shell=True)


    # TODO: fix checks!
    # The checks are done on the original graph instead of the annotated graph!
    def export_node(self, n, file_handler: 'class _io.TextIOWrapper'):
        """
        exports node n as a line of file that is identified by file_hanlder
        :param n: the label of node n
        :param file_handler: the file object
        :return: nothing
        """
        if self.is_cleaned_pi(n) or self.is_cleaned_po(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            elif COLOR in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            line = f"{n} [{label}, {shape}, {color}];\n"
        elif self.is_cleaned_gate(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            line = f"{n} [{label}, {shape}, {color}];\n"
        elif self.is_cleaned_constant(n):
            label = f"{LABEL}=\"{self.subgraph.nodes[n][LABEL]}\\n{n}\""
            if SUBGRAPH in self.subgraph.nodes[n]:
                color = f"{COLOR}={self.subgraph.nodes[n][COLOR]}"
            else:
                color = f"{COLOR}={WHITE}"
            shape = f"{SHAPE}={self.subgraph.nodes[n][SHAPE]}"
            line = f"{n} [{label}, {shape}, {color}];\n"
        else:
            print('ERROR!!! found a node that is not a PI, PO, WIRE, CONSTANT, GATE')
            exit()
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

    #TODO
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


