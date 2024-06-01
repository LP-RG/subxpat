from typing import List, Dict, Optional, Tuple, AnyStr

import json
import re
import subprocess
from subprocess import PIPE
import os
import math
import itertools

from Z3Log.graph import Graph
from Z3Log.config.config import *
from Z3Log.config.path import *

from z_marco.ma_graph import MaGraph
from z_marco.utils import pprint, color

from .annotatedGraph import AnnotatedGraph
from .config import paths as sxpatpaths
from .config import config as sxpatconfig
from .templateSpecs import TemplateSpecs


class Synthesis:
    # TODO:
    # we assign wires to both inputs and outputs of an annotated subgraph
    # follow, inputs, red, white, outputs notation in the Verilog generation
    def __init__(self, template_specs: TemplateSpecs, graph_obj: AnnotatedGraph = None, json_obj: List[Dict] = None, magraph: MaGraph = None):
        self.__benchmark_name = template_specs.benchmark_name
        self.__exact_benchmark_name = template_specs.exact_benchmark
        self.__template_name = template_specs.template_name

        self.__subxpat: bool = template_specs.subxpat
        self.__shared: bool = template_specs.shared
        self.__lut: bool = template_specs.lut
        self.__lut_MP: bool = template_specs.lut_MP

        self.__iterations = template_specs.iterations
        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__selectors_per_output = template_specs.selectors_per_output
        self.__error_threshold = template_specs.et
        self.__graph: AnnotatedGraph = graph_obj
        self.__magraph: Optional[MaGraph] = magraph
        self.__partitioning_percentage = template_specs.partitioning_percentage
        self.__num_models: int = template_specs.num_of_models
        print(f'{self.__num_models = }')

        if self.shared:
            self.__products_in_total: int = template_specs.products_in_total
        else:
            self.__products_in_total: float = float('inf')

        if json_obj == sxpatconfig.UNSAT or json_obj == sxpatconfig.UNKNOWN:
            pprint.error('ERROR!!! the json does not contain any models!')
        else:
            self.__json_model: json = json_obj
            self.__num_models = self.get_num_models_from_json(json_obj)

            self.__use_json_model: bool = None
            self.__use_graph: bool = None

            folder, extension = sxpatpaths.OUTPUT_PATH[sxpatconfig.JSON]
            self.__json_in_path: str = None
            folder, extension = OUTPUT_PATH[sxpatconfig.GV]
            self.__graph_in_path: str = None

            self.__ver_out_name: str = None
            self.__ver_out_path: str = self.set_path(OUTPUT_PATH['ver'])

            self.__verilog_string: List[str] = self.convert_to_verilog()

    @property
    def products_in_total(self):
        return self.__products_in_total

    @property
    def pit(self):
        return self.__products_in_total

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def shared(self):
        return self.__shared
    @property
    def lut(self):
        return self.__lut
    @property
    def lut_MP(self):
        return self.__lut_MP
    @property
    def num_of_models(self):
        return self.__num_models

    @property
    def products_in_total(self):
        return self.__products_in_total

    @property
    def pit(self):
        return self.__products_in_total

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def shared(self):
        return self.__shared

    @property
    def num_of_models(self):
        return self.__num_models

    @property
    def benchmark_name(self):
        return self.__benchmark_name

    @benchmark_name.setter
    def benchmark_name(self, this_name):
        self.__benchmark_name = this_name

    @property
    def exact_name(self):
        return self.__exact_benchmark_name

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iteration: int):
        self.__iterations = this_iteration

    @property
    def graph(self):
        return self.__graph

    @property
    def json_model(self):
        return self.__json_model

    @property
    def literals_per_product(self):
        return self.__literal_per_product

    @property
    def lpp(self):
        return self.__literal_per_product

    @property
    def products_per_output(self):
        return self.__product_per_output

    @property
    def ppo(self):
        return self.__product_per_output

    @property
    def selectors_per_output(self):
        return self.__selectors_per_output

    @property
    def spo(self):
        return self.__selectors_per_output

    @property
    def template_name(self):
        return self.__template_name

    @property
    def error_threshold(self):
        return self.__error_threshold

    @property
    def et(self):
        return self.__error_threshold

    @property
    def use_json_model(self):
        return self.__use_json_model

    @use_json_model.setter
    def use_json_model(self, use_json_model: bool):
        self.__use_json_model = use_json_model

    @property
    def use_graph(self):
        return self.__use_graph

    @use_graph.setter
    def use_graph(self, use_graph: bool):
        self.__use_graph = use_graph

    @property
    def ver_out_name(self):
        return self.__ver_out_name

    @ver_out_name.setter
    def ver_out_name(self, this_name):
        self.__ver_out_name = this_name

    @property
    def ver_out_path(self):
        return self.__ver_out_path

    @ver_out_path.setter
    def ver_out_path(self, this_path: str):
        self.__ver_out_path = this_path

    @property
    def verilog_string(self):
        return self.__verilog_string

    @verilog_string.setter
    def verilog_string(self, this_verilog_string):
        self.__verilog_string = this_verilog_string

    def get_num_models_from_json(self, json_obj: List[Dict]):
        # todo:refactor
        # return sum(1 for i in range(len(json_obj)) if json_obj[i])

        num_models = 0
        for idx in range(len(json_obj)):
            if json_obj[idx]:
                num_models += 1

        return num_models

    def set_path(self, this_path: Tuple[str, str] = None, this_name: str = None, id: int = 0):
        folder, extenstion = this_path

        if this_name:
            self.ver_out_name = this_name

        elif re.search('id(\d+)', self.benchmark_name):
            self.ver_out_name = f'{self.benchmark_name}_{id}.{extenstion}'

        elif self.num_of_models == 1:
            self.ver_out_name = f'{self.exact_name}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_id0.{extenstion}'

        elif self.num_of_models > 1:
            self.ver_out_name = f'{self.exact_name}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_id{id}.{extenstion}'

        self.ver_out_path = f'{folder}/{self.ver_out_name}'
        return self.ver_out_path

    def convert_to_verilog(self):
        """
        converts the graph and/or the json model into a Verilog string
        :param use_graph: if set to true, the graph is used
        :param use_json_model: if set to true, the json model is used
        :return: a Verilog description in the form of a String object
        """
        if self.__magraph:
            # todo:hack: temporary
            verilog_str = [self.__magraph_to_verilog()]
        elif self.subxpat and self.shared:
            verilog_str = self.__annotated_graph_to_verilog_shared()  # Shared SubXPAT
        elif self.lut:
            verilog_str = self.__json_model_to_verilog_lut()
        elif self.lut_MP:
            verilog_str = self.__json_model_to_verilog_lut_MP()
        elif self.subxpat and not self.shared:
            verilog_str = self.__annotated_graph_to_verilog()  # SubXPAT
        elif not self.subxpat and self.shared:
            verilog_str = self.__json_model_to_verilog_shared()  # Shared XPAT
        elif not self.subxpat and not self.shared:
            verilog_str = self.__annotated_graph_to_verilog()  # XPAT (Vanilla)
            #TODO: Mohamed, please put your own synthesis funciton here! with the correct flags!
            # which means, whenever we choose subxpat and lut (create this one if it does not exist)
            # you should run this function right here!
            pass
        else:
            pprint.error('ERROR!!! the graph or json model cannot be converted into a Verilog script!')
            exit(1)

        return verilog_str

    def __json_input_wire_declarations(self, idx: int = 0):
        graph_input_list = list(self.graph.subgraph_input_dict.values())

        input_wire_list = f'//json input wires\n'
        input_wire_list += f'{sxpatconfig.VER_WIRE} '
        wires = f''
        for idx in range(self.graph.subgraph_num_inputs):
            if idx == self.graph.subgraph_num_inputs - 1:
                wires += f'{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{idx};\n'
            else:
                wires += f'{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{idx}, '
        if wires:
            return input_wire_list + wires
        else:
            return '// no json wires!\n'

    def __json_model_wire_declarations(self):
        wire_list = f'//json model\n'

        if self.ppo > 0 and self.graph.subgraph_num_outputs:
            wire_list += f'wire '
            for o_idx in range(self.graph.subgraph_num_outputs):
                for ppo_idx in range(self.ppo):
                    wire_list += f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}'
                    if ppo_idx == self.ppo - 1 and o_idx == self.graph.subgraph_num_outputs - 1:
                        wire_list += ';\n'
                    else:
                        wire_list += ', '
        else:
            wire_list += f'// No wires detected!'
        return wire_list

    def __get_fanin_cone(self, n: str, visited: List[str] = []):
        visited.append(n)
        assignment = f''
        succ_n_list = list(self.graph.graph.predecessors(n))
        for s_n in succ_n_list:
            if s_n in self.graph.input_dict.values():
                pass
            else:
                if s_n not in visited:
                    assignment += self.__get_fanin_cone(s_n, visited)

        if len(succ_n_list) == 2:
            gate_1 = f'{sxpatconfig.VER_WIRE_PREFIX}{succ_n_list[0]}' if succ_n_list[
                0] not in self.graph.input_dict.values() else \
                succ_n_list[0]
            gate_2 = f'{sxpatconfig.VER_WIRE_PREFIX}{succ_n_list[1]}' if succ_n_list[
                1] not in self.graph.input_dict.values() else \
                succ_n_list[1]
            if self.graph.graph.nodes[n][LABEL] == sxpatconfig.AND:
                operator = sxpatconfig.VER_AND
            elif self.graph.graph.nodes[n][LABEL] == sxpatconfig.OR:
                operator = sxpatconfig.VER_OR

            assignment += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = " \
                          f"{gate_1} {operator} {gate_2};\n"
        else:
            gate_1 = f'{sxpatconfig.VER_WIRE_PREFIX}{succ_n_list[0]}' if succ_n_list[
                0] not in self.graph.input_dict.values() else \
                succ_n_list[0]
            assignment += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = ~{gate_1};\n"
        return assignment

    def __subgraph_inputs_assigns(self):
        s_inputs_assigns = f'//subgraph inputs assigns\n'

        for n in self.graph.subgraph_input_dict.values():
            if n in self.graph.input_dict.values():
                s_inputs_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {n};\n'
            else:
                s_inputs_assigns += self.__get_fanin_cone(n)
        return s_inputs_assigns

    def __subgraph_inputs_assigns_shared(self):
        s_inputs_assigns = f'//subgraph inputs assigns\n'

        for n in self.graph.subgraph_input_dict.values():
            if n in self.graph.input_dict.values():
                s_inputs_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {n};\n'
            else:
                s_inputs_assigns += self.__get_fanin_cone(n)
        return s_inputs_assigns

    def __fix_order(self):
        subpgraph_input_list = list(self.graph.subgraph_input_dict.values())
        subpgraph_input_list_ordered = []
        pi_list = []
        g_list = []

        for node in subpgraph_input_list:
            if re.search('in(\d+)', node):
                idx = int(re.search('in(\d+)', node).group(1))
                pi_list.append(node)
            else:
                g_list.append(node)

        # note:marco: bug found, was sorting by string and not by int
        pi_list.sort(key=lambda x: int(re.search('\d+', x).group()))
        for el in pi_list:
            subpgraph_input_list_ordered.append(el)
        for el in g_list:
            subpgraph_input_list_ordered.append(el)
        return subpgraph_input_list_ordered

    def __subgraph_to_json_input_mapping(self):
        sub_to_json = f'//mapping subgraph inputs to json inputs\n'

        subgraph_input_list = list(self.graph.subgraph_input_dict.values())
        subgraph_input_list = self.__fix_order()
        # print(f'{subgraph_input_list = }')

        for idx in range(self.graph.subgraph_num_inputs):
            sub_to_json += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{idx} = ' \
                           f'{sxpatconfig.VER_WIRE_PREFIX}{subgraph_input_list[idx]};\n'

        return sub_to_json

    def __json_model_lpp_and_subgraph_output_assigns(self, idx: int = 0):
        lpp_assigns = f'//json model assigns (approximated/XPATed part)\n'
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())

        lpp_assigns += f''
        for o_idx in range(self.graph.subgraph_num_outputs):
            p_o = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}'

            if self.json_model[idx][p_o]:
                # p_o0_t0, p_o0_t1
                included_products = []
                for ppo_idx in range(self.ppo):
                    included_products.append(f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}')

                for ppo_idx in range(self.ppo):
                    included_literals = []
                    for input_idx in range(self.graph.subgraph_num_inputs):
                        p_s = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                        p_l = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'
                        if self.json_model[idx][p_s]:
                            if self.json_model[idx][p_l]:
                                included_literals.append(
                                    f'{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')
                            else:
                                included_literals.append(
                                    f'{sxpatconfig.VER_NOT}{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')

                    if included_literals:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = ' \
                                       f"{' & '.join(included_literals)};\n"
                    else:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = 1;\n'

                lpp_assigns += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = {' | '.join(included_products)};\n"
            else:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = 0;\n'

        # print(f'{lpp_assigns = }')

        return lpp_assigns

    def __intact_part_assigns(self):
        intact_part = f'// intact gates assigns\n'
        for n_idx in self.graph.constant_dict.keys():
            n = self.graph.constant_dict[n_idx]

            sn = list(self.graph.graph.successors(n))
            Value = self.graph.graph.nodes[n][LABEL]

            if Value.upper() == 'FALSE':
                Value = "1'b0"
            else:
                Value = "1'b1"

            intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {Value};\n'

        for n_idx in self.graph.graph_intact_gate_dict.keys():
            n = self.graph.graph_intact_gate_dict[n_idx]
            pn = list(self.graph.graph.predecessors(n))
            gate = self.graph.graph.nodes[n][LABEL]
            for idx, el in enumerate(pn):
                if (
                    (el in list(self.graph.input_dict.values()) and el not in list(self.graph.subgraph_input_dict.values()))
                    or (el in list(self.graph.output_dict.values()))
                ):
                    pass
                else:
                    pn[idx] = f'{sxpatconfig.VER_WIRE_PREFIX}{el}'

            # print(f'{pn = }')

            if len(pn) == 1:
                intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {sxpatconfig.VER_NOT}{pn[0]};\n'
            elif len(pn) == 2:
                if gate == sxpatconfig.AND:

                    intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = ' \
                                   f'{pn[0]} {sxpatconfig.VER_AND} ' \
                                   f'{pn[1]};\n'
                elif gate == sxpatconfig.OR:
                    intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = ' \
                                   f'{pn[0]} {sxpatconfig.VER_OR} ' \
                                   f'{pn[1]};\n'
            else:
                pprint.error(f'ERROR!!! node {n} has more than two drivers!')
                exit()

        return intact_part

    def __output_assigns(self):
        output_assigns = f'// output assigns\n'

        for n in self.graph.output_dict.values():
            pn = list(self.graph.graph.predecessors(n))
            gate = self.graph.graph.nodes[n][LABEL]

            if len(pn) == 1:
                if gate == sxpatconfig.NOT:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN} {n} = {sxpatconfig.VER_NOT}{sxpatconfig.VER_WIRE_PREFIX}{pn[0]};\n'
                else:
                    # print(f'{pn = }')
                    if pn[0] in list(self.graph.input_dict.values()) and pn[0] not in list(self.graph.subgraph_input_dict.values()):
                        # print(f'We are here=============')
                        output_assigns += f'{sxpatconfig.VER_ASSIGN} {n} = {pn[0]};\n'
                    else:
                        output_assigns += f'{sxpatconfig.VER_ASSIGN} {n} = {sxpatconfig.VER_WIRE_PREFIX}{pn[0]};\n'
            elif len(pn) == 2:
                if gate == sxpatconfig.AND:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN}  = ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_AND} ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'
                elif gate == sxpatconfig.OR:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN}  = ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_OR} ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'

        output_assigns += f'{sxpatconfig.VER_ENDMODULE}'
        return output_assigns

    def __intact_gate_wires(self):
        intact_gate_list = list(self.graph.graph_intact_gate_dict.values())
        constant_intact_gate_list = list(self.graph.constant_dict.values())
        non_input_intact_gate_list = []

        for gate in intact_gate_list:
            if not self.graph.is_subgraph_input(gate):
                non_input_intact_gate_list.append(gate)

        intact_gate_variable_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in non_input_intact_gate_list]

        intact_wires = f'//intact gates wires \n'
        if len(non_input_intact_gate_list) > 0:
            intact_wires += f"wire "
            for gate_idx, gate in enumerate(non_input_intact_gate_list):
                if not self.graph.is_subgraph_input(gate):
                    if gate_idx < len(non_input_intact_gate_list) - 1:
                        intact_wires += f"{intact_gate_variable_list[gate_idx]}, "
                    else:
                        intact_wires += f"{intact_gate_variable_list[gate_idx]};\n"
        else:
            intact_wires += f'{TAB}//no intact gates detected!\n'
        if len(constant_intact_gate_list) > 0:
            intact_wires += f'{sxpatconfig.VER_WIRE} '
            for gate_idx, gate in enumerate(constant_intact_gate_list):
                if gate_idx == len(constant_intact_gate_list) - 1:
                    intact_wires += f'{sxpatconfig.VER_WIRE_PREFIX}{gate};'
                else:
                    intact_wires += f'{sxpatconfig.VER_WIRE_PREFIX}{gate}, '

        return intact_wires

    def __get_module_signature(self, idx: int = 0):
        input_list = list(self.graph.input_dict.values())

        # note:marco: bug found, was sorting by string and not by int
        input_list.sort(key=lambda x: int(re.search('\d+', x).group()))
        # input_list.sort(key=lambda x: re.search('\d+', x).group())

        output_list = list(self.graph.output_dict.values())
        # Sort Dictionary

        module_name = self.ver_out_name[:-2]
        module_signature = f"{sxpatconfig.VER_MODULE} {module_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"

        return module_signature

    def __declare_inputs_outputs(self):
        input_list = list(self.graph.input_dict.values())
        # note:marco: bug found, was sorting by string and not by int
        input_list.sort(key=lambda x: int(re.search('\d+', x).group()))
        # input_list.sort(key=lambda x: re.search('\d+', x).group())
        # input_list.reverse()
        # print(f'{input_list = }')

        output_list = list(self.graph.output_dict.values())
        input_declarations = f"//input/output declarations\n"
        input_declarations += f"{sxpatconfig.VER_INPUT} {', '.join(input_list)};\n"
        output_declarations = f"{sxpatconfig.VER_OUTPUT} {', '.join(output_list)};\n"
        
        return input_declarations + output_declarations

    def __get_subgraph_input_wires(self):
        annotated_graph_input_list = list(self.graph.subgraph_input_dict.values())
        annotated_graph_input_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_input_list]
        annotated_graph_input_wires = f"//annotated subgraph inputs\n"
        if len(annotated_graph_input_list) != 0:
            annotated_graph_input_wires += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_input_list)};\n"
        return annotated_graph_input_wires

    def __get_subgraph_output_wires(self):
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        annotated_graph_output_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_output_list]
        annotated_graph_output_wires = f"//annotated subgraph outputs\n"
        if len(annotated_graph_output_list) != 0:
            annotated_graph_output_wires += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_output_list)};\n"
        return annotated_graph_output_wires

    def sort_list(self, this_list: List[str]) -> List[str]:
        sorted_list: List[str] = ['-1'] * len(this_list)
        for idx, el in enumerate(this_list):
            if re.search("(in|out)(\d+)", el):
                match = re.search("(in|out)(\d+)", el)
                signal_idx = int(match.group(2))
                sorted_list[signal_idx] = el
            else:
                raise Exception(f'The names are not correct in this array {this_list}')
        return sorted_list

    def __json_model_input_declaration_shared(self):

        annotated_graph_input_list = list(self.graph.input_dict.values())

        annotated_graph_input_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_input_list]

        json_model_inputs = f"// JSON model input\n"
        json_model_inputs += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_input_list)};\n"

        return json_model_inputs

    def __json_model_output_declaration_subxpat_shared(self):

        annotated_graph_output_list = list(self.graph.output_dict.values())
        annotated_graph_output_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_output_list]

        json_model_outputs = f"// JSON model output\n"
        json_model_outputs += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_output_list)};\n"

        return json_model_outputs

    def __json_model_output_declaration_shared(self):

        annotated_graph_output_list = list(self.graph.output_dict.values())
        annotated_graph_output_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_output_list]

        json_model_outputs = f"// JSON model output\n"
        json_model_outputs += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_output_list)};\n"

        return json_model_outputs

    def __json_model_wire_declarations_shared(self):
        wire_list = f'//json model\n'
        wire_list += f'wire '
        for n in self.graph.output_dict.values():
            pn = list(self.graph.graph.predecessors(n))  # g17
            wire_list += f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX}'
            if n == self.graph.num_outputs - 1:
                wire_list += ';\n'
            else:
                wire_list += ', '

        for out_idx in range(self.graph.num_outputs):
            for pit_idx in range(self.pit):
                wire_list += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{out_idx}'
                if pit_idx == self.pit - 1 and n == self.graph.num_outputs - 1:
                    wire_list += ';\n'
                else:
                    wire_list += ', '
        for pit_idx in range(self.pit):
            wire_list += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}'
            if pit_idx == self.pit - 1:
                wire_list += ';\n'
            else:
                wire_list += ', '

        return wire_list

    def __json_input_assigns(self):
        annotated_graph_input_list = list(self.graph.input_dict.values())

        json_model_inputs = f"// JSON model input assign\n"
        for item in annotated_graph_input_list:
            json_model_inputs += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{item} = {item};\n"

        return json_model_inputs

    def __json_model_lpp_product_assigns_subxpat_shared(self, idx: int = 0):

        lpp_assigns = f'\n'
        lpp_assigns += f'//json model assigns (approximated Shared/XPAT part)\n'
        lpp_assigns += f'//assign literals to products\n'
        o_idx = self.graph.subgraph_num_outputs
        included_products = []

        for pit_idx in range(self.pit):
            included_products.append(
                f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}')

            included_literals = []
            for input_idx in range(self.graph.subgraph_num_inputs):
                p_s = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                p_l = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'

                if self.json_model[idx][p_s]:
                    if self.json_model[idx][p_l]:
                        included_literals.append(
                            f'{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')
                    else:
                        included_literals.append(
                            f'{sxpatconfig.VER_NOT}{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')
            if included_literals:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} = ' \
                               f"{' & '.join(included_literals)};\n"
            else:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} = 1;\n'

        return lpp_assigns

    def __json_model_lpp_product_assigns_shared(self, idx: int = 0):

        lpp_assigns = f'\n'
        lpp_assigns += f'//json model assigns (approximated Shared/XPAT part)\n'
        lpp_assigns += f'//assign literals to products\n'
        o_idx = self.graph.subgraph_num_outputs
        included_products = []

        for pit_idx in range(self.pit):
            included_products.append(
                f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}')

            included_literals = []
            for input_idx in range(self.graph.num_inputs):
                p_s = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                p_l = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'

                if self.json_model[idx][p_s]:
                    if self.json_model[idx][p_l]:
                        included_literals.append(
                            f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')
                    else:
                        included_literals.append(
                            f'{sxpatconfig.VER_NOT}{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{input_idx}')
            if included_literals:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} = ' \
                               f"{' & '.join(included_literals)};\n"
            else:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} = 1;\n'

        return lpp_assigns

    def __shared_logic_assigns_subxpat_shared(self, idx=0):

        shared_assigns = f'//if a product has literals and if the product is being "activated" for that output'
        shared_assigns += f'\n'
        for o_idx in range(self.graph.subgraph_num_outputs):

            for pit_idx in range(self.pit):
                json_output = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}'
                shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx} = '
                shared_assigns += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} '
                if self.json_model[idx][json_output]:
                    shared_assigns += f'{sxpatconfig.VER_AND} 1'
                else:
                    shared_assigns += f'{sxpatconfig.VER_AND} 0'
                shared_assigns += ';\n'

        shared_assigns += f'//compose an output with corresponding products (OR)'
        shared_assigns += f'\n'
        # assign OR products in output
        # Morteza added! fixing the correspondence between the graph outputs and the primary outputs ===================
        # mapping template outputs to primary outputs
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        primary_output_list = list(self.graph.subgraph_output_dict.values())
        sorted_annotated_graph_output_list = [-1] * len(annotated_graph_output_list)
        for node_idx in range(len(annotated_graph_output_list)):
            this_node = annotated_graph_output_list[node_idx]
            for key in self.graph.subgraph_output_dict.keys():
                if primary_output_list[node_idx] == self.graph.subgraph_output_dict[key]:
                    sorted_annotated_graph_output_list[key] = this_node
                    break

        # ==============================================================================================================

        output_quantity = 0
        # print(Fore.LIGHTCYAN_EX + f'{sorted_annotated_graph_output_list}' + Style.RESET_ALL)
        for o_idx, item in enumerate(sorted_annotated_graph_output_list):

            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.OUT}{o_idx} = '
            pit_quantity = self.pit
            for pit_idx in range(self.pit):
                shared_assigns += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{output_quantity}'
                if pit_quantity == 1:
                    shared_assigns += ';\n'
                else:
                    shared_assigns += f' {sxpatconfig.VER_OR} '
                pit_quantity -= 1
            output_quantity += 1

        shared_assigns += f'//if an output has products and if it is part of the JSON model'
        shared_assigns += f'\n'

        for o_idx, item in enumerate(sorted_annotated_graph_output_list):
            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{item} =  {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.OUT}{o_idx} {sxpatconfig.VER_AND} '
            json_output_p_o = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}'
            # print(f'{self.json_model[idx] = }')
            if self.json_model[idx][json_output_p_o]:
                shared_assigns += f'1'
            else:
                shared_assigns += f'0'
            shared_assigns += ';\n'

        # for key in self.graph.subgraph_output_dict.keys():
        #     n = self.graph.subgraph_output_dict[key]
        #     pn = list(self.graph.graph.predecessors(n))
        #
        #     shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX} = {sxpatconfig.VER_WIRE_PREFIX}{n} {sxpatconfig.VER_AND} '
        #     json_output_p_o = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{key}'
        #     o_idx += 1
        #     if self.json_model[idx][json_output_p_o]:
        #         shared_assigns += f'1'
        #     else:
        #         shared_assigns += f'0'
        #     shared_assigns += ';\n'

        return shared_assigns

    def __shared_logic_assigns(self, idx=0):

        shared_assigns = f'//if a product has literals and if the product is being "activated" for that output'
        shared_assigns += f'\n'
        for o_idx in range(self.graph.num_outputs):

            for pit_idx in range(self.pit):
                json_output = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}'
                shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx} = '
                shared_assigns += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} '
                if self.json_model[idx][json_output]:
                    shared_assigns += f'{sxpatconfig.VER_AND} 1'
                else:
                    shared_assigns += f'{sxpatconfig.VER_AND} 0'
                shared_assigns += ';\n'

        shared_assigns += f'//compose an output with corresponding products (OR)'
        shared_assigns += f'\n'
        # assign OR products in output
        # Morteza added! fixing the correspondence between the graph outputs and the primary outputs ===================
        # mapping template outputs to primary outputs
        annotated_graph_output_list = list(self.graph.output_dict.values())
        primary_output_list = list(self.graph.output_dict.values())
        sorted_annotated_graph_output_list = [-1] * len(annotated_graph_output_list)
        for node_idx in range(len(annotated_graph_output_list)):
            this_node = annotated_graph_output_list[node_idx]
            for key in self.graph.output_dict.keys():
                if primary_output_list[node_idx] == self.graph.output_dict[key]:
                    sorted_annotated_graph_output_list[key] = this_node
                    break

        # ==============================================================================================================

        output_quantity = 0
        # print(f'')
        for item in sorted_annotated_graph_output_list:
            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{item} = '
            pit_quantity = self.pit
            for pit_idx in range(self.pit):
                shared_assigns += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{output_quantity}'
                if pit_quantity == 1:
                    shared_assigns += ';\n'
                else:
                    shared_assigns += f' {sxpatconfig.VER_OR} '
                pit_quantity -= 1
            output_quantity += 1

        shared_assigns += f'//if an output has products and if it is part of the JSON model'
        shared_assigns += f'\n'
        o_idx = 0
        for key in self.graph.output_dict.keys():
            n = self.graph.output_dict[key]
            pn = list(self.graph.graph.predecessors(n))

            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX} = {sxpatconfig.VER_WIRE_PREFIX}{n} {sxpatconfig.VER_AND} '
            json_output_p_o = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{key}'
            o_idx += 1
            # print(f'HEREEEE')
            # print(f'{json_output_p_o}')
            # print(f'{self.json_model[json_output_p_o]}')
            if self.json_model[idx][json_output_p_o]:
                shared_assigns += f'1'
            else:
                shared_assigns += f'0'
            shared_assigns += ';\n'

        return shared_assigns

    def __output_assigns_shared(self):
        output_assigns = f'// output assigns\n'
        output_list = list(self.graph.output_dict.values())

        output_list = sorted(output_list)

        for n in self.graph.output_dict.values():
            pn = list(self.graph.graph.predecessors(n))
            gate = self.graph.graph.nodes[n][LABEL]

            if len(pn) == 1:
                if gate == sxpatconfig.NOT:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN} {n} = {sxpatconfig.VER_NOT}{sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX};\n'
                else:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN} {n} = {sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX};\n'
            elif len(pn) == 2:
                if gate == sxpatconfig.AND:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN}  = ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_AND} ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'
                elif gate == sxpatconfig.OR:
                    output_assigns += f'{sxpatconfig.VER_ASSIGN}  = ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_OR} ' \
                                      f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'

        output_assigns += f'{sxpatconfig.VER_ENDMODULE}'
        return output_assigns

    def __json_model_to_verilog_lut(self) -> List[AnyStr]:
        ver_string = []
        for idx in range(self.num_of_models):

            self.set_path(this_path=OUTPUT_PATH['ver'], id=idx)

            ver_str = f''
            # 1. module signature
            module_signature = self.__get_module_signature(idx)

            # 2. declarations
            # input/output declarations
            io_declaration = self.__declare_inputs_outputs()

            # 3. wire declarations
            intact_wires = self.__intact_gate_wires()

            # 4. subgraph input wires
            annotated_graph_input_wires = self.__get_subgraph_input_wires()

            # 5. subgraph output wires
            annotated_graph_output_wires = self.__get_subgraph_output_wires()

            # 6. json model input wires
            json_input_wires = self.__json_input_wire_declarations()

            # 7. json model wires
            json_model_wires = f'//json model\n'

            if self.graph.subgraph_num_outputs:
                json_model_wires += f'wire '

                for o_idx in range(self.graph.subgraph_num_outputs):
                    for mux_in_idx in range(2**self.spo):
                        json_model_wires += f'{sxpatconfig.LUT_MUX_PREFIX}0_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_INPUT_PREFIX}{mux_in_idx}'
                        if mux_in_idx == 2**self.spo - 1 and self.spo == 0 and o_idx == self.graph.subgraph_num_outputs - 1:
                            json_model_wires += ";\n"
                        else:
                            json_model_wires += ", "

                for o_idx in range(self.graph.subgraph_num_outputs):
                    for spo_idx in range(self.spo):
                        json_model_wires += f'{sxpatconfig.LUT_MUX_PREFIX}0_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_SELECTOR_PREFIX}{spo_idx}'
                        if spo_idx == self.spo - 1 and o_idx == self.graph.subgraph_num_outputs - 1:
                            json_model_wires += ';\n'
                        else:
                            json_model_wires += ', '
            else:
                json_model_wires += f'// No wires detected!'




            wire_declarations = intact_wires + annotated_graph_input_wires + annotated_graph_output_wires + json_input_wires + json_model_wires

            # 8. assigns
            # subgraph_inputs_assigns
            subgraph_inputs_assigns = self.__subgraph_inputs_assigns()

            # 9. map subgraph inputs to json inputs
            subgraph_to_json_input_mapping = self.__subgraph_to_json_input_mapping()

            # 10. json_model_and_subgraph_outputs_assigns

            json_model_and_subgraph_outputs_assigns = f'//json model assigns (approximated/XPATed part)\n'
            annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())

            json_model_and_subgraph_outputs_assigns += f''
            for o_idx in range(self.graph.subgraph_num_outputs):
                for mux_in_idx in range(2**self.spo):
                    mux_in = f'{sxpatconfig.LUT_MUX_PREFIX}{0}_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_INPUT_PREFIX}{mux_in_idx}'
                    data_input = f'{sxpatconfig.VER_ASSIGN} {mux_in}'
                    value = "1'b1" if self.json_model[idx][mux_in] == True else "1'b0"
                    json_model_and_subgraph_outputs_assigns += f'{data_input} = {value};\n'

            number_of_parameters_per_selector = math.ceil(math.log2(self.graph.subgraph_num_inputs))

            for o_idx in range(self.graph.subgraph_num_outputs):
                for spo_idx in range(self.spo):
                    selector = f'{sxpatconfig.LUT_MUX_PREFIX}{0}_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_SELECTOR_PREFIX}{spo_idx}'
                    selector_value = ""
                    for i in range(self.graph.subgraph_num_inputs):
                        selector_value += "0"
                    for p_idx in range(number_of_parameters_per_selector):
                        if self.json_model[idx][selector + f'_{sxpatconfig.LUT_PARAMETER_PREFIX}{p_idx}'] == True:
                            selector_value = selector_value[:p_idx] + "1" + selector_value[p_idx+1:]
                    selector_value = selector_value[::-1]
                    json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {selector} = {sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{int(selector_value,2)};\n'

            binary_combinations = list(itertools.product([0, 1], repeat=self.spo))

            for o_idx in range(self.graph.subgraph_num_outputs):
                json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = '
                for sel_combination in range(len(binary_combinations)):
                    # json_model_and_subgraph_outputs_assigns += f"{TAB}{TAB}{Z3_AND}(" if sel_combination != 0 else f"{Z3_AND}("

                    selectors = []
                    for sel_idx in range(len(binary_combinations[sel_combination])):
                        selector = f'mux0_o{o_idx}_sel{sel_idx}'
                        selectors.append(
                            f'{sxpatconfig.VER_NOT}({selector})' if not binary_combinations[sel_combination][sel_idx] else selector)
                    selectors_string = f' {sxpatconfig.VER_AND} '.join(selectors)

                    mux_in = f'mux0_o{o_idx}_in{sel_combination} {sxpatconfig.VER_AND} {selectors_string}' if selectors else f'mux0_o{o_idx}_in{sel_combination}'
                    json_model_and_subgraph_outputs_assigns += mux_in + ';\n' if sel_combination == len(
                        binary_combinations) - 1 else mux_in + ' | '



            # 11. the intact assigns
            intact_assigns = self.__intact_part_assigns()

            # 12. output assigns
            output_assigns = self.__output_assigns()

            assigns = subgraph_inputs_assigns + subgraph_to_json_input_mapping + json_model_and_subgraph_outputs_assigns + intact_assigns + output_assigns

            # assignments

            # endmodule
            ver_str = module_signature + io_declaration + wire_declarations + assigns

            ver_string.append(ver_str)

        return ver_string



    def __json_model_to_verilog_lut_MP(self) -> List[AnyStr]:
        ver_string = []
        for idx in range(self.num_of_models):

            self.set_path(this_path=OUTPUT_PATH['ver'], id=idx)

            ver_str = f''
            # 1. module signature
            module_signature = self.__get_module_signature(idx)

            # 2. declarations
            # input/output declarations
            io_declaration = self.__declare_inputs_outputs()

            # 3. wire declarations
            intact_wires = self.__intact_gate_wires()

            # 4. subgraph input wires
            annotated_graph_input_wires = self.__get_subgraph_input_wires()

            # 5. subgraph output wires
            annotated_graph_output_wires = self.__get_subgraph_output_wires()

            # 6. json model input wires
            json_input_wires = self.__json_input_wire_declarations()

            # 7. json model wires
            json_model_wires = f'//json model\n'

            if self.graph.subgraph_num_outputs:
                json_model_wires += f'wire '

                for o_idx in range(self.graph.subgraph_num_outputs):
                    for mux_in_idx in range(2**self.spo):
                        json_model_wires += f'{sxpatconfig.LUT_MUX_PREFIX}0_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_INPUT_PREFIX}{mux_in_idx}'
                        if mux_in_idx == 2**self.spo - 1 and self.spo == 0 and o_idx == self.graph.subgraph_num_outputs - 1:
                            json_model_wires += ";\n"
                        else:
                            json_model_wires += ", "

                for o_idx in range(self.graph.subgraph_num_outputs):
                    for spo_idx in range(self.spo):
                        json_model_wires += f'{sxpatconfig.LUT_MUX_PREFIX}0_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_SELECTOR_PREFIX}{spo_idx}'
                        if spo_idx == self.spo - 1 and o_idx == self.graph.subgraph_num_outputs - 1:
                            json_model_wires += ';\n'
                        else:
                            json_model_wires += ', '
            else:
                json_model_wires += f'// No wires detected!'




            wire_declarations = intact_wires + annotated_graph_input_wires + annotated_graph_output_wires + json_input_wires + json_model_wires

            # 8. assigns
            # subgraph_inputs_assigns
            subgraph_inputs_assigns = self.__subgraph_inputs_assigns()

            # 9. map subgraph inputs to json inputs
            subgraph_to_json_input_mapping = self.__subgraph_to_json_input_mapping()

            # 10. json_model_and_subgraph_outputs_assigns

            json_model_and_subgraph_outputs_assigns = f'//json model assigns (approximated/XPATed part)\n'
            annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())

            json_model_and_subgraph_outputs_assigns += f''
            for o_idx in range(self.graph.subgraph_num_outputs):
                for mux_in_idx in range(2**self.spo):
                    # in case all the parameters for the given data input are set to false,
                    # set the data input to false.
                    value_assigned = False
                    mux_in = f'{sxpatconfig.LUT_MUX_PREFIX}{0}_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_INPUT_PREFIX}{mux_in_idx}'
                    for mux_in_p in range(self.graph.subgraph_num_inputs*2+2):
                        if self.json_model[idx][mux_in + f'_{sxpatconfig.LUT_PARAMETER_PREFIX}{mux_in_p}'] == True:
                            value_assigned = True
                            if mux_in_p < self.graph.subgraph_num_inputs:
                                json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {mux_in} =  {sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{mux_in_p};\n'
                            elif mux_in_p < 2*self.graph.subgraph_num_inputs:
                                json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {mux_in} =  {sxpatconfig.VER_NOT}{sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{mux_in_p - self.graph.subgraph_num_inputs};\n'
                            elif mux_in_p == 2*self.graph.subgraph_num_inputs:
                                json_model_and_subgraph_outputs_assigns += f"{sxpatconfig.VER_ASSIGN} {mux_in} = 1'b1;\n"
                            else:
                                json_model_and_subgraph_outputs_assigns += f"{sxpatconfig.VER_ASSIGN} {mux_in} = 1'b0;\n"
                    if not value_assigned:
                        json_model_and_subgraph_outputs_assigns += f"{sxpatconfig.VER_ASSIGN} {mux_in} = 1'b0;\n"

            number_of_parameters_per_selector = math.ceil(math.log2(self.graph.subgraph_num_inputs))

            for o_idx in range(self.graph.subgraph_num_outputs):
                for spo_idx in range(self.spo):
                    selector = f'{sxpatconfig.LUT_MUX_PREFIX}{0}_{sxpatconfig.LUT_OUTPUT_PREFIX}{o_idx}_{sxpatconfig.LUT_SELECTOR_PREFIX}{spo_idx}'
                    selector_value = ""
                    for i in range(self.graph.subgraph_num_inputs):
                        selector_value += "0"
                    for p_idx in range(number_of_parameters_per_selector):
                        if self.json_model[idx][selector + f'_{sxpatconfig.LUT_PARAMETER_PREFIX}{p_idx}'] == True:
                            selector_value = selector_value[:p_idx] + "1" + selector_value[p_idx+1:]
                    selector_value = selector_value[::-1]
                    json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {selector} = {sxpatconfig.VER_JSON_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{int(selector_value,2)};\n'

            binary_combinations = list(itertools.product([0, 1], repeat=self.spo))

            for o_idx in range(self.graph.subgraph_num_outputs):
                json_model_and_subgraph_outputs_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = '
                for sel_combination in range(len(binary_combinations)):
                    # json_model_and_subgraph_outputs_assigns += f"{TAB}{TAB}{Z3_AND}(" if sel_combination != 0 else f"{Z3_AND}("

                    selectors = []
                    for sel_idx in range(len(binary_combinations[sel_combination])):
                        selector = f'mux0_o{o_idx}_sel{sel_idx}'
                        selectors.append(
                            f'{sxpatconfig.VER_NOT}({selector})' if not binary_combinations[sel_combination][sel_idx] else selector)
                    selectors_string = f' {sxpatconfig.VER_AND} '.join(selectors)

                    mux_in = f'mux0_o{o_idx}_in{sel_combination} {sxpatconfig.VER_AND} {selectors_string}' if selectors else f'mux0_o{o_idx}_in{sel_combination}'
                    json_model_and_subgraph_outputs_assigns += mux_in + ';\n' if sel_combination == len(
                        binary_combinations) - 1 else mux_in + ' | '



            # 11. the intact assigns
            intact_assigns = self.__intact_part_assigns()

            # 12. output assigns
            output_assigns = self.__output_assigns()

            assigns = subgraph_inputs_assigns + subgraph_to_json_input_mapping + json_model_and_subgraph_outputs_assigns + intact_assigns + output_assigns

            # assignments

            # endmodule
            ver_str = module_signature + io_declaration + wire_declarations + assigns

            ver_string.append(ver_str)

        return ver_string



    def __json_model_to_verilog_shared(self) -> List[AnyStr]:
        # print(Fore.CYAN + f'XPAT WITH sharing synthesis' + Style.RESET_ALL)
        ver_string = []
        for idx in range(self.num_of_models):
            self.set_path(this_path=OUTPUT_PATH['ver'], id=idx)

            input_list = list(self.graph.input_dict.values())
            input_list = self.sort_list(input_list)

            output_list = list(self.graph.output_dict.values())
            output_list = self.sort_list(output_list)

            # define module signature
            module_name = self.ver_out_name[:-2]
            module_signature = f"{sxpatconfig.VER_MODULE} {module_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"

            # 2) declare inputs
            input_declarations = f'// declaring inputs\n'
            input_declarations += f'{sxpatconfig.VER_INPUT}'

            for inp_idx, inp in enumerate(input_list):
                if inp_idx == len(input_list) - 1:
                    input_declarations += f' {inp};\n'
                else:
                    input_declarations += f' {inp}, '

            # 3) declare outputs
            output_declarations = f'// declaring outputs\n'
            output_declarations += f'{sxpatconfig.VER_OUTPUT}'
            for out_idx, out in enumerate(output_list):
                if out_idx == len(output_list) - 1:
                    output_declarations += f' {out};\n'
                else:
                    output_declarations += f' {out}, '

            # 4) declaring wires
            annotated_graph_input_wires = self.__json_model_input_declaration_shared()
            annotated_graph_output_wires = self.__json_model_output_declaration_shared()

            # json model wires
            json_model_wires = self.__json_model_wire_declarations_shared()
            wire_declarations = annotated_graph_input_wires + annotated_graph_output_wires + json_model_wires

            # 5) assigns
            json_input_assign = self.__json_input_assigns()

            # json_model_and_subgraph_outputs_assigns
            json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_product_assigns_shared(idx=idx)

            # shared logic assigns
            shared_assigns = self.__shared_logic_assigns(idx=idx)

            # output assigns
            output_assigns = self.__output_assigns_shared()

            assigns = json_input_assign + json_model_and_subgraph_outputs_assigns + shared_assigns + output_assigns

            # assignments

            # endmodule
            ver_str = module_signature + input_declarations + output_declarations + wire_declarations + assigns

            ver_string.append(ver_str)

        return ver_string

    def __annotated_graph_to_verilog_shared(self):
        # print(Fore.LIGHTCYAN_EX + f'Shared SubXPAT synthesis' + Style.RESET_ALL)
        ver_string = []

        for idx in range(self.num_of_models):
            self.set_path(this_path=OUTPUT_PATH['ver'], id=idx)
            ver_str = f''
            # 1. module declaration
            module_signature = self.__get_module_signature(idx)

            # 2. declarations
            # input/output declarations
            io_declaration = self.__declare_inputs_outputs()

            # intact wire declaration
            intact_wires = self.__intact_gate_wires()

            # subgraph input wires
            annotated_graph_input_wires = self.__get_subgraph_input_wires()
            annotated_graph_output_wires = self.__get_subgraph_output_wires()
            # json input wires
            json_input_wires = self.__json_input_wire_declarations()

            json_model_wires = self.__json_model_wire_declarations_shared()
            json_output_wires = self.__json_model_output_declaration_subxpat_shared()

            # 2. assigns
            json_input_assign = self.__subgraph_inputs_assigns_shared()
            subgraph_to_json_input_mapping = self.__subgraph_to_json_input_mapping()
            intact_assigns = self.__intact_part_assigns()

            json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_product_assigns_subxpat_shared(idx=idx)
            shared_assigns = self.__shared_logic_assigns_subxpat_shared(idx=idx)
            output_assigns = self.__output_assigns()

            ver_str += module_signature + io_declaration + intact_wires + annotated_graph_input_wires + json_input_wires + \
                       annotated_graph_input_wires + annotated_graph_output_wires + json_output_wires + json_model_wires
            ver_str += json_input_assign + subgraph_to_json_input_mapping + intact_assigns + \
                       json_model_and_subgraph_outputs_assigns + shared_assigns + output_assigns

            # print(f'{ver_str = }')
            ver_string.append(ver_str)

        return ver_string

    def __annotated_graph_to_verilog(self) -> List[AnyStr]:
        # print(Fore.CYAN + f'subxpat without sharing synthesis' + Style.RESET_ALL)
        ver_string = []
        for idx in range(self.num_of_models):

            self.set_path(this_path=OUTPUT_PATH['ver'], id=idx)

            ver_str = f''
            # 1. module signature
            module_signature = self.__get_module_signature(idx)

            # 2. declarations
            # input/output declarations
            io_declaration = self.__declare_inputs_outputs()

            # 3. wire declarations
            intact_wires = self.__intact_gate_wires()

            # 4. subgraph input wires
            annotated_graph_input_wires = self.__get_subgraph_input_wires()

            # 5. subgraph output wires
            annotated_graph_output_wires = self.__get_subgraph_output_wires()

            # 6. json model input wires
            json_input_wires = self.__json_input_wire_declarations()

            # 7. json model wires
            json_model_wires = self.__json_model_wire_declarations()

            wire_declarations = intact_wires + annotated_graph_input_wires + annotated_graph_output_wires + json_input_wires + json_model_wires

            # 8. assigns
            # subgraph_inputs_assigns
            subgraph_inputs_assigns = self.__subgraph_inputs_assigns()

            # 9. map subgraph inputs to json inputs
            subgraph_to_json_input_mapping = self.__subgraph_to_json_input_mapping()

            # 10. json_model_and_subgraph_outputs_assigns
            json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_and_subgraph_output_assigns(idx)

            # 11. the intact assigns
            intact_assigns = self.__intact_part_assigns()

            # 12. output assigns
            output_assigns = self.__output_assigns()

            assigns = subgraph_inputs_assigns + subgraph_to_json_input_mapping + json_model_and_subgraph_outputs_assigns + intact_assigns + output_assigns

            # assignments

            # endmodule
            ver_str = module_signature + io_declaration + wire_declarations + assigns

            ver_string.append(ver_str)

        return ver_string

    def __json_model_to_verilog(self):
        ver_string = []
        for idx in range(self.num_of_models):
            ver_str = f''
            module_name = 'module circuit('
            inputs = ', '.join([f'in{i}' for i in range(self.graph.num_inputs)])
            outputs = ', '.join([f'out{o}' for o in range(self.graph.num_outputs)])
            module_name += f'{inputs}, {outputs});\n\n'

            i_decl = f'input {inputs};\n'
            o_decl = f'output {outputs};\n'

            enabled_outputs = []
            for o in range(self.graph.num_outputs):
                if self.json_model[idx][f'p_o{o}']:
                    enabled_outputs.append(f'{o}')

            wires = []
            for o in enabled_outputs:
                for p in range(self.ppo):
                    wires.append(f'o{o}_t{p}')

            wire_decl = f"wire {', '.join(wire for wire in wires)};\n\n"
            products = ''
            for o in range(self.graph.num_outputs):
                if f'{o}' in enabled_outputs:
                    included_products = []
                    for p in range(self.ppo):
                        included_literals = []
                        for i in range(self.graph.num_inputs):
                            if self.json_model[idx][f'p_o{o}_t{p}_i{i}_s']:
                                if self.json_model[idx][f'p_o{o}_t{p}_i{i}_l']:
                                    included_literals.append(f'in{i}')
                                else:
                                    included_literals.append(f'~in{i}')
                        if included_literals:
                            products += f"assign o{o}_t{p} = {' & '.join(included_literals)};\n"
                            included_products.append(f'o{o}_t{p}')
                    products += f"assign out{o} = {' | '.join(included_products)};\n\n"
                else:
                    products += f'assign out{o} = 0;\n\n'

            ver_str += module_name + i_decl + o_decl + wire_decl + products
            ver_str += 'endmodule\n'
            ver_string.append(ver_str)
        return ver_string

    def __magraph_to_verilog(self):
        ver_str = f''
        input_list = list(self.__magraph.inputs)
        output_list = list(self.__magraph.outputs)

        # 1. module signature
        ver_str += f"{sxpatconfig.VER_MODULE} {self.ver_out_name[:-2]} ({', '.join(input_list)}, {', '.join(output_list)});\n"

        # 2. declarations
        # 2.1 inputs / outputs
        ver_str += '\n'.join((
            f"// input/output declarations",
            f"{sxpatconfig.VER_INPUT} {', '.join(input_list)};",
            f"{sxpatconfig.VER_OUTPUT} {', '.join(output_list)};"
        )) + '\n'
        # 2.2 wires
        if len(self.__magraph.gates) == 0:
            ver_str += "// No wires\n"
        else:
            ver_str += '\n'.join((
                f'// gates wires',
                f"{sxpatconfig.VER_WIRE} {', '.join(self.__magraph.gates)};"
            )) + '\n'

        # 3. assignments
        # 3.1 constants
        constants = {True: "1'b1", False: "1'b0"}
        ver_str += '\n'.join((
            f'// constants assignments',
            *(
                f'{sxpatconfig.VER_ASSIGN} {name} = {constants[value]};'
                for name, value in self.__magraph.constants
            )
        )) + '\n'
        # 3.2 gates
        cases = {
            (1, sxpatconfig.NOT): lambda ps: f'{sxpatconfig.VER_NOT}{ps[0]}',
            (2, sxpatconfig.AND): lambda ps: f'{ps[0]} {sxpatconfig.VER_AND} {ps[1]}',
            (2, sxpatconfig.OR): lambda ps: f'{ps[0]} {sxpatconfig.VER_OR} {ps[1]}',
        }
        lines = []
        for name in self.__magraph.gates:
            preds = self.__magraph.predecessors(name)
            case = (len(preds), self.__magraph.function_of(name))
            if case not in cases:
                pprint.e(f'ERROR! node {name} has an invalid value (#predecessors={case[0]}, function={case[1]})')
                exit(1)
            lines.append(f'{sxpatconfig.VER_ASSIGN} {name} = {cases[case](preds)};')
        ver_str += '\n'.join((
            f'// gates assignments',
            *lines
        )) + '\n'
        # 3.3 outputs
        ver_str += '\n'.join((
            f'// output assigns',
            *(
                f'{sxpatconfig.VER_ASSIGN} {name} = {self.__magraph.predecessors(name)[0]};'
                for name in self.__magraph.outputs
            )
        )) + '\n'

        ver_str += f'{sxpatconfig.VER_ENDMODULE}'
        return ver_str

    # =========================

    def estimate_area(self, this_path: str = None):
        if this_path:
            design_path = this_path
        else:
            design_path = self.ver_out_path

        yosys_command = f"read_verilog \"{design_path}\";\n" \
                        f"synth -flatten;\n" \
                        f"opt;\n" \
                        f"opt_clean -purge;\n" \
                        f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                        f"stat -liberty {sxpatconfig.LIB_PATH};\n"

        process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
        if process.stderr:
            raise Exception(color.error(f'Yosys ERROR!!!\n {process.stderr.decode()}'))
        else:

            if re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()):
                area = re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()).group(1)

            elif re.search(r"Don't call ABC as there is nothing to map", process.stdout.decode()):
                area = 0
            else:
                raise Exception(color.error('Yosys ERROR!!!\nNo useful information in the stats log!'))

        return float(area)

    def __synthesize_for_circuit_metrics(self, this_path: str = None):
        if this_path:
            design_in_path = this_path
        else:
            design_in_path = self.ver_out_path
        design_out_path = f'{design_in_path[:-2]}_for_metrics.v'
        yosys_command = f"read_verilog {design_in_path};\n" \
                        f"synth -flatten;\n" \
                        f"opt;\n" \
                        f"opt_clean -purge;\n" \
                        f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                        f"write_verilog -noattr {design_out_path}"
        process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
        if process.stderr:
            raise Exception(color.error(f'Yosys ERROR!!!\n {process.stderr.decode()}'))

    def estimate_delay(self, this_path: str = None):
        if this_path:
            design_in_path = this_path
            module_name = self.extract_module_name(this_path)
        else:
            design_in_path = self.ver_out_path
            module_name = self.extract_module_name()

        design_out_path = f'{design_in_path[:-2]}_for_metrics.v'
        delay_script = f'{design_in_path[:-2]}_for_delay.script'
        self.__synthesize_for_circuit_metrics(design_in_path)
        sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
                      f"read_verilog {design_out_path}\n" \
                      f"link_design {module_name}\n" \
                      f"create_clock -name clk -period 1\n" \
                      f"set_input_delay -clock clk 0 [all_inputs]\n" \
                      f"set_output_delay -clock clk 0 [all_outputs]\n" \
                      f"report_checks -digits 6\n" \
                      f"exit"
        with open(delay_script, 'w') as ds:
            ds.writelines(sta_command)
        # process = subprocess.run([sxpatconfig.OPENSTA, delay_script], stderr=PIPE)
        process = subprocess.run([sxpatconfig.OPENSTA, delay_script], stdout=PIPE, stderr=PIPE)
        if process.stderr:
            raise Exception(color.error(f'Yosys ERROR!!!\n {process.stderr.decode()}'))
        else:
            os.remove(delay_script)
            if re.search('(\d+.\d+).*data arrival time', process.stdout.decode()):
                time = re.search('(\d+.\d+).*data arrival time', process.stdout.decode()).group(1)
                return float(time)
            else:
                pprint.warning('OpenSTA Warning! Design has 0 delay!')
                return -1

    def extract_module_name(self, this_path: str = None):
        if this_path:
            design_in_path = this_path
        else:
            design_in_path = self.ver_out_path
        with open(design_in_path, 'r') as dp:
            contents = dp.readlines()
            for line in contents:
                if re.search(r'module\s+(.*)\(', line):
                    modulename = re.search(r'module\s+(.*)\(', line).group(1)

        return modulename

    def estimate_power(self, this_path: str = None):
        if this_path:
            design_in_path = this_path
            module_name = self.extract_module_name(this_path)
        else:
            design_in_path = self.ver_out_path
            module_name = self.extract_module_name()

        design_out_path = f'{design_in_path[:-2]}_for_metrics.v'
        power_script = f'{design_in_path[:-2]}_for_power.script'
        self.__synthesize_for_circuit_metrics(design_in_path)
        sta_command = f"read_liberty {sxpatconfig.LIB_PATH}\n" \
                      f"read_verilog {design_out_path}\n" \
                      f"link_design {module_name}\n" \
                      f"create_clock -name clk -period 1\n" \
                      f"set_input_delay -clock clk 0 [all_inputs]\n" \
                      f"set_output_delay -clock clk 0 [all_outputs]\n" \
                      f"report_checks\n" \
                      f"report_power -digits 12\n" \
                      f"exit"
        with open(power_script, 'w') as ds:
            ds.writelines(sta_command)
        # process = subprocess.run([sxpatconfig.OPENSTA, power_script], stderr=PIPE)

        process = subprocess.run([sxpatconfig.OPENSTA, power_script], stdout=PIPE, stderr=PIPE)
        if process.stderr:
            raise Exception(color.error(f'OpenSTA ERROR!!!\n {process.stderr.decode()}'))
        else:
            os.remove(power_script)
            pattern = r"Total\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+)[^0-9]*\d+\s+(\d+.\d+[^0-9]*\d+)\s+"
            if re.search(pattern, process.stdout.decode()):
                total_power_str = re.search(pattern, process.stdout.decode()).group(4)

                if re.search(r'e[^0-9]*(\d+)', total_power_str):
                    total_power = float(re.search(r'(\d+.\d+)e[^0-9]*\d+', total_power_str).group(1))
                    sign = (re.search(r'e([^0-9]*)(\d+)', total_power_str).group(1))
                    if sign == '-':
                        sign = -1
                    else:
                        sign = +1
                    exponant = int(re.search(r'e([^0-9]*)(\d+)', total_power_str).group(2))
                    total_power = total_power * (10 ** (sign * exponant))
                else:
                    total_power = total_power_str

                return float(total_power)

            else:
                pprint.warning('OpenSTA Warning! Design has 0 power consumption!')
                return -1

    # =========================

    def export_verilog(self, this_path: str = None, idx: int = -1):
        if idx < 0:
            idx = 0

        if this_path:
            with open(f'{this_path}/{self.ver_out_name}', 'w') as f:
                f.writelines(self.verilog_string[idx])
        else:
            with open(self.ver_out_path, 'w') as f:
                f.writelines(self.verilog_string[idx])

    def __repr__(self):
        return f'An object of class Synthesis:\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.graph = }\n' \
               f'{self.json_model = }\n'
