from builtins import property
from typing import List, Dict, Callable, Iterable, Tuple
import json
import re
import networkx as nx
from colorama import Fore, Back, Style

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
    def __init__(self, template_specs: TemplateSpecs, graph_obj: AnnotatedGraph = None, json_obj=None, subxpat: bool = False,
                 shared: bool = True):
        print(f'{Fore.RED}{template_specs = }{Style.RESET_ALL}')

        self.__subxpat: bool = subxpat
        self.__shared: bool = shared
        if self.shared:
            self.__products_in_total : int = template_specs.products_in_total
        else:
            self.__products_in_total: float = float('inf')


        self.__benchmark_name = template_specs.benchmark_name
        self.__template_name = template_specs.template_name
        self.__graph: AnnotatedGraph = graph_obj
        if json_obj == sxpatconfig.UNSAT:
            print('ERROR!!! the json does not contain any models!')
            exit()
        self.__json_model: json = json_obj

        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__error_threshold = template_specs.et

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
    def benchmark_name(self):
        return self.__benchmark_name


    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def shared(self):
        return self.__shared

    @property
    def products_in_total(self):
        return self.__products_in_total

    @property
    def pit(self):
        return self.__products_in_total

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

    @property
    def verilog_string(self):
        return self.__verilog_string

    @verilog_string.setter
    def verilog_string(self, this_verilog_string):
        self.__verilog_string = this_verilog_string

    def set_path(self, this_path: Tuple[str, str]):
        folder, extenstion = this_path
        self.ver_out_name = f'{self.benchmark_name}_{sxpatconfig.LPP}{self.lpp}_{sxpatconfig.PPO}{self.ppo}_{sxpatconfig.PIT}{self.pit}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}.{extenstion}'
        return f'{folder}/{self.benchmark_name}_{sxpatconfig.LPP}{self.lpp}_{sxpatconfig.PPO}{self.ppo}_{sxpatconfig.PIT}{self.pit}_{sxpatconfig.TEMPLATE_SPEC_ET}{self.et}_{self.template_name}.{extenstion}'

    def convert_to_verilog(self, use_graph: bool = use_graph, use_json_model: bool = use_json_model):
        """
        converts the graph and/or the json model into a Verilog string
        :param use_graph: if set to true, the graph is used
        :param use_json_model: if set to true, the json model is used
        :return: a Verilog description in the form of a String object
        """

        if not self.subxpat and not self.shared:
            verilog_str = self.__json_model_to_verilog()
        elif not self.subxpat and self.shared:
            print(f'this part is for Cata')
            verilog_str = self.__json_model_to_verilog_shared()
        elif self.subxpat and not self.shared:
            verilog_str = self.__annotated_graph_to_verilog()
        elif self.subxpat and self.shared:
            verilog_str = self.__annotated_graph_to_verilog_shared()
        else:
            raise Exception("The experiment is not recongnized!")

        return verilog_str

    def __json_model_wire_declarations(self):
        wire_list = f'//json model\n'
        wire_list += f'wire '
        for o_idx in range(self.graph.subgraph_num_outputs):
            for ppo_idx in range(self.ppo):
                wire_list += f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}'

                if ppo_idx == self.ppo - 1 and o_idx == self.graph.subgraph_num_outputs - 1:
                    wire_list += ';\n'
                else:
                    wire_list += ', '
        return wire_list

    def __subgraph_inputs_assigns(self):
        s_inputs_assigns = f'//subgraph inputs assigns\n'
        for n in self.graph.subgraph_input_dict.values():
            s_inputs_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {n};\n'

        return s_inputs_assigns

    def __json_model_lpp_and_subgraph_output_assigns(self):
        lpp_assigns = f'//json model assigns (approximated/XPATed part)\n'
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
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
                                    f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.INPUT_LITERAL_PREFIX}n{input_idx}')
                            else:
                                included_literals.append(
                                    f'{sxpatconfig.VER_NOT}{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.INPUT_LITERAL_PREFIX}n{input_idx}')
                    if included_literals:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = ' \
                                       f"{' & '.join(included_literals)};\n"
                    else:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = 1;\n'

                lpp_assigns += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = {' | '.join(included_products)};\n"
            else:
                lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{self.graph.subgraph_output_dict[o_idx]} = 0;\n'

        return lpp_assigns

    def __intact_part_assigns(self):
        intact_part = f'// intact gates assigns\n'
        print(f'{self.graph.graph_intact_gate_dict = }')
        for n_idx in self.graph.graph_intact_gate_dict.keys():

            n = self.graph.graph_intact_gate_dict[n_idx]
            pn = list(self.graph.graph.predecessors(n))
            gate = self.graph.graph.nodes[n][LABEL]

            if len(pn) == 1:
                intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = {sxpatconfig.VER_NOT}{sxpatconfig.VER_WIRE_PREFIX}{pn[0]};\n'
            elif len(pn) == 2:
                if gate == sxpatconfig.AND:
                    intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = ' \
                                   f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_AND} ' \
                                   f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'
                elif gate == sxpatconfig.OR:
                    intact_part += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{n} = ' \
                                   f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_OR} ' \
                                   f'{sxpatconfig.VER_WIRE_PREFIX}{pn[1]};\n'
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
        intact_gate_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in intact_gate_list]

        intact_wires = f'//intact gates wires \n'
        if len(intact_gate_list) > 0:
            intact_wires += f"{sxpatconfig.VER_WIRE} {', '.join(intact_gate_list)};\n"
        else:
            intact_wires += f'{TAB}//no intact gates detected!\n'
        return intact_wires

    def __annotated_graph_to_verilog_shared(self):
        verilog_str = f''
        print(f'HERE WE ARE GONNA CONVERT THE RESULT OF SUBXPAT AND SHARED INTO A VERILOG')
        return verilog_str

    def __annotated_graph_to_verilog(self):
        ver_str = f''
        # module signature
        # print(f'{self.graph = }')

        # TODO:
        # FIX ORDER NO MATTER WHAT MAYBE YOU CAN USE ORDERED DICT
        # 1. module signature
        input_list = list(self.graph.subgraph_input_dict.values())
        input_list.reverse()
        output_list = list(self.graph.output_dict.values())


        module_name = self.ver_out_name[:-2]
        module_signature = f"{sxpatconfig.VER_MODULE} {module_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"

        # 2. declarations
        # input/output declarations
        input_declarations = f"{sxpatconfig.VER_INPUT} {', '.join(input_list)};\n"
        for o in self.graph.subgraph_output_dict:
            print(f'{self.graph.subgraph_output_dict[o] = }')
        print(f'{output_list = }')
        output_declarations = f"{sxpatconfig.VER_OUTPUT} {', '.join(output_list)};\n"

        # wire declarations

        intact_wires = self.__intact_gate_wires()

        # subgrpah input wires
        annotated_graph_input_list = list(self.graph.subgraph_input_dict.values())
        annotated_graph_input_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_input_list]
        annotated_graph_input_wires = f"//annotated subgraph inputs\n"
        annotated_graph_input_wires += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_input_list)};\n"

        # subgraph output wires
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        annotated_graph_output_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_output_list]
        annotated_graph_output_wires = f"//annotated subgraph outputs\n"
        annotated_graph_output_wires += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_output_list)};\n"
        # json model wires
        json_model_wires = self.__json_model_wire_declarations()

        wire_declarations = intact_wires + annotated_graph_input_wires + annotated_graph_output_wires + json_model_wires

        # 3. assigns
        # subgraph_inputs_assigns
        subgraph_inputs_assigns = self.__subgraph_inputs_assigns()
        # json_model_and_subgraph_outputs_assigns
        json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_and_subgraph_output_assigns()
        # the intact assings
        intact_assigns = self.__intact_part_assigns()
        # output assings
        output_assings = self.__output_assigns()

        assigns = subgraph_inputs_assigns + json_model_and_subgraph_outputs_assigns + intact_assigns + output_assings

        # assignments

        # endmodule
        ver_str = module_signature + input_declarations + output_declarations + wire_declarations + assigns

        return ver_str

    def __json_model_to_verilog(self):
        verilog_str = f''
        return verilog_str

    def __json_model_to_verilog_shared(self):
        verilog_str = f''
        print(f"Cata's next task!")

        # 1) extract inputs and outputs
        input_list = list(self.graph.subgraph_input_dict.values())
        input_list = self.sort_list(input_list)

        output_list = list(self.graph.output_dict.values())
        output_list = self.sort_list(output_list)

        # define module signature
        module_name = self.ver_out_name[:-2]
        module_signature = f"{sxpatconfig.VER_MODULE} {module_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"


        # 2) declare inputs
        decl_inp = f'// declaring inputs\n'
        decl_inp += f'{sxpatconfig.VER_INPUT}'

        for inp_idx, inp in enumerate(input_list):
            if inp_idx == len(input_list) - 1:
                decl_inp += f' {inp};\n'
            else:
                decl_inp += f' {inp}, '

        # 3) declare outputs
        decl_out = f'// declaring outputs\n'
        decl_out += f'{sxpatconfig.VER_OUTPUT}'
        for out_idx, out in enumerate(output_list):
            if out_idx == len(output_list) - 1:
                decl_out += f' {out};\n'
            else:
                decl_out += f' {out}, '

        # 4) assigning wires

        verilog_str = module_signature + decl_inp + decl_out
        return verilog_str


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


    def __graph_to_verilog(self):
        pass

    def export_verilog(self):
        with open(self.ver_out_path, 'w') as f:
            f.writelines(self.verilog_string)

    def __repr__(self):
        return f'An object of class Synthesis:\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.graph = }\n' \
               f'{self.json_model = }\n'
