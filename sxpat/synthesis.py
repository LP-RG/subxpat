from builtins import property
from typing import List, Dict, Callable, Iterable, Tuple
import json
import re

from Z3Log.graph import Graph
from Z3Log.config.config import *
from Z3Log.config.path import *

from .annotatedGraph import AnnotatedGraph
from .config import paths as sxpatpaths
from .config import config as sxpatconfig
from .templateSpecs import TemplateSpecs


class Synthesis:
    def __init__(self, template_specs: TemplateSpecs, graph_obj: AnnotatedGraph = None, json_obj=None):
        self.__benchmark_name = template_specs.benchmark_name
        self.__template_name = template_specs.template_name
        self.__template_name = template_specs.template_name
        self.__graph: AnnotatedGraph = graph_obj
        if json_obj == sxpatconfig.UNSAT:
            print('ERROR!!! the json does not contain any models!')
            exit()
        self.__json_model: json = json_obj

        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__error_threshold = None

        self.__use_json_model: bool = None
        self.__use_graph: bool = None

        folder, extension = sxpatpaths.OUTPUT_PATH[sxpatconfig.JSON]
        self.__json_in_path: str = None
        folder, extension = OUTPUT_PATH[sxpatconfig.GV]
        self.__graph_in_path: str = None

        self.__ver_out_path: str = self.set_path(OUTPUT_PATH['ver'])
        self.__verilog_string: str = self.convert_to_verilog()

    @property
    def benchmark_name(self):
        return self.__benchmark_name

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
        return f'{folder}/{self.benchmark_name}_{sxpatconfig.LPP}{self.lpp}_{sxpatconfig.PPO}{self.ppo}_{self.et}_{self.template_name}.{extenstion}'

    def __json_model_wire_declarations(self):
        wire_list = f'wire '
        for o_idx in range(self.graph.subgraph_num_outputs):
            for ppo_idx in range(self.ppo):
                wire_list += f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}'

                if ppo_idx == self.ppo - 1 and o_idx == self.graph.subgraph_num_outputs - 1:
                    wire_list += ';\n'
                else:
                    wire_list += ', '
        return wire_list

    def __json_model_lpp_and_subgraph_output_assigns(self):
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        lpp_assigns = f''
        for o_idx in range(self.graph.subgraph_num_outputs):
            p_o = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}'
            if self.json_model[p_o]:
                for ppo_idx in range(self.ppo):
                    included_literals = []
                    for input_idx in range(self.graph.subgraph_num_inputs):
                        p_s = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                        p_l = f'{sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx}_{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'

                        if self.json_model[p_s]:
                            if self.json_model[p_l]:
                                included_literals.append(f'{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}')
                            else:
                                included_literals.append(
                                    f'{sxpatconfig.VER_NOT}{sxpatconfig.INPUT_LITERAL_PREFIX}{input_idx}')
                    if included_literals:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = ' \
                                      f"{' & '.join(included_literals)};\n"
                    else:
                        lpp_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.PRODUCT_PREFIX}{o_idx}_{sxpatconfig.TREE_PREFIX}{ppo_idx} = 1;\n'
            else:
                lpp_assigns += f'{self.graph.subgraph_output_dict[o_idx]} = 0;\n'

        print(f'{lpp_assigns = }')
        return lpp_assigns

    def __json_model_ppo_subgraph_output_assigns(self):
        pass

    def __annotated_graph_to_verilog(self):
        ver_str = f''
        # module signature
        print(f'{self.graph = }')

        # TODO:
        # FIX ORDER NO MATTER WHAT MAYBE YOU CAN USE ORDERED DICT
        # module signature
        input_list = list(self.graph.subgraph_input_dict.values())
        input_list.reverse()
        output_list = list(self.graph.output_dict.values())
        module_signature = f"module {self.benchmark_name} ({', '.join(input_list)}, {', '.join(output_list)});\n"

        # input/output declarations
        input_declarations = f"input {', '.join(input_list)};\n"
        output_declarations = f"input {', '.join(output_list)};\n"

        # wire declarations
        intact_gate_list = list(self.graph.graph_intact_gate_dict.values())
        intact_wires = f"//intact gates\n"
        intact_wires += f"wire {', '.join(intact_gate_list)};\n"

        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        annotated_graph_output_wires = f"//annotated subgraph outputs\n"
        annotated_graph_output_wires += f"wire {', '.join(annotated_graph_output_list)}\n"

        json_model_wires = self.__json_model_wire_declarations()

        # assigns
        # json_model_and_subgraph_outputs_assigns
        json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_and_subgraph_output_assigns()


        assigns = json_model_and_subgraph_outputs_assigns


        wire_declarations = intact_wires + annotated_graph_output_wires + json_model_wires + assigns

        # assignments

        # endmodule
        ver_str = module_signature + input_declarations + output_declarations + wire_declarations
        print(f'{ver_str = }')
        return ver_str

    def __json_model_to_verilog(self):
        pass

    def __graph_to_verilog(self):
        pass

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

    def export_verilog(self):
        with open(self.ver_out_path, 'w') as f:
            f.writelines(self.verilog_string)

    def __repr__(self):
        return f'An object of class Synthesis:\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.graph = }\n' \
               f'{self.json_model = }\n'
