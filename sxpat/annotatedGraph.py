from typing import Dict, List, Callable
import networkx as nx
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *
from .config.config import *


class AnnotatedGraph(Graph):
    def __init__(self, benchmark_name: str, is_clean: bool = False) -> Graph:
        # Prepare a clean Verilog
        Verilog(benchmark_name)
        # Convert the clean Verilog into a Yosys GV
        convert_verilog_to_gv(benchmark_name)
        super().__init__(benchmark_name, is_clean)

        self.__subgraph = self.extract_subgraph()
        # self.export_annotated_graph()

        self.__subgraph_input_dict = self.input_dict
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


    @property
    def subgraph(self):
        return self.__subgraph

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

    def __repr__(self):
        return f'An object of class SubgraphExtractor:\n' \
               f'{self.name = }\n' \
               f'{self.subgraph_num_inputs = }\n' \
               f'{self.subgraph_num_outputs = }\n' \
               f'{self.subgraph_num_gates = }'

    def extract_subgraph(self):
        # Todo:
        # 1) First, the number of outputs or outgoing edges of the subgraph
        # 2) We might need to consider the labels
        # Potential Fitness function = #of nodes/ (#ofInputs + #ofOutputs)
        tmp_graph = self.graph.copy(as_view=False)
        for gate_idx in self.gate_dict:
            if gate_idx <= 14:
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
        with open(self.out_path, 'w') as f:
            f.write(f"{STRICT} {DIGRAPH} \"{self.name}\" {{\n")
            f.write(f"{NODE} [{STYLE} = {FILLED}, {FILLCOLOR} = {WHITE}]\n")
            for n in self.subgraph.nodes:
                self.export_node(n, f)
            for e in self.subgraph.edges:
                self.export_edge(e, f)
            f.write(f"}}\n")

    # TODO: fix checks!
    # The checks are done on the original graph instead of the annotated graph!
    def export_node(self, n, file_handler: 'class _io.TextIOWrapper'):
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

    def is_subgraph_input(self, n):
        """
        checks whether node n is an input node of the subgraph; an output node is node that has an ingoing edge
        to the subgraph.
        :param n: a node
        :return: True if node n is in the fanout logic, otherwise returns False
        """
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
        return None

    def extract_subgraph_outputs(self):
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

