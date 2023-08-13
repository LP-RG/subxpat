from builtins import property
from typing import List, Dict, Callable, Iterable, Tuple
import json
import re
import networkx as nx
from colorama import Fore, Back, Style
import subprocess

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

    def __json_model_wire_declarations_shared(self):
        wire_list = f'//json model\n'
        wire_list += f'wire '
        for n in self.graph.output_dict.values():
            pn = list(self.graph.graph.predecessors(n)) #g17
            wire_list += f'{sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX}'
            if n == self.graph.subgraph_num_outputs - 1:
                wire_list += ';\n'
            else:
                wire_list += ', '
        
        for out_idx in range(self.graph.subgraph_num_outputs):
            for pit_idx in range(self.pit):
                wire_list += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{out_idx}'
                if pit_idx == self.pit - 1 and n == self.graph.subgraph_num_outputs - 1:
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

    def __json_model_lpp_product_assigns_shared(self):

        lpp_assigns = f'\n'
        lpp_assigns += f'//json model assigns (approximated Shared/XPAT part)\n'
        lpp_assigns += f'//assign literals to products\n'
        o_idx = self.graph.subgraph_num_outputs
        included_products = []

        for pit_idx in range(self.pit):
            included_products.append(f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}')

            included_literals = []
            for input_idx in range(self.graph.subgraph_num_inputs):
                p_s = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.SELECT_PREFIX}'
                p_l = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{sxpatconfig.LITERAL_PREFIX}'

                if self.json_model[p_s]:
                    if self.json_model[p_l]:
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


    def __json_model_product_to_output_assigns_shared(self):
        pto_assigns = 'f'

        return pto_assigns

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
        # print(f'{output_list = }')
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
        json_model_wires = self.__json_model_wire_declarations_shared()

        wire_declarations = intact_wires + annotated_graph_input_wires + annotated_graph_output_wires + json_model_wires

        # 3. assigns
        # subgraph_inputs_assigns
        subgraph_inputs_assigns = self.__subgraph_inputs_assigns()
        # json_model_and_subgraph_outputs_assigns
        json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_and_subgraph_output_assigns()

        #json_model_product_to_output_assigns_shared
        json_model_product_to_output_assigns_shared = self.__json_model_product_to_output_assigns_shared

        # the intact assings
        intact_assigns = self.__intact_part_assigns()
        # output assings
        output_assings = self.__output_assigns()

        assigns = subgraph_inputs_assigns + json_model_and_subgraph_outputs_assigns + json_model_product_to_output_assigns_shared + intact_assigns + output_assings

        # assignments

        # endmodule
        ver_str = module_signature + input_declarations + output_declarations + wire_declarations + assigns

        return ver_str

    def __json_model_to_verilog(self):
        verilog_str = f''
        return verilog_str

    def __json_model_to_verilog_shared(self):
        ver_str = f''

        # 1) extract inputs and outputs
        input_list = list(self.graph.subgraph_input_dict.values())
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
        annotated_graph_output_wires =  self.__json_model_output_declaration_shared()

        #json model wires
        json_model_wires = self.__json_model_wire_declarations_shared()
        wire_declarations = annotated_graph_input_wires + annotated_graph_output_wires + json_model_wires

        # 5) assigns
        json_input_assign = self.__json_input_assigns()

        
        # json_model_and_subgraph_outputs_assigns
        json_model_and_subgraph_outputs_assigns = self.__json_model_lpp_product_assigns_shared()

        # shared logic assigns
        shared_assigns = self.__shared_logic_assigns()

        # output assigns
        output_assigns = self.__output_assigns()

        assigns = json_input_assign + json_model_and_subgraph_outputs_assigns + shared_assigns + output_assigns

        # assignments

        # endmodule
        ver_str = module_signature + input_declarations + output_declarations + wire_declarations + assigns

        # print(f'{ver_str}')
        return ver_str

    def __shared_logic_assigns(self):

        shared_assigns = f'//if a product has literals and if the product is being "activated" for that output'
        shared_assigns += f'\n'
        for o_idx in range(self.graph.subgraph_num_outputs):
           
            for pit_idx in range(self.pit):
                json_output = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx}'
                shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{o_idx} = '
                shared_assigns += f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx} '        
                if self.json_model[json_output]:
                    shared_assigns += f'{sxpatconfig.VER_AND} 1'   
                else:
                    shared_assigns += f'{sxpatconfig.VER_AND} 0'    
                shared_assigns += ';\n'   

        shared_assigns += f'//compose an output with corresponding products (OR)'
        shared_assigns += f'\n'
        #assign OR products in output
        # Morteza added! fixing the correspondence between the graph outputs and the primary outputs ===================
        # mapping template outputs to primary outputs
        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        primary_output_list = list(self.graph.output_dict.values())
        sorted_annotated_graph_output_list = [-1] * len(annotated_graph_output_list)

        for node_idx in range(len(annotated_graph_output_list)):
            this_node = annotated_graph_output_list[node_idx]
            for key in self.graph.output_dict.keys():

                if primary_output_list[node_idx] == self.graph.output_dict[key]:
                    sorted_annotated_graph_output_list[key] = this_node
                    break
        #     print(f'{sorted_annotated_graph_output_list = }')
        #
        #
        # print(f'{annotated_graph_output_list = }')
        # print(f'{primary_output_list = }')
        # print(f'{sorted_annotated_graph_output_list= }')
        # ==============================================================================================================




        output_quantity = 0
        for item in sorted_annotated_graph_output_list:
            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{item} = '
            pit_quantity = self.pit
            for pit_idx in range(self.pit):    
                shared_assigns +=  f'{sxpatconfig.VER_WIRE_PREFIX}{sxpatconfig.SHARED_PRODUCT_PREFIX}{pit_idx}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{output_quantity}'     
                if pit_quantity == 1:
                    shared_assigns += ';\n'     
                else:
                    shared_assigns += f' {sxpatconfig.VER_OR} '
                pit_quantity -= 1 
            output_quantity +=1

        shared_assigns += f'//if an output has products and if it is part of the JSON model'
        shared_assigns += f'\n'
        o_idx = 0
        for key in self.graph.output_dict.keys():
            n = self.graph.output_dict[key]
            pn = list(self.graph.graph.predecessors(n)) #g17
            shared_assigns += f'{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{pn[0]}_{sxpatconfig.SHARED_PRODUCT_PREFIX} = {sxpatconfig.VER_WIRE_PREFIX}{pn[0]} {sxpatconfig.VER_AND} '
            json_output_p_o = f'{sxpatconfig.SHARED_PARAM_PREFIX}_{sxpatconfig.SHARED_OUTPUT_PREFIX}{key}'
            o_idx += 1
            # print(f'HEREEEE')
            # print(f'{json_output_p_o}')
            # print(f'{self.json_model[json_output_p_o]}')
            if self.json_model[json_output_p_o]:
                shared_assigns += f'1'   
            else:
                shared_assigns += f'0'    
            shared_assigns += ';\n'   

        return shared_assigns

    def __json_model_input_declaration_shared(self):

        annotated_graph_input_list = list(self.graph.subgraph_input_dict.values())

        annotated_graph_input_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_input_list]

        json_model_inputs = f"// JSON model input\n"
        json_model_inputs += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_input_list)};\n"
        
        return json_model_inputs

    def __json_model_output_declaration_shared(self):

        annotated_graph_output_list = list(self.graph.subgraph_output_dict.values())
        annotated_graph_output_list = [sxpatconfig.VER_WIRE_PREFIX + item for item in annotated_graph_output_list]

        json_model_outputs = f"// JSON model output\n"
        json_model_outputs += f"{sxpatconfig.VER_WIRE} {', '.join(annotated_graph_output_list)};\n"

        return json_model_outputs

    def __json_input_assigns(self):
        annotated_graph_input_list = list(self.graph.subgraph_input_dict.values())

        json_model_inputs = f"// JSON model input assign\n"
        for item in annotated_graph_input_list:
            json_model_inputs += f"{sxpatconfig.VER_ASSIGN} {sxpatconfig.VER_WIRE_PREFIX}{item} = {item};\n"

        return json_model_inputs

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

    def estimate_area(self, this_path: str = None):
        if this_path:
            yosys_command = f"read_verilog {this_path};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                            f"stat -liberty {sxpatconfig.LIB_PATH};\n"
        else:
            # print(f'{self.ver_out_path = }')
            yosys_command = f"read_verilog {self.ver_out_path};\n" \
                            f"synth -flatten;\n" \
                            f"opt;\n" \
                            f"opt_clean -purge;\n" \
                            f"abc -liberty {sxpatconfig.LIB_PATH} -script {sxpatconfig.ABC_SCRIPT_PATH};\n" \
                            f"stat -liberty {sxpatconfig.LIB_PATH};\n"

        process = subprocess.run([YOSYS, '-p', yosys_command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if process.stderr:
            raise Exception(Fore.RED + f'Yosys ERROR!!!\n {process.stderr.decode()}' + Style.RESET_ALL)
        else:

            if re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()):
                area = re.search(r'Chip area for .*: (\d+.\d+)', process.stdout.decode()).group(1)

            elif re.search(r"Don't call ABC as there is nothing to map", process.stdout.decode()):
                area = 0
            else:
                raise Exception(Fore.RED + 'Yosys ERROR!!!\nNo useful information in the stats log!' + Style.RESET_ALL)

        return float(area)

    def __graph_to_verilog(self):
        pass

    def export_verilog(self, this_path = None):
        if this_path:
            with open(f'{this_path}/{self.ver_out_name}', 'w') as f:
                f.writelines(self.verilog_string)
        with open(self.ver_out_path, 'w') as f:
            f.writelines(self.verilog_string)

    def __repr__(self):
        return f'An object of class Synthesis:\n' \
               f'{self.benchmark_name = }\n' \
               f'{self.graph = }\n' \
               f'{self.json_model = }\n'

