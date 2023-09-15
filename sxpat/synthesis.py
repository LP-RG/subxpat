from builtins import property
from typing import List, Dict, Callable, Iterable, Tuple
import json
import re
import networkx as nx
import subprocess
import os
from subprocess import PIPE
from colorama import Fore, Back, Style
from itertools import repeat

from Z3Log.graph import Graph
from Z3Log.config.config import *
from Z3Log.config.path import *

from .annotatedGraph import AnnotatedGraph
from .config import paths as sxpatpaths
from .config import config as sxpatconfig
from .templateSpecs import TemplateSpecs


class Synthesis:
    # TODO:
    # we assign wires to both inputs and outputs of an annotated subgraph
    # follow, inputs, red, white, outputs notation in the Verilog generation
    def __init__(self, template_specs: TemplateSpecs, graph_obj: AnnotatedGraph = None, json_obj=None):
        self.__benchmark_name = template_specs.benchmark_name
        self.__exact_benchmark_name = template_specs.exact_benchmark
        self.__template_name = template_specs.template_name
        self.__iterations = template_specs.iterations
        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__error_threshold = template_specs.et
        self.__graph: AnnotatedGraph = graph_obj
        self.__partitioning_percentage = template_specs.partitioning_percentage
        if json_obj == sxpatconfig.UNSAT or json_obj == sxpatconfig.UNKNOWN:
            print(Fore.RED + 'ERROR!!! the json does not contain any models!' + Style.RESET_ALL)
        else:
            self.__json_model: json = json_obj
            self.__use_json_model: bool = None
            self.__use_graph: bool = None

            folder, extension = sxpatpaths.OUTPUT_PATH[sxpatconfig.JSON]
            self.__json_in_path: str = None
            folder, extension = OUTPUT_PATH[sxpatconfig.GV]
            self.__graph_in_path: str = None

            self.__ver_out_name: str = None
            self.__ver_out_path: str = self.set_path(OUTPUT_PATH['ver'])

            self.__verilog_string: str = self.convert_to_verilog()

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage

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

    def set_path(self, this_path: Tuple[str, str]):
        folder, extenstion = this_path
        self.ver_out_name = f'{self.exact_name}_{sxpatconfig.LPP}{self.lpp}_{sxpatconfig.PPO}{self.ppo}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_{sxpatconfig.PAP}{self.pp}_{sxpatconfig.ITER}{self.iterations}.{extenstion}'
        return f'{folder}/{self.ver_out_name}'
        # return f'{folder}/{self.benchmark_name}_{sxpatconfig.LPP}{self.lpp}_{sxpatconfig.PPO}{self.ppo}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_{sxpatconfig.PAP}{self.pp}_{sxpatconfig.ITER}{self.iterations}.{extenstion}'

    def convert_to_verilog(self, use_graph: bool = use_graph, use_json_model: bool = use_json_model):
        """
        converts the graph and/or the json model into a Verilog string
        :param use_graph: if set to true, the graph is used
        :param use_json_model: if set to true, the json model is used
        :return: a Verilog description in the form of a String object
        """
        if use_graph and use_json_model:  # for SubXPAT
            verilog_str = self.__annotated_graph_to_verilog()
        elif use_graph and not use_json_model:  # for general use
            verilog_str = self.__graph_to_verilog()
        elif not use_graph and use_json_model:  # for XPAT
            verilog_str = self.__json_model_to_verilog()
        else:
            print(f'ERROR!!! the graph or json model cannot be converted into a Verilog script!')
            exit()
        return verilog_str

    def __json_input_wire_declarations(self):
        graph_input_list = list(self.graph.subgraph_input_dict.values())
        # print(f'{graph_input_list = }')

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
        pi_list.sort(key=lambda x: re.search('\d+', x).group())
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

        # for idx in range(self.graph.num_inputs, self.graph.subgraph_num_inputs):
        #     sub_to_json += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.VER_INPUT_PREFIX}{idx} = ' \
        #                    f'{sxpatconfig.VER_WIRE_PREFIX}{subgraph_input_list[idx]};\n'

        # print(f'{sub_to_json = }')

        return sub_to_json

    def __json_model_lpp_and_subgraph_output_assigns(self):
        lpp_assigns = f'//json model assigns (approximated/XPATed part)\n'
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        # print(f'{annotated_graph_output_list = }')
        lpp_assigns += f''
        for o_idx in range(self.graph.subgraph_num_outputs):
            p_o = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}'

            if self.json_model[p_o]:
                # p_o0_t0, p_o0_t1
                included_products = []
                for ppo_idx in range(self.ppo):
                    included_products.append(f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}')

                for ppo_idx in range(self.ppo):
                    included_literals = []
                    for input_idx in range(self.graph.subgraph_num_inputs):
                        p_s = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                        p_l = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'
                        if self.json_model[p_s]:
                            if self.json_model[p_l]:
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
        # print(f'{self.graph.graph_intact_gate_dict = }')
        # print(f'We are printing the constant assigns!!!==========================')
        for n_idx in self.graph.constant_dict.keys():
            n = self.graph.constant_dict[n_idx]

            sn = list(self.graph.graph.successors(n))
            Value = self.graph.graph.nodes[n][LABEL]

            if Value.upper() == 'FALSE':
                Value = "1'b0"
            else:
                Value = "1'b1"

            intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {Value};\n'
            #
            # for s in sn:
            #     intact_part += f'{sxpatconfig.VER_ASSIGN} {s} = {Value};\n'

        for n_idx in self.graph.graph_intact_gate_dict.keys():
            n = self.graph.graph_intact_gate_dict[n_idx]
            pn = list(self.graph.graph.predecessors(n))
            gate = self.graph.graph.nodes[n][LABEL]
            # print(f'{pn = }')
            for idx, el in enumerate(pn):
                if (el in list(self.graph.input_dict.values()) and el not in list(
                        self.graph.subgraph_input_dict.values())) \
                        or el in list(self.graph.output_dict.values()):
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
                print(f'ERROR!!! node {n} has more than two drivers!')
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

    def __get_module_signature(self):
        input_list = list(self.graph.input_dict.values())
        input_list.reverse()
        output_list = list(self.graph.output_dict.values())
        # Sort Dictionary
        module_name = self.ver_out_name[:-2]
        module_signature = f"{sxpatconfig.VER_MODULE} {module_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"
        return module_signature

    def __declare_inputs_outputs(self):
        input_list = list(self.graph.input_dict.values())
        input_list.reverse()
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

    def __annotated_graph_to_verilog(self):
        ver_str = f''
        # 1. module signature
        module_signature = self.__get_module_signature()

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
        json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_and_subgraph_output_assigns()

        # 11. the intact assigns
        intact_assigns = self.__intact_part_assigns()

        # 12. output assigns
        output_assigns = self.__output_assigns()

        assigns = subgraph_inputs_assigns + subgraph_to_json_input_mapping + json_model_and_subgraph_outputs_assigns + intact_assigns + output_assigns

        # assignments

        # endmodule
        ver_str = module_signature + io_declaration + wire_declarations + assigns

        return ver_str

    def __json_model_to_verilog(self):
        pass

    def __graph_to_verilog(self):
        pass

    # =========================
    def estimate_area(self, this_path: str = None):
        if this_path:
            design_path = this_path
        else:
            design_path = self.ver_out_path
        yosys_command = f"read_verilog {design_path};\n" \
                        f"synth -flatten;\n" \
                        f"opt;\n" \
                        f"opt_clean -purge;\n" \
                        f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                        f"stat -liberty {sxpatconfig.LIB_PATH};\n"


        process = subprocess.run([YOSYS, '-p', yosys_command], stdout=PIPE, stderr=PIPE)
        if process.stderr:
            raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}'+Style.RESET_ALL)
        else:

            if re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()):
                area = re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()).group(1)

            elif re.search(r"Don't call ABC as there is nothing to map", process.stdout.decode()):
                area = 0
            else:
                raise Exception(Fore.RED +'Yosys ERROR!!!\nNo useful information in the stats log!'+Style.RESET_ALL)

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
            raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}' + Style.RESET_ALL)

    def estimate_delay(self, this_path: str = None):
        if this_path:
            design_in_path = this_path
            module_name= self.extract_module_name(this_path)
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
            raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}' + Style.RESET_ALL)
        else:
            os.remove(delay_script)
            if re.search('(\d+.\d+).*data arrival time', process.stdout.decode()):
                time = re.search('(\d+.\d+).*data arrival time', process.stdout.decode()).group(1)
                return float(time)
            else:
                print(Fore.RED + f'ERROR!!! No delay was found!' + Style.RESET_ALL)
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
            raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}' + Style.RESET_ALL)
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
                print(Fore.YELLOW + f'Warning!!! No power was found!' + Style.RESET_ALL)
                return -1

    # =========================

    def export_verilog(self, this_path: str = None):
        if this_path:
            with open(f'{this_path}/{self.ver_out_name}', 'w') as f:
                f.writelines(self.verilog_string)
        else:

            with open(self.ver_out_path, 'w') as f:
                f.writelines(self.verilog_string)

    def __repr__(self):
        return f'An object of class Synthesis:\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.graph = }\n' \
               f'{self.json_model = }\n'
