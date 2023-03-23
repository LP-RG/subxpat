from itertools import repeat, islice
from typing import Tuple, List, Callable, Any, Union
import networkx as nx
from Z3Log.config.config import *
from Z3Log.config.path import *
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *

from .config.config import *
from .templateSpecs import TemplateSpecs




class TemplateCreator:
    def __init__(self, template_specs: TemplateSpecs):
        self.__template_name = template_specs.template_name
        self.__benchmark_name = template_specs.benchmark_name
        self.__graph = self.import_graph()

        self.__z3pyscript_out_path = None


    @property
    def template_name(self):
        return self.__template_name
    @property
    def benchmark_name(self):
        return self.__benchmark_name
    @property
    def graph(self):
        return self.__graph



    def import_graph(self):
        """
        Reads the input Verilog benchmark located at "input/ver" and cleans it.
        Reads the cleaned version of the input Verilog benchmark from "output/ver".
        Converts it into a GraphViz (.gv) file, cleans it, and stores it at "output/gv"
        :return: the cleaned GraphViz file as a NetworkX graph object
        """
        temp_verilog_obj = Verilog(self.benchmark_name)
        convert_verilog_to_gv(self.benchmark_name)
        temp_graph_obj = Graph(self.benchmark_name, is_clean=False)
        temp_graph_obj.export_graph()
        return temp_graph_obj

    def __repr__(self):
        return f'An object of Class TemplateCreator:\n' \
               f'{self.__template_name = }\n' \
               f'{self.__benchmark_name}\n' \
               f'{self.graph = }'


class Template_SOP1(TemplateCreator):
    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)
        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__z3pyscript = None
        self.__z3_out_path = self.set_path(OUTPUT_PATH['z3'])

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
    def z3pyscript(self):
        return self.__z3pyscript

    @z3pyscript.setter
    def z3pyscript(self, input_z3pyscript):
        self.__z3pyscript = input_z3pyscript

    @property
    def z3_out_path(self):
        return self.__z3_out_path


    def set_path(self, this_path: Tuple[str, str]):
        folder, extenstion = this_path
        return f'{folder}/{self.benchmark_name}_{self.template_name}.{extenstion}'

    def export_z3pyscript(self):
        print(f'Storing in {self.z3_out_path}')
        with open(self.z3_out_path, 'w') as z:
            z.writelines(self.z3pyscript)



    def z3_generate_z3pyscript(self):
        imports = self.z3_generate_imports()
        z3_abs_function = self.z3_generate_z3_abs_function()
        input_variables_declaration = self.z3_generate_declare_input_variables()
        exact_integer_function_declaration = self.z3_generate_declare_integer_function(F_EXACT)
        approximate_integer_function_declaration = self.z3_generate_declare_integer_function(F_APPROXIMATE)
        utility_variables = self.z3_generate_utility_variables()
        implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters()
        exact_circuit_wires_declaration = self.z3_generate_exact_circuit_wires_declaration()
        exact_circuit_outputs_declaration = self.z3_generate_exact_circuit_outputs_declaration()
        exact_circuit_wire_constraints = self.z3_generate_exact_circuit_wire_constraints()
        approximate_circuit = ''
        for_all_solver = ''
        verification_solver = ''


        self.z3pyscript = imports + z3_abs_function +  input_variables_declaration + exact_integer_function_declaration + approximate_integer_function_declaration \
                        + utility_variables + implicit_parameters_declaration + exact_circuit_wires_declaration \
                        + exact_circuit_outputs_declaration
        self.export_z3pyscript()

    def z3_generate_imports(self):
        imports = f'from z3 import *\n' \
                  f'import sys\n' \
                  f'from time import time\n' \
                  f'from typing import Tuple, List, Callable, Any, Union\n' \
                  f'import json\n' \
                  f'\n'
        return imports

    def z3_generate_z3_abs_function(self):
        z3_abs_function = f'def z3_abs(x: ArithRef) -> ArithRef:\n' \
                          f'{TAB}return If(x >= 0, x, -x)\n' \
                          f'\n'

        return z3_abs_function

    def declare_gate(self, this_key: str, this_dict: dict = None):
        if this_dict is None:
            declaration = f"{this_key} = {Z3BOOL}('{this_key}')\n"
        else:
            declaration = f"{this_dict[this_key]} = {Z3BOOL}('{this_dict[this_key]}')\n"
        return declaration

    def z3_generate_declare_input_variables(self):
        input_variables = ''
        for inp_key in self.graph.input_dict.keys():
            input_variables += self.declare_gate(inp_key, self.graph.input_dict)
        input_variables += '\n'
        return input_variables

    def z3_generate_declare_integer_function(self, function_name):
        integer_function = ''
        temp_arg_list = ', '.join(repeat(BOOLSORT, self.graph.num_inputs))
        temp_arg_list += ', ' + INTSORT
        integer_function = f"{function_name} = {FUNCTION}('{function_name}', {temp_arg_list})\n"
        return integer_function

    def z3_generate_utility_variables(self):
        utility_variables = f"\n" \
                            f"difference = z3_abs({F_EXACT}({', '.join(self.graph.input_dict.values())}) - " \
                            f"{F_APPROXIMATE}({', '.join(self.graph.input_dict.values())})" \
                            f")\n" \
                            f"error = {Z3INT}('error')\n"

        utility_variables += '\n'
        return utility_variables

    def z3_generate_o(self):
        temp_o = ''
        for idx in range(self.graph.num_outputs):
            temp_name = f'{PRODUCT_PREFIX}{idx}'
            temp_o += self.declare_gate(temp_name)
        return temp_o

    def z3_generate_oti(self):
        temp_oti = ''
        for o_idx in range(self.graph.num_outputs):
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.graph.num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    temp_oti += self.declare_gate(p_s)
                    temp_oti += self.declare_gate(p_l)
        return temp_oti

    def z3_generate_declare_implicit_parameters(self):
        implicit_parameters = ''
        implicit_parameters += self.z3_generate_o()
        implicit_parameters += self.z3_generate_oti()
        implicit_parameters += '\n'
        return implicit_parameters


    def z3_generate_exact_circuit_wires_declaration(self):
        exact_wires_declaration = ''
        for g_idx in range(self.graph.num_gates):
            exact_wires_declaration += f"{EXACT_WIRES_PREFIX}{self.graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{EXACT_WIRES_PREFIX}{self.graph.num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.graph.num_inputs))}" \
                                       f", {INTSORT}" \
                                       f")\n"
        exact_wires_declaration += '\n'
        return exact_wires_declaration

    def z3_generate_exact_circuit_outputs_declaration(self):
        exact_circuit_output_declaration = ''
        for output_idx in range(self.graph.num_outputs):
            exact_circuit_output_declaration += f"{EXACT_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{EXACT_OUTPUT_PREFIX}{OUT}{output_idx}', " \
                                                f"{', '.join(repeat(BOOLSORT, self.graph.num_inputs + 1))}" \
                                                f")\n"
        exact_circuit_output_declaration += '\n'
        return exact_circuit_output_declaration

    def z3_generate_exact_circuit_wire_constraints(self):
        for gate_label in self.graph.gate_dict.values():
            print(f'{gate_label = }, {nx.descendants(self.graph.graph, gate_label) = }')
            print(self.graph.graph.nodes[gate_label])
            print(f'{nx.predecessor(self.graph.graph, gate_label) = }')
            print()
            exit()
        pass


# TODO: Later
class Template_SOP1ShareLogic(TemplateCreator):
    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)

