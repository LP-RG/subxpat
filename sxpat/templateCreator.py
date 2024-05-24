from itertools import repeat, islice
from typing import Tuple, List, Callable, Any, Union
import networkx as nx
import json
import subprocess
from subprocess import PIPE
from colorama import Fore, Style

from Z3Log.config.config import *
from Z3Log.config.path import *
from Z3Log.graph import Graph
from Z3Log.verilog import Verilog
from Z3Log.utils import *

from .labeling import *
from .config.config import *
from .templateSpecs import TemplateSpecs
from .config import paths as sxpatpaths
from .annotatedGraph import AnnotatedGraph


class TemplateCreator:
    is_two_phase_kind = False

    def __init__(self, template_specs: TemplateSpecs):
        self.__template_name = template_specs.template_name
        self.__benchmark_name = template_specs.benchmark_name
        self.__exact_benchmark_name = template_specs.exact_benchmark
        self.__partitioning_percentage = template_specs.pp

        self.__imax = template_specs.imax
        self.__omax = template_specs.omax

        self.__subxpat: bool = template_specs.subxpat
        self.__shared: bool = template_specs.shared

        self.__current_graph = self.import_graph()
        self.__exact_graph = self.import_exact_graph()
        self.__z3pyscript_out_path = None

        if self.current_graph.subgraph:
            self.current_graph.export_annotated_graph()

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def shared(self):
        return self.__shared

    @property
    def partitioning_percentage(self):
        return self.__partitioning_percentage

    @property
    def pp(self):
        return self.__partitioning_percentage

    @property
    def template_name(self):
        return self.__template_name

    @template_name.setter
    def template_name(self, this_template_name):
        self.__template_name = this_template_name

    @property
    def benchmark_name(self):
        return self.__benchmark_name

    @benchmark_name.setter
    def benchmark_name(self, this_benchmark_name):
        self.__benchmark_name = this_benchmark_name

    @property
    def exact_benchmark(self):
        return self.__exact_benchmark_name

    @exact_benchmark.setter
    def exact_benchmark(self, this_exact_benchmark):
        self.__exact_benchmark_name = this_exact_benchmark

    @property
    def current_graph(self):
        return self.__current_graph

    @current_graph.setter
    def current_graph(self, this_current_graph):
        self.__current_graph = this_current_graph

    @property
    def exact_graph(self):
        return self.__exact_graph

    @exact_graph.setter
    def exact_graph(self, this_exact_graph):
        self.__exact_graph = this_exact_graph

    @property
    def imax(self):
        return self.__imax

    @imax.setter
    def imax(self, this_imax):
        self.__imax = this_imax

    @property
    def omax(self):
        return self.__omax

    @omax.setter
    def omax(self, this_omax):
        self.__omax = this_omax

    def import_graph(self):
        """
        Reads the input Verilog benchmark located at "input/ver" and cleans it.
        Reads the cleaned version of the input Verilog benchmark from "output/ver".
        Converts it into a GraphViz (.gv) file, cleans it, and stores it at "output/gv"
        :return: the cleaned GraphViz file as a NetworkX graph object
        """
        # print(Fore.LIGHTMAGENTA_EX+ f'importing {self.benchmark_name}' + Style.RESET_ALL)
        temp_verilog_obj = Verilog(self.benchmark_name)

        convert_verilog_to_gv(self.benchmark_name)
        # exit()
        temp_graph_obj = AnnotatedGraph(self.benchmark_name, is_clean=False, partitioning_percentage=1)

        return temp_graph_obj

    def import_exact_graph(self):
        exact_benchmark_name = ''
        temp_verilog_obj = Verilog(self.exact_benchmark)
        convert_verilog_to_gv(self.exact_benchmark)
        temp_graph_obj = AnnotatedGraph(self.exact_benchmark, is_clean=False, partitioning_percentage=0)

        return temp_graph_obj

    def run_phase1(self, arguments: Tuple):
        raise NotImplementedError(f"{self.__class__.__name__}.run_phase1(...) is not yet implemented.")

    def run_phase2(self):
        raise NotImplementedError(f"{self.__class__.__name__}.run_phase2(...) is not yet implemented.")

    def __repr__(self):
        return f'An object of Class TemplateCreator:\n' \
               f'{self.__template_name = }\n' \
               f'{self.__benchmark_name}\n' \
               f'{self.current_graph = }\n'


class Template_SOP1(TemplateCreator):
    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)
        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__subxpat: bool = template_specs.subxpat
        self.__error_threshold = template_specs.et
        self.__iterations = template_specs.iterations
        self.__num_models = template_specs.num_of_models

        self.__z3pyscript = None
        self.__z3_out_path = None

        self.__json_out_path = None
        self.__json_in_path = None
        self.__json_model: List = []
        self.__json_status: List = []

    @property
    def num_models(self):
        return self.__num_models

    @num_models.setter
    def num_models(self, this_num_models):
        self.__num_models = this_num_models

    @property
    def literals_per_product(self):
        return self.__literal_per_product

    @property
    def lpp(self):
        return self.__literal_per_product

    @lpp.setter
    def lpp(self, this_lpp):
        self.__literal_per_product = this_lpp

    @property
    def products_per_output(self):
        return self.__product_per_output

    @property
    def ppo(self):
        return self.__product_per_output

    @ppo.setter
    def ppo(self, this_ppo):
        self.__product_per_output = this_ppo

    @property
    def subxpat(self):
        return self.__subxpat

    @property
    def z3pyscript(self):
        return self.__z3pyscript

    @z3pyscript.setter
    def z3pyscript(self, input_z3pyscript):
        self.__z3pyscript = input_z3pyscript

    @property
    def json_model(self):
        return self.__json_model

    @json_model.setter
    def json_model(self, this_json_model):
        self.__json_model = this_json_model

    @property
    def json_status(self):
        return self.__json_status

    @json_status.setter
    def json_status(self, this_status):
        self.__json_status = this_status

    @property
    def et(self):
        return self.__error_threshold

    @et.setter
    def et(self, value):
        self.__error_threshold = value

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iteration: int):
        self.__iterations = this_iteration

    @property
    def z3_out_path(self):
        return self.__z3_out_path

    @z3_out_path.setter
    def z3_out_path(self, this_z3_out_path):
        self.__z3_out_path = this_z3_out_path

    @property
    def json_out_path(self):
        return self.__json_out_path

    @json_out_path.setter
    def json_out_path(self, this_json_out_path):
        self.__json_out_path = this_json_out_path

    @property
    def json_in_path(self):
        return self.__json_in_path

    @json_in_path.setter
    def json_in_path(self, this_json_path):
        self.__json_in_path = this_json_path

    def label_graph(self, min_labeling: bool = False,  partial: bool = False, et: int = -1, parallel: bool = False):
        print(f'{et = } for partial labeling!')
        # labels = labeling(self.exact_benchmark, self.benchmark_name, min_labeling, parallel)
        labels, _ = labeling_explicit(self.exact_benchmark, self.benchmark_name, constant_value=0, min_labeling=min_labeling,
                                      partial=partial, et=et, parallel=parallel)

        for n in self.current_graph.graph.nodes:
            if n in labels:
                self.current_graph.graph.nodes[n][WEIGHT] = int(labels[n])
            else:
                self.current_graph.graph.nodes[n][WEIGHT] = int(-1)

    # TODO: Deprecated
    def label_graph_old(self, constant_value=2, min_labeling: bool = False, parallel: bool = False):
        """ ~ DEPRECATED ~ """
        print(Fore.BLUE + f'labeling...' + Style.RESET_ALL)
        labels1, labels0 = labeling_explicit(self.exact_benchmark, self.benchmark_name, constant_value, min_labeling, parallel=parallel)
        for n in self.current_graph.graph.nodes:
            if n in labels0 and n in labels1:
                if constant_value == 0:
                    self.current_graph.graph.nodes[n][WEIGHT] = int(labels0[n])
                elif constant_value == 1:
                    self.current_graph.graph.nodes[n][WEIGHT] = int(labels1[n])
                else:
                    self.current_graph.graph.nodes[n][WEIGHT] = max(int(labels0[n]), int(labels1[n]))

    def set_new_context(self, specs_obj: TemplateSpecs):
        self.lpp = specs_obj.lpp
        self.ppo = specs_obj.ppo
        self.iterations = specs_obj.iterations
        self.template_name = specs_obj.template_name
        self.benchmark_name = specs_obj.benchmark_name
        self.exact_benchmark = specs_obj.exact_benchmark
        self.json_out_path = self.set_path(sxpatpaths.OUTPUT_PATH[JSON])
        self.z3_out_path = self.set_path(OUTPUT_PATH['z3'])

    def set_path(self, this_path: Tuple[str, str]):
        folder, extension = this_path
        # print(f'setting json out path...')
        # print(f'{self.benchmark_name = }')
        if re.search('id', self.benchmark_name):
            path = f'{folder}/{self.benchmark_name}_{ITER}{self.iterations}.{extension}'
        else:
            path = f'{folder}/{self.benchmark_name}_{TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_{ITER}{self.iterations}.{extension}'
        # print(f'{path = }')
        return path

    def export_z3pyscript(self):
        # print(f'Storing in {self.z3_out_path}')
        with open(self.z3_out_path, 'w') as z:
            z.writelines(self.z3pyscript)

    def import_json_model(self, this_path=None):
        self.json_model = []
        self.json_status = []
        if this_path:
            self.json_in_path(this_path)
        else:
            self.json_in_path = self.set_path(sxpatpaths.OUTPUT_PATH[JSON])

        with open(self.json_in_path, 'r') as f:
            data = json.load(f)
        for d in data:
            for key in d.keys():
                if key == RESULT:
                    if d[key] == SAT:
                        self.json_model.append(d[MODEL])
                        self.json_status.append(SAT)
                    elif d[key] == UNSAT:
                        self.json_model.append(None)
                        self.json_status.append(UNSAT)
                    else:
                        self.json_model.append(None)
                        self.json_status.append(UNKNOWN)

    def get_json_runtime(self, this_id: int = 0):
        with open(self.json_in_path, 'r') as f:
            data = json.load(f)

        for d in data:
            for key in d.keys():
                if key == "total_time":
                    return float(d[key])

    def run_z3pyscript(self, ET=2, num_models=1, timeout=10800):
        # print(f'{self.z3_out_path = }')
        # print(f'{ET = }')
        process = subprocess.run([PYTHON3, self.z3_out_path, f'{ET}', f'{num_models}', f'{timeout}'], stderr=PIPE, stdout=PIPE)
        if process.stderr:
            print(Fore.RED + f"{process.stderr.decode()}" + Style.RESET_ALL)
            raise Exception(Fore.RED + f'ERROR!!! Cannot run file {self.z3_out_path}' + Style.RESET_ALL)

    def z3_generate_z3pyscript(self):
        if self.subxpat or (not self.subxpat and not self.shared):
            imports = self.z3_generate_imports()  # parent
            config = self.z3_generate_config()
            z3_abs_function = self.z3_generate_z3_abs_function()  # parent
            input_variables_declaration = self.z3_generate_declare_input_variables()
            exact_integer_function_declaration = self.z3_generate_declare_integer_function(F_EXACT)
            approximate_integer_function_declaration = self.z3_generate_declare_integer_function(F_APPROXIMATE)
            utility_variables = self.z3_generate_utility_variables()
            implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters_subxpat()
            exact_circuit_wires_declaration = self.z3_generate_exact_circuit_wires_declaration()
            approximate_circuit_wires_declaration = self.z3_generate_approximate_circuit_wires_declaration_subxpat()

            exact_circuit_outputs_declaration = self.z3_generate_exact_circuit_outputs_declaration()
            approximate_circuit_outputs_declaration = self.z3_generate_approximate_circuit_outputs_declaration()

            exact_circuit_constraints = self.z3_generate_exact_circuit_constraints()
            approximate_circuit_constraints_subxpat = self.z3_generate_approximate_circuit_constraints_subxpat()

            for_all_solver = self.z3_generate_forall_solver_subxpat()
            verification_solver = self.z3_generate_verification_solver()
            parameter_constraint_list = self.z3_generate_parameter_constraint_list()
            find_wanted_number_of_models = self.z3_generate_find_wanted_number_of_models()
            store_data = self.z3_generate_store_data()
            self.z3pyscript = imports + config + z3_abs_function + input_variables_declaration + exact_integer_function_declaration + approximate_integer_function_declaration \
                + utility_variables + implicit_parameters_declaration + exact_circuit_wires_declaration \
                + approximate_circuit_wires_declaration \
                + exact_circuit_outputs_declaration \
                + approximate_circuit_outputs_declaration \
                + exact_circuit_constraints + approximate_circuit_constraints_subxpat \
                + for_all_solver + verification_solver + parameter_constraint_list + find_wanted_number_of_models \
                + store_data
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
        input_variables += f'# Inputs variables declaration\n'
        for inp_key in self.exact_graph.input_dict.keys():
            input_variables += self.declare_gate(inp_key, self.exact_graph.input_dict)
        input_variables += '\n'
        return input_variables

    def z3_generate_declare_integer_function(self, function_name):
        integer_function = ''
        integer_function += f'# Integer function declaration\n'
        temp_arg_list = ', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))
        temp_arg_list += ', ' + INTSORT
        integer_function += f"{function_name} = {FUNCTION}('{function_name}', {temp_arg_list})\n"
        return integer_function

    def z3_generate_utility_variables(self):
        utility_variables = ''
        utility_variables += f'# utility variables'
        utility_variables += f"\n" \
                             f"difference = z3_abs({F_EXACT}({', '.join(self.exact_graph.input_dict.values())}) - " \
                             f"{F_APPROXIMATE}({', '.join(self.exact_graph.input_dict.values())})" \
                             f")\n" \
                             f"error = {Z3INT}('error')\n"

        utility_variables += '\n'
        return utility_variables

    def z3_generate_o(self):
        temp_o = ''
        for idx in range(self.current_graph.num_outputs):
            temp_name = f'{PRODUCT_PREFIX}{idx}'
            temp_o += self.declare_gate(temp_name)
        return temp_o

    def z3_generate_oti(self):
        temp_oti = ''
        for o_idx in range(self.current_graph.num_outputs):
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.current_graph.num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    temp_oti += self.declare_gate(p_s)
                    temp_oti += self.declare_gate(p_l)
        return temp_oti

    def z3_generate_declare_implicit_parameters(self):
        implicit_parameters = ''
        implicit_parameters += f'# Parameters variables declaration\n'
        implicit_parameters += self.z3_generate_o()
        implicit_parameters += self.z3_generate_oti()
        implicit_parameters += '\n'
        return implicit_parameters

    def z3_generate_o_subxpat(self):
        temp_o = ''
        for idx in range(self.current_graph.subgraph_num_outputs):
            temp_name = f'{PRODUCT_PREFIX}{idx}'
            temp_o += self.declare_gate(temp_name)
        return temp_o

    def z3_generate_oti_subxpat(self):
        temp_oti = ''
        for o_idx in range(self.current_graph.subgraph_num_outputs):
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.current_graph.subgraph_num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    temp_oti += self.declare_gate(p_s)
                    temp_oti += self.declare_gate(p_l)
        return temp_oti

    def z3_generate_declare_implicit_parameters_subxpat(self):
        implicit_parameters = ''
        implicit_parameters += f'# Parameters variables declaration\n'
        implicit_parameters += self.z3_generate_o_subxpat()
        implicit_parameters += self.z3_generate_oti_subxpat()
        implicit_parameters += '\n'
        return implicit_parameters

    def z3_generate_exact_circuit_wires_declaration(self):
        exact_wires_declaration = ''
        exact_wires_declaration += f'# wires functions declaration for exact circuit\n'

        for g_idx in self.exact_graph.gate_dict:
            exact_wires_declaration += f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))}" \
                                       f", {BOOLSORT}" \
                                       f")\n"

        for g_idx in self.exact_graph.constant_dict:
            # print(f'{g_idx = }')
            exact_wires_declaration += f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))}" \
                                       f", {BOOLSORT}" \
                                       f")\n"
        exact_wires_declaration += '\n'
        return exact_wires_declaration

    def z3_generate_approximate_circuit_wires_declaration_subxpat(self):
        approximate_wires_declaration = ''
        approximate_wires_declaration += f'# wires functions declaration for approximate circuit\n'
        # TODO:
        # Fix when PIs are not the subgrpah's inputs

        gate_key_list = list(self.current_graph.gate_dict.keys())
        constant_key_list = list(self.current_graph.constant_dict.keys())
        # gates
        for g_idx in gate_key_list:
            g_label = self.current_graph.gate_dict[g_idx]
            if self.current_graph.is_subgraph_member(g_label):
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.subgraph_num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
            else:
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
        # constants
        for g_idx in constant_key_list:
            g_label = self.current_graph.constant_dict[g_idx]
            if self.current_graph.is_subgraph_member(g_label):
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.subgraph_num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
            else:
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
        approximate_wires_declaration += '\n'
        return approximate_wires_declaration

    def z3_generate_approximate_circuit_wires_declaration(self):
        exact_wires_declaration = ''
        exact_wires_declaration += f'# wires functions declaration for approximate circuit\n'
        # TODO:
        # Fix when PIs are not the subgrpah's inputs
        for g_idx in range(self.current_graph.num_gates):
            exact_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.subgraph_num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.current_graph.subgraph_num_inputs))}" \
                                       f", {BOOLSORT}" \
                                       f")\n"
        exact_wires_declaration += '\n'
        return exact_wires_declaration

    def z3_generate_exact_circuit_outputs_declaration(self):
        exact_circuit_output_declaration = ''
        exact_circuit_output_declaration += f'# outputs functions declaration for exact circuit\n'
        for output_idx in range(self.current_graph.num_outputs):
            exact_circuit_output_declaration += f"{EXACT_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{EXACT_OUTPUT_PREFIX}{OUT}{output_idx}', " \
                                                f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs + 1))}" \
                                                f")\n"
        exact_circuit_output_declaration += '\n'
        return exact_circuit_output_declaration

    def z3_generate_approximate_circuit_outputs_declaration(self):
        approximate_circuit_output_declaration = ''
        approximate_circuit_output_declaration = f'# outputs functions declaration for approximate circuit\n'
        # for output_idx in range(self.graph.subgraph_num_outputs):
        for output_idx in range(self.current_graph.num_outputs):
            approximate_circuit_output_declaration += f"{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx}', " \
                                                      f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs + 1))}" \
                                                      f")\n"
            # approximate_circuit_output_declaration += f"{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx}', " \
            #                                           f"{', '.join(repeat(BOOLSORT, self.graph.num_inputs + 1))}" \
            #                                           f")\n"
        approximate_circuit_output_declaration += '\n'
        return approximate_circuit_output_declaration

    def get_predecessors(self, node: str) -> List[str]:
        return list(self.exact_graph.graph.predecessors(node))

    def get_logical_function(self, node: str) -> str:
        return self.exact_graph.graph.nodes[node][LABEL]

    def get_predecessors_xpat(self, node: str) -> List[str]:
        return list(self.current_graph.subgraph.predecessors(node))

    def get_logical_function_xpat(self, node: str) -> str:
        return self.current_graph.subgraph.nodes[node][LABEL]

    def z3_express_node_as_wire_constraints(self, node: str):
        # print(f'{self.exact_graph.graph.nodes = }')
        assert node in list(self.exact_graph.input_dict.values()) or node in list(self.exact_graph.gate_dict.values()) \
            or node in list(self.exact_graph.output_dict.values()) or node in list(self.exact_graph.constant_dict.values())

        if node in list(self.exact_graph.input_dict.values()):
            return node
        elif node in list(self.exact_graph.gate_dict.values()):
            node_id = -1
            for key in self.exact_graph.gate_dict.keys():
                if self.exact_graph.gate_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + node_id}({','.join(list(self.exact_graph.input_dict.values()))})"
        elif node in list(self.exact_graph.output_dict.values()):
            for key in self.exact_graph.output_dict.keys():
                if self.exact_graph.output_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{OUT}{node_id}({','.join(list(self.exact_graph.input_dict.values()))})"
        elif node in list(self.exact_graph.constant_dict.values()):
            # print(f'{self.current_graph.graph.nodes[node] = }')
            return Z3_GATES_DICTIONARY[self.exact_graph.graph.nodes[node][LABEL]]

    def __z3_get_approximate_label(self, node: str):
        graph_gates = list(self.current_graph.gate_dict.values())

        if node in list(self.current_graph.gate_dict.values()):
            for gate_idx in self.current_graph.gate_dict.keys():
                if self.current_graph.gate_dict[gate_idx] == node:
                    return f'{APPROXIMATE_WIRE_PREFIX}{gate_idx + self.current_graph.num_inputs}'
        else:
            return node

    def __z3_get_subgraph_input_list(self):
        input_list = list(self.current_graph.subgraph_input_dict.values())
        input_list_tmp = list(self.current_graph.subgraph_input_dict.values())

        input_list_tmp = self.__fix_order()
        for idx, inp in enumerate(input_list):
            if inp in self.current_graph.gate_dict.values():
                input_list_tmp[
                    idx] = f"{self.__z3_get_approximate_label(inp)}({', '.join(list(self.current_graph.input_dict.values()))})"
        return input_list_tmp

    def __fix_order(self):
        subpgraph_input_list = list(self.current_graph.subgraph_input_dict.values())
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

    def z3_express_node_as_wire_constraints_subxpat(self, node: str):
        # print(f'We are checking this node!')

        # print(f'{self.current_graph.input_dict.values() = }')
        # print(f'{self.current_graph.gate_dict.values() = }')
        # print(f'{self.current_graph.output_dict.values() = }')
        assert node in list(self.current_graph.input_dict.values()) or node in list(
            self.current_graph.gate_dict.values()) \
            or node in list(self.current_graph.output_dict.values()) or node in list(
            self.current_graph.constant_dict.values()) \
            or node.startswith(APPROXIMATE_WIRE_PREFIX)

        if node in list(self.current_graph.input_dict.values()):
            return node
        elif node in list(self.current_graph.gate_dict.values()):
            if self.current_graph.is_subgraph_member(node):
                node_id = -1
                for key in self.current_graph.gate_dict.keys():
                    if self.current_graph.gate_dict[key] == node:
                        node_id = key

                input_list = self.__z3_get_subgraph_input_list()
                # print(f'for the subgraph = {input_list}')
                return f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + node_id}({','.join(input_list)})"
            else:
                node_id = -1
                for key in self.current_graph.gate_dict.keys():
                    if self.current_graph.gate_dict[key] == node:
                        node_id = key
                return f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + node_id}({','.join(list(self.current_graph.input_dict.values()))})"
        elif node in list(self.current_graph.output_dict.values()):
            for key in self.current_graph.output_dict.keys():
                if self.current_graph.output_dict[key] == node:
                    node_id = key
            return f"{APPROXIMATE_WIRE_PREFIX}{OUT}{node_id}({','.join(list(self.current_graph.input_dict.values()))})"
        elif node in list(self.current_graph.constant_dict.values()):
            # print(f'{self.current_graph.graph.nodes[node] = }')
            return Z3_GATES_DICTIONARY[self.current_graph.graph.nodes[node][LABEL]]

    def z3_generate_exact_circuit_wire_constraints(self):
        exact_wire_constraints = ''
        exact_wire_constraints += f'# exact circuit constraints\n'
        exact_wire_constraints += f'{EXACT_CIRCUIT} = And(\n'
        exact_wire_constraints += f'{TAB}# wires\n'

        for g_idx in self.exact_graph.gate_dict:

            g_label = self.exact_graph.gate_dict[g_idx]
            g_predecessors = self.get_predecessors(g_label)
            g_function = self.get_logical_function(g_label)

            assert len(g_predecessors) == 1 or len(g_predecessors) == 2
            assert g_function == NOT or g_function == AND or g_function == OR
            if len(g_predecessors) == 1:
                if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:

                    pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
            else:
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

                if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:
                    pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])
                if g_predecessors[1] in list(self.exact_graph.input_dict.values()):
                    pred_2 = g_predecessors[1]
                else:
                    pred_2 = self.z3_express_node_as_wire_constraints(g_predecessors[1])

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
        return exact_wire_constraints

    def z3_generate_exact_circuit_output_constraints(self):
        exact_output_constraints = ''
        exact_output_constraints += f'{TAB}# boolean outputs (from the least significant)\n'
        for output_idx in self.exact_graph.output_dict.keys():
            output_label = self.exact_graph.output_dict[output_idx]
            output_predecessors = list(self.exact_graph.graph.predecessors(output_label))
            assert len(output_predecessors) == 1

            pred = self.z3_express_node_as_wire_constraints(output_predecessors[0])
            output = self.z3_express_node_as_wire_constraints(output_label)
            exact_output_constraints += f'{TAB}{output} == {pred},\n'
        return exact_output_constraints

    def z3_generate_exact_circuit_integer_output_constraints(self):
        exact_integer_outputs = ''
        exact_integer_outputs += f'{TAB}# exact_integer_outputs\n'
        exact_integer_outputs += f"{TAB}{F_EXACT}({','.join(self.current_graph.input_dict.values())}) == \n"

        for idx in range(self.current_graph.num_outputs):
            output_label = self.current_graph.output_dict[idx]
            if idx == self.current_graph.num_outputs - 1:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints(output_label)},\n"
            else:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints(output_label)} +\n"
        return exact_integer_outputs

    def z3_generate_approximate_circuit_wire_constraints_subxpat(self):
        exact_wire_constraints = ''
        exact_wire_constraints += f'# approximate circuit constraints\n'
        exact_wire_constraints += f'{APPROXIMATE_CIRCUIT} = And(\n'
        exact_wire_constraints += f'{TAB}# wires\n'
        subgraph_input_list = self.__z3_get_subgraph_input_list()
        # print(f'{subgraph_input_list = }')
        gate_key_list = list(self.current_graph.gate_dict.keys())
        for g_idx in gate_key_list:
            g_label = self.current_graph.gate_dict[g_idx]
            # print(f'{g_label = }')
            if not self.current_graph.is_subgraph_member(g_label):
                g_predecessors = self.get_predecessors_xpat(g_label)
                # print(f'{g_predecessors = }')
                g_function = self.get_logical_function_xpat(g_label)
                assert len(g_predecessors) == 1 or len(g_predecessors) == 2
                assert g_function == NOT or g_function == AND or g_function == OR
                if len(g_predecessors) == 1:
                    if g_predecessors[0] in list(self.current_graph.input_dict.values()):
                        pred_1 = g_predecessors[0]
                    else:
                        pred_1 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[0])

                    exact_wire_constraints += f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                              f"{','.join(list(self.current_graph.input_dict.values()))}) == "
                    exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
                else:
                    exact_wire_constraints += f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                              f"{','.join(list(self.current_graph.input_dict.values()))}) == "
                    if g_predecessors[0] in list(self.current_graph.input_dict.values()):
                        pred_1 = g_predecessors[0]
                    else:
                        pred_1 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[0])
                    if g_predecessors[1] in list(self.current_graph.input_dict.values()):
                        pred_2 = g_predecessors[1]
                    else:
                        pred_2 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[1])
                    exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
            # if the gate is an output node of the annotated graph (subgraph)
            elif self.current_graph.is_subgraph_member(g_label) and self.current_graph.is_subgraph_output(g_label):

                output_list = list(self.current_graph.subgraph_output_dict.values())
                output_idx = output_list.index(g_label)

                exact_wire_constraints += f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                          f"{','.join(subgraph_input_list)}) == "
                exact_wire_constraints += f"{Z3_AND}({PRODUCT_PREFIX}{output_idx}, {Z3_OR}("
                for ppo_idx in range(self.ppo):
                    exact_wire_constraints += f"{Z3_AND}("
                    for input_idx, input_label in enumerate(self.current_graph.subgraph_input_dict.values()):
                        max_input_id = self.current_graph.subgraph_num_inputs - 1
                        p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                        p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                        loop_2_last_iter_flg = (ppo_idx == self.ppo - 1)
                        loop_3_last_iter_flg = (input_idx == self.current_graph.subgraph_num_inputs - 1)

                        exact_wire_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {subgraph_input_list[input_idx]})'

                        if loop_2_last_iter_flg and loop_3_last_iter_flg:
                            exact_wire_constraints += f'))),\n'
                        elif loop_3_last_iter_flg:
                            exact_wire_constraints += f'), '
                        else:
                            exact_wire_constraints += ', '

        return exact_wire_constraints

    def z3_generate_approximate_circuit_output_constraints_subxpat(self):
        approximate_output_constraints = ''
        approximate_output_constraints += f'{TAB}# boolean outputs (from the least significant)\n'

        for output_idx in self.current_graph.output_dict.keys():
            output_label = self.current_graph.output_dict[output_idx]
            output_predecessors = list(self.current_graph.graph.predecessors(output_label))

            assert len(output_predecessors) == 1
            # print(f'{self.current_graph.subgraph_gate_dict = }')
            # print(f'{self.current_graph.graph.nodes = }')
            # print(f'{output_predecessors = }')
            pred = self.z3_express_node_as_wire_constraints_subxpat(output_predecessors[0])
            output = self.z3_express_node_as_wire_constraints_subxpat(output_label)
            approximate_output_constraints += f'{TAB}{output} == {pred},\n'
        return approximate_output_constraints

    def z3_generate_exact_circuit_integer_output_constraints_subxpat(self):
        exact_integer_outputs = ''
        exact_integer_outputs += f'{TAB}# approximate_integer_outputs\n'
        exact_integer_outputs += f"{TAB}{F_APPROXIMATE}({','.join(self.current_graph.input_dict.values())}) == \n"

        for idx in range(self.current_graph.num_outputs):
            output_label = self.current_graph.output_dict[idx]
            if idx == self.current_graph.num_outputs - 1:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat(output_label)},\n"
            else:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat(output_label)} +\n"
        return exact_integer_outputs

    def z3_generate_exact_circuit_constraints(self):
        wires = self.z3_generate_exact_circuit_wire_constraints()
        outputs = self.z3_generate_exact_circuit_output_constraints()
        integer_outputs = self.z3_generate_exact_circuit_integer_output_constraints()
        wires += '\n'
        outputs += '\n'
        integer_outputs += '\n'
        exact_circuit_constraints = wires + outputs + integer_outputs + ')\n'

        return exact_circuit_constraints

    def z3_generate_approximate_circuit_constraints(self):
        approximate_circuit_constraints = ''
        approximate_circuit_constraints += f'# Approximate circuit\n'
        approximate_circuit_constraints += f'# constraints\n'
        approximate_circuit_constraints += f'{APPROXIMATE_CIRCUIT} = {Z3_AND}(\n'
        approximate_circuit_constraints += f"{TAB}{F_APPROXIMATE}({','.join(self.current_graph.input_dict.values())}) == \n"
        approximate_circuit_constraints += f"{TAB}{SUM}("
        for o_idx in range(self.current_graph.num_outputs):
            if o_idx > 0:
                approximate_circuit_constraints += f"{TAB}{TAB}"  # fixing the indentations
            approximate_circuit_constraints += f"{INTVAL}({2 ** o_idx}) * {Z3_AND} ( {PRODUCT_PREFIX}{o_idx}, {Z3_OR}({Z3_AND}("
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.current_graph.num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                    loop_1_last_iter_flg = o_idx == self.current_graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.current_graph.num_inputs - 1

                    approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {self.current_graph.input_dict[input_idx]})'

                    if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
                        approximate_circuit_constraints += '))))\n)\n'
                    elif loop_3_last_iter_flg and loop_2_last_iter_flg:
                        approximate_circuit_constraints += '))),\n'
                    else:
                        approximate_circuit_constraints += ','
        return approximate_circuit_constraints

    def z3_generate_approximate_circuit_constraints_subxpat(self):
        wires = self.z3_generate_approximate_circuit_wire_constraints_subxpat() + '\n'
        outputs = self.z3_generate_approximate_circuit_output_constraints_subxpat() + '\n'
        integer_outputs = self.z3_generate_exact_circuit_integer_output_constraints_subxpat() + '\n'
        approximate_circuit_constraints = wires + outputs + integer_outputs + ')\n'

        return approximate_circuit_constraints

    def z3_generate_forall_solver(self):
        prep = self.z3_generate_forall_solver_preperation() + '\n'
        error = self.z3_generate_forall_solver_error_constraint() + '\n'
        circuits = self.z3_generate_forall_solver_circuits() + '\n'
        atmost_constraints = self.z3_generate_forall_solver_atmost_constraints() + '\n'
        redundancy_constraints = self.z3_generate_forall_solver_redundancy_constraints() + '\n'
        forall_solver = prep + error + circuits + atmost_constraints + redundancy_constraints
        return forall_solver

    def z3_generate_forall_solver_subxpat(self):
        prep = self.z3_generate_forall_solver_preperation() + '\n'
        error = self.z3_generate_forall_solver_error_constraint() + '\n'
        circuits = self.z3_generate_forall_solver_circuits() + '\n'
        atmost_constraints = self.z3_generate_forall_solver_atmost_constraints_subxpat() + '\n'
        redundancy_constraints = self.z3_generate_forall_solver_redundancy_constraints_subxpat() + '\n'
        forall_solver = prep + error + circuits + atmost_constraints + redundancy_constraints
        return forall_solver

    def z3_generate_forall_solver_preperation(self):
        prep = ''
        prep += '# forall solver\n'
        prep += f'{FORALL_SOLVER} = {SOLVER}\n' \
                f'{FORALL_SOLVER}.{ADD}({FORALL}(\n' \
                f"{TAB}[{','.join(list(self.current_graph.input_dict.values()))}],\n" \
                f"{TAB}{Z3_AND}(\n"
        return prep

    def z3_generate_forall_solver_error_constraint(self):
        error = ''
        error += f'{TAB}{TAB}# error constraints\n'
        error += f'{TAB}{TAB}{DIFFERENCE} <= {ET},\n'
        return error

    def z3_generate_forall_solver_circuits(self):
        circuits = ''
        circuits += f'{TAB}{TAB}# circuits\n'
        circuits += f'{TAB}{TAB}{EXACT_CIRCUIT},\n' \
                    f'{TAB}{TAB}{APPROXIMATE_CIRCUIT},\n'
        return circuits

    def z3_generate_forall_solver_atmost_constraints(self, *, relevant_inputs_num: int = None, relevant_outputs_num: int = None):
        relevant_inputs_num = self.current_graph.num_inputs if relevant_inputs_num is None else relevant_inputs_num
        relevant_outputs_num = self.current_graph.num_outputs if relevant_outputs_num is None else relevant_outputs_num

        atmost = ''
        atmost += f'{TAB}{TAB}# AtMost constraints\n'

        for output_idx in range(relevant_outputs_num):
            for ppo_idx in range(self.ppo):
                atmost += f"{TAB}{TAB}("
                for input_idx in range(relevant_inputs_num):

                    loop_1_last_iter_flg = output_idx == relevant_outputs_num - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == relevant_inputs_num - 1

                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    atmost += f"{IF}({p_s}, 1, 0)"

                    if loop_3_last_iter_flg:
                        atmost += f') <= {self.lpp},\n'
                    else:
                        atmost += f' + '
        atmost += '\n'

        return atmost

    def z3_generate_forall_solver_atmost_constraints_subxpat(self):
        return self.z3_generate_forall_solver_atmost_constraints(
            relevant_inputs_num=self.current_graph.subgraph_num_inputs,
            relevant_outputs_num=self.current_graph.subgraph_num_outputs,
        )

    def z3_generate_forall_solver_redundancy_constraints_subxpat(self):
        redundancy = ''
        redundancy += f'{TAB}{TAB}# Redundancy constraints\n'
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care_subxpat() + '\n'
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_subxpat() + '\n'
        set_ppo_order = self.z3_generate_forall_solver_redundancy_constraints_set_ppo_order_subxpat() + '\n'

        end = f"{TAB})\n))\n"
        redundancy += double_no_care + remove_constant_zero_permutation + set_ppo_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints(self):
        redundancy = ''
        redundancy += f'{TAB}{TAB}# Redundancy constraints\n'
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care() + '\n'
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation() + '\n'
        set_ppo_order = self.z3_generate_forall_solver_redundancy_constraints_set_ppo_order() + '\n'

        end = f"{TAB})\n))\n"
        redundancy += double_no_care + remove_constant_zero_permutation + set_ppo_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints_double_no_care_subxpat(self):
        return self.z3_generate_forall_solver_redundancy_constraints_double_no_care(
            relevant_inputs_num=self.current_graph.subgraph_num_inputs,
            relevant_outputs_num=self.current_graph.subgraph_num_outputs,
        )

    def z3_generate_forall_solver_redundancy_constraints_double_no_care(self, *, relevant_inputs_num: int = None, relevant_outputs_num: int = None):
        relevant_inputs_num = self.current_graph.num_inputs if relevant_inputs_num is None else relevant_inputs_num
        relevant_outputs_num = self.current_graph.num_outputs if relevant_outputs_num is None else relevant_outputs_num

        double = ''
        double += f'{TAB}{TAB}# remove double no-care\n'
        for output_idx in range(relevant_outputs_num):
            double += f"{TAB}{TAB}"
            for ppo_idx in range(self.ppo):
                for input_idx in range(relevant_inputs_num):

                    loop_1_last_iter_flg = output_idx == relevant_outputs_num - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == relevant_inputs_num - 1

                    p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    double += f'{IMPLIES}({p_l}, {p_s}), '

                    if loop_2_last_iter_flg and loop_3_last_iter_flg:
                        double += f'\n'

        return double

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_subxpat(self):
        return self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation(
            relevant_inputs_num=self.current_graph.subgraph_num_inputs,
            relevant_outputs_num=self.current_graph.subgraph_num_outputs,
        )

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation(self, *, relevant_inputs_num: int = None, relevant_outputs_num: int = None):
        relevant_inputs_num = self.current_graph.num_inputs if relevant_inputs_num is None else relevant_inputs_num
        relevant_outputs_num = self.current_graph.num_outputs if relevant_outputs_num is None else relevant_outputs_num

        const_zero_perm = ''
        const_zero_perm += f'{TAB}{TAB}# remove constant 0 parameters permutations\n'
        for output_idx in range(relevant_outputs_num):
            const_zero_perm += f"{TAB}{TAB}{IMPLIES}({Z3_NOT}({PRODUCT_PREFIX}{output_idx}), {Z3_NOT}({Z3_OR}("
            for ppo_idx in range(self.ppo):
                for input_idx in range(relevant_inputs_num):

                    loop_1_last_iter_flg = output_idx == relevant_outputs_num - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == relevant_inputs_num - 1

                    p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'

                    const_zero_perm += f'{p_s}, {p_l}'
                    if loop_2_last_iter_flg and loop_3_last_iter_flg:
                        const_zero_perm += f'))),\n'
                    else:
                        const_zero_perm += f', '

        return const_zero_perm

    def z3_generate_forall_solver_redundancy_constraints_set_ppo_order_subxpat(self):
        return self.z3_generate_forall_solver_redundancy_constraints_set_ppo_order(
            relevant_inputs_num=self.current_graph.subgraph_num_inputs,
            relevant_outputs_num=self.current_graph.subgraph_num_outputs,
        )

    def z3_generate_forall_solver_redundancy_constraints_set_ppo_order(self, *, relevant_inputs_num: int = None, relevant_outputs_num: int = None):
        relevant_inputs_num = self.current_graph.num_inputs if relevant_inputs_num is None else relevant_inputs_num
        relevant_outputs_num = self.current_graph.num_outputs if relevant_outputs_num is None else relevant_outputs_num

        ppo_order = ''
        ppo_order += f'{TAB}{TAB}# set order of trees\n'

        if self.ppo == 1:
            # print(f'No need for ordering the PPOs!')
            ppo_order += f'{TAB}{TAB}True, \n'
        else:
            for output_idx in range(relevant_outputs_num):
                for ppo_idx in range(self.ppo - 1):

                    current_product = f'{TAB}{TAB}('
                    next_product = f'('
                    for input_idx in range(relevant_inputs_num):

                        loop_1_last_iter_flg = output_idx == self.current_graph.num_outputs - 1
                        loop_2_last_iter_flg = ppo_idx == self.ppo - 2
                        loop_3_last_iter_flg = input_idx == self.current_graph.num_inputs - 1

                        p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                        p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'

                        p_l_next = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx + 1}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                        p_s_next = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx + 1}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'

                        current_product += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'
                        next_product += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s_next} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l_next}'

                        if loop_3_last_iter_flg:
                            current_product += ')'
                            next_product += '),\n'
                            ppo_order += f'{current_product} >= {next_product}'
                        else:
                            current_product += f' + '
                            next_product += f' + '

        return ppo_order

    def z3_generate_verification_solver(self):
        verficiation_solver = ''
        verficiation_solver += f'{VERIFICATION_SOLVER} = {SOLVER}\n' \
                               f'{VERIFICATION_SOLVER}.{ADD}(\n' \
                               f'{TAB}{ERROR} == {DIFFERENCE},\n' \
                               f'{TAB}{EXACT_CIRCUIT},\n' \
                               f'{TAB}{APPROXIMATE_CIRCUIT},\n' \
                               f')\n'
        return verficiation_solver

    def z3_generate_parameter_constraint_list(self):
        parameter_list = ''
        parameter_list += f'parameters_constraints: List[Tuple[BoolRef, bool]] = []\n'
        return parameter_list

    def z3_generate_find_wanted_number_of_models(self):
        prep_loop1 = self.z3_generate_find_wanted_number_of_models_prep_loop1() + '\n'
        prep_loop2 = self.z3_generate_find_wanted_number_of_models_prep_loop2() + '\n'
        prep_loop3 = self.z3_generate_find_wanted_number_of_models_prep_loop3() + '\n'
        final_prep = self.z3_generate_find_wanted_number_of_models_final_prep() + '\n'
        find_wanted_number_of_models = prep_loop1 + prep_loop2 + prep_loop3 + final_prep
        return find_wanted_number_of_models

    def z3_generate_find_wanted_number_of_models_prep_loop1(self):
        prep_loop1 = ''
        prep_loop1 += f'found_data = []\n' \
                      f'while(len(found_data) < wanted_models and timeout > 0):\n' \
                      f'{TAB}time_total_start = time()\n' \
                      f'{TAB}\n' \
                      f'{TAB}attempts = 1\n' \
                      f'{TAB}result: CheckSatResult = None\n' \
                      f'{TAB}attempts_times: List[Tuple[float, float, float]] = []\n'

        return prep_loop1

    def z3_generate_find_wanted_number_of_models_prep_loop2(self):
        find_valid_model = ''
        find_valid_model += f'{TAB}while result != sat:\n' \
                            f'{TAB}{TAB}time_attempt_start = time()\n' \
                            f'{TAB}{TAB}time_parameters_start = time_attempt_start\n'

        find_valid_model += f'{TAB}{TAB}# add constrain to prevent the same parameters to happen\n' \
                            f'{TAB}{TAB}if parameters_constraints:\n' \
                            f'{TAB}{TAB}{TAB}forall_solver.add(Or(*map(lambda x: x[0] != x[1], parameters_constraints)))\n'

        find_valid_model += f'{TAB}{TAB}parameters_constraints = []\n'
        find_valid_model += f"{TAB}{TAB}forall_solver.set(\"timeout\", int(timeout * 1000))\n" \
                            f"{TAB}{TAB}result = forall_solver.check()\n" \
                            f"{TAB}{TAB}time_parameters = time() - time_attempt_start\n" \
                            f"{TAB}{TAB}time_attempt = time() - time_attempt_start\n" \
                            f"{TAB}{TAB}timeout -= time_parameters # removed the time used from the timeout\n"
        find_valid_model += f'{TAB}{TAB}if result != sat:\n' \
                            f'{TAB}{TAB}{TAB}attempts_times.append((time_attempt, time_parameters, None))\n' \
                            f'{TAB}{TAB}{TAB}break\n'
        find_valid_model += f'{TAB}{TAB}m = forall_solver.model()\n' \
                            f'{TAB}{TAB}parameters_constraints = []\n' \
                            f'{TAB}{TAB}for k, v in map(lambda k: (k, m[k]), m):\n' \
                            f'{TAB}{TAB}{TAB}if str(k)[0] == "p":\n' \
                            f'{TAB}{TAB}{TAB}{TAB}parameters_constraints.append((Bool(str(k)), v))\n'

        find_valid_model += f'{TAB}{TAB}# verify parameters\n' \
                            f'{TAB}{TAB}WCE: int = None\n' \
                            f'{TAB}{TAB}verification_ET: int = 0\n' \
                            f'{TAB}{TAB}time_verification_start = time()\n' \
                            f'{TAB}{TAB}# save state\n' \
                            f'{TAB}{TAB}verification_solver.push()\n' \
                            f'{TAB}{TAB}# parameters constraints\n' \
                            f'{TAB}{TAB}verification_solver.add(\n' \
                            f'{TAB}{TAB}{TAB}*map(lambda x: x[0] == x[1], parameters_constraints),\n' \
                            f'{TAB}{TAB})\n'

        return find_valid_model

    def z3_generate_find_wanted_number_of_models_prep_loop3(self):
        prep_loop3 = f'{TAB}{TAB}while verification_ET < max_possible_ET:\n' \
                     f'{TAB}{TAB}{TAB}# add constraint\n' \
                     f'{TAB}{TAB}{TAB}verification_solver.add(difference > verification_ET)\n' \
                     f'{TAB}{TAB}{TAB}# run solver\n' \
                     f'{TAB}{TAB}{TAB}verification_solver.set("timeout", int(timeout * 1000))\n' \
                     f'{TAB}{TAB}{TAB}v_result = verification_solver.check()\n'

        prep_loop3 += f'{TAB}{TAB}{TAB}if v_result == unsat:\n' \
                      f'{TAB}{TAB}{TAB}{TAB}# unsat, WCE found\n' \
                      f'{TAB}{TAB}{TAB}{TAB}WCE = verification_ET\n' \
                      f'{TAB}{TAB}{TAB}{TAB}break\n'

        prep_loop3 += f'{TAB}{TAB}{TAB}elif v_result == sat:\n' \
                      f'{TAB}{TAB}{TAB}{TAB}# sat, need to search again\n' \
                      f'{TAB}{TAB}{TAB}{TAB}m = verification_solver.model()\n' \
                      f'{TAB}{TAB}{TAB}{TAB}verification_ET = m[error].as_long()\n' \
                      f'{TAB}{TAB}{TAB}else:\n' \
                      f'{TAB}{TAB}{TAB}{TAB} # unknown (probably a timeout)\n' \
                      f'{TAB}{TAB}{TAB}{TAB}WCE = -1\n' \
                      f'{TAB}{TAB}{TAB}{TAB}break\n'

        return prep_loop3

    def z3_generate_find_wanted_number_of_models_final_prep(self):
        final_prep = ''
        final_prep += f'{TAB}{TAB}if WCE is None:\n' \
                      f'{TAB}{TAB}{TAB}WCE = max_possible_ET\n'

        final_prep += f'{TAB}{TAB}# revert state\n' \
                      f'{TAB}{TAB}verification_solver.pop()\n' \
                      f'{TAB}{TAB}time_verification = time() - time_verification_start\n' \
                      f'{TAB}{TAB}time_attempt = time() - time_attempt_start\n' \
                      f'{TAB}{TAB}timeout -= time_verification  # remove the time used from the timeout\n' \
                      f'{TAB}{TAB}attempts_times.append((time_attempt, time_parameters, time_verification))\n' \
                      f'{TAB}{TAB}\n'

        final_prep += f'{TAB}{TAB}# ==== continue or exit\n' \
                      f'{TAB}{TAB}if WCE > ET:\n' \
                      f"{TAB}{TAB}{TAB}# Z3 hates us and decided it doesn't like being appreciated\n" \
                      f'{TAB}{TAB}{TAB}result = None\n' \
                      f'{TAB}{TAB}{TAB}attempts += 1\n' \
                      f'{TAB}{TAB}{TAB}invalid_parameters = parameters_constraints\n' \
                      f'{TAB}{TAB}elif WCE < 0:  # caused by unknown\n' \
                      f'{TAB}{TAB}{TAB}break\n'

        return final_prep

    def z3_generate_store_data(self):
        store_data = ''
        store_data += f'{TAB}# store data\n'
        extract_info = self.z3_generate_store_data_define_extract_info_function()
        key_function = self.z3_generate_store_data_define_extract_key_function()
        stats = self.z3_generate_stats()
        results = self.z3_dump_results_onto_json()
        extract_info += '\n'
        key_function += '\n'
        stats += '\n'
        results += '\n'
        store_data += extract_info + key_function + stats + results
        return store_data

    def z3_generate_store_data_define_extract_info_function(self):
        extract_info = ''
        extract_info += f'{TAB}def extract_info(pattern: Union[Pattern, str], string: str,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}parser: Callable[[Any], Any] = lambda x: x,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}default: Union[Callable[[], None], Any] = None) -> Any:\n' \
                        f'{TAB}{TAB}import re\n' \
                        f'{TAB}{TAB}return (parser(match[1]) if (match := re.search(pattern, string))\n' \
                        f'{TAB}{TAB}{TAB}{TAB}else (default() if callable(default) else default))\n'

        return extract_info

    def z3_generate_store_data_define_extract_key_function(self):
        """
        Blah Blah Blah
        :return:
        """
        key_function = ''
        key_function += f"{TAB}def key_function(parameter_constraint):\n" \
                        f'{TAB}{TAB}p = str(parameter_constraint[0])\n' \
                        f"{TAB}{TAB}o_id = extract_info(r'_o(\d+)', p, int, -1)\n" \
                        f"{TAB}{TAB}t_id = extract_info(r'_t(\d+)', p, int, 0)\n" \
                        f"{TAB}{TAB}i_id = extract_info(r'_i(\d+)', p, int, 0)\n" \
                        f"{TAB}{TAB}typ = extract_info(r'_(l|s)', p, {{'s': 1, 'l': 2}}.get, 0)\n" \
                        f'{TAB}{TAB}if o_id < 0:\n' \
                        f'{TAB}{TAB}{TAB}return 0\n' \
                        f'{TAB}{TAB}return (o_id * 100000\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ t_id * 1000\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ i_id * 10\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ typ)\n'

        return key_function

    def z3_generate_stats(self):
        stats = ''
        stats += f'{TAB}time_total = time() - time_total_start\n'
        stats += f'{TAB}data_object = {{\n' \
                 f"{TAB}{TAB}'result': str(result),\n" \
                 f"{TAB}{TAB}'total_time': time_total,\n" \
                 f"{TAB}{TAB}'attempts': attempts,\n" \
                 f"{TAB}{TAB}'attempts_times': [list(map(lambda tup: [*tup], attempts_times))]\n" \
                 f"{TAB}}}\n"

        stats += f'{TAB}if result == sat:\n' \
                 f"{TAB}{TAB}data_object['model'] = dict(map(lambda item: (str(item[0]), is_true(item[1])),\n" \
                 f"{TAB}{TAB}{TAB}sorted(parameters_constraints,\n" \
                 f"{TAB}{TAB}{TAB}key=key_function)))\n"

        stats += f'{TAB}found_data.append(data_object)\n' \
                 f'{TAB}if result != sat:\n' \
                 f'{TAB}{TAB}break\n'

        stats += f'print(json.dumps(found_data, separators=(",", ":"),))\n'

        return stats

    def z3_generate_config(self):
        config = ''
        config += f'ET = int(sys.argv[1])\n' \
                  f'wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])\n' \
                  f'timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])\n' \
                  f'max_possible_ET: int = 2 ** 3 - 1\n' \
                  f'\n'

        return config

    def z3_dump_results_onto_json(self):
        results = ''
        folder, extension = sxpatpaths.OUTPUT_PATH[JSON]

        results += f"with open(f'{self.json_out_path}', 'w') as ofile:\n" \
                   f"{TAB}ofile.write(json.dumps(found_data, separators=(\",\", \":\"), indent=4))\n"
        return results


class Template_SOP1ShareLogic(TemplateCreator):
    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)
        self.__literal_per_product = template_specs.literals_per_product
        self.__product_per_output = template_specs.products_per_output
        self.__z3pyscript = None
        self.__product_in_total = template_specs.products_in_total
        self.__et = template_specs.et
        self.__iterations = template_specs.iterations
        self.__z3_out_path = self.set_path(OUTPUT_PATH['z3'])
        self.__json_out_path = self.set_path(sxpatpaths.OUTPUT_PATH['json'])
        self.__json_in_path = None
        self.__json_model: List = []
        self.__json_status: List = []

        # TODO
        # Create a __json_model propery

    @property
    def iterations(self):
        return self.__iterations

    @iterations.setter
    def iterations(self, this_iteration: int):
        self.__iterations = this_iteration

    @property
    def et(self):
        return self.__et

    @et.setter
    def et(self, this_et):
        self.__et = this_et

    @property
    def graph(self):
        return self.current_graph

    @property
    def literals_per_product(self):
        return self.__literal_per_product

    @property
    def lpp(self):
        return self.__literal_per_product

    @lpp.setter
    def lpp(self, this_lpp):
        self.__literal_per_product = this_lpp

    @property
    def products_per_output(self):
        return self.__product_per_output

    @property
    def ppo(self):
        return self.__product_per_output

    # New
    @property
    def products_in_total(self):
        return self.__product_in_total

    # New
    @property
    def pit(self):
        return self.__product_in_total

    @pit.setter
    def pit(self, this_pit):
        self.__product_in_total = this_pit

    @property
    def json_status(self):
        return self.__json_status

    @json_status.setter
    def json_status(self, this_status):
        self.__json_status = this_status

    @property
    def json_model(self):
        return self.__json_model

    @json_model.setter
    def json_model(self, this_model):
        self.__json_model = this_model

    @property
    def z3pyscript(self):
        return self.__z3pyscript

    @z3pyscript.setter
    def z3pyscript(self, input_z3pyscript):
        self.__z3pyscript = input_z3pyscript

    @property
    def z3_out_path(self):
        return self.__z3_out_path

    @z3_out_path.setter
    def z3_out_path(self, this_z3_out_path):
        self.__z3_out_path = this_z3_out_path

    @property
    def json_out_path(self):
        return self.__json_out_path

    @json_out_path.setter
    def json_out_path(self, this_json_out_path):
        self.__json_out_path = this_json_out_path

    @property
    def json_in_path(self):
        return self.__json_in_path

    @json_in_path.setter
    def json_in_path(self, this_path):
        self.__json_in_path = this_path

    def label_graph(self, min_labeling: bool = False, parallel: bool = True):
        labels = labeling(self.exact_benchmark, self.benchmark_name, min_labeling, parallel)

        for n in self.current_graph.graph.nodes:
            if n in labels:
                self.current_graph.graph.nodes[n][WEIGHT] = int(labels[n])

    # TODO: Deprecated
    def label_graph_old(self, constant_value=2, min_labeling: bool = False, parallel: bool = False):
        
        print(Fore.BLUE + f'labeling...' + Style.RESET_ALL)
        labels1, labels0 = labeling_explicit(self.exact_benchmark, self.benchmark_name, constant_value, min_labeling, parallel=parallel)
        for n in self.current_graph.graph.nodes:
            if n in labels0 and n in labels1:
                if constant_value == 0:
                    self.current_graph.graph.nodes[n][WEIGHT] = int(labels0[n])
                elif constant_value == 1:
                    self.current_graph.graph.nodes[n][WEIGHT] = int(labels1[n])
                else:
                    self.current_graph.graph.nodes[n][WEIGHT] = max(int(labels0[n]), int(labels1[n]))

    def set_new_context(self, specs_obj: TemplateSpecs):
        self.lpp = specs_obj.lpp
        self.pit = specs_obj.pit
        self.iterations = specs_obj.iterations
        self.template_name = specs_obj.template_name
        self.benchmark_name = specs_obj.benchmark_name
        self.exact_benchmark = specs_obj.exact_benchmark
        self.json_out_path = self.set_path(sxpatpaths.OUTPUT_PATH[JSON])
        self.z3_out_path = self.set_path(OUTPUT_PATH['z3'])

    # fix this to add the pit, not ppo
    def set_path(self, this_path: Tuple[str, str]):
        # folder, extenstion = this_path
        # if self.shared:
        #     return f'{folder}/{self.benchmark_name}_{LPP}{self.lpp}_{PIT}{self.pit}_{self.template_name}.{extenstion}'
        # else:
        #     return f'{folder}/{self.benchmark_name}_{LPP}{self.lpp}_{PPO}{self.ppo}_{self.template_name}.{extenstion}'
        folder, extension = this_path

        if re.search('id', self.benchmark_name):
            path = f'{folder}/{self.benchmark_name}_{ITER}{self.iterations}.{extension}'
        else:
            path = f'{folder}/{self.benchmark_name}_{TEMPLATE_SPEC_ET}{self.et}_{self.template_name}_{ITER}{self.iterations}.{extension}'
        # print(f'{path = }')
        return path

    def export_z3pyscript(self):
        with open(self.z3_out_path, 'w') as z:
            z.writelines(self.z3pyscript)

    def run_z3pyscript(self, ET: int = 2, num_models: int = 1, timeout: int = 1800):

        process = subprocess.run([PYTHON3, self.z3_out_path, f'{ET}', f'{num_models}', f'{timeout}'], stderr=PIPE,
                                 stdout=PIPE)

        if process.stderr:
            print(Fore.RED + f'ERROR!!! Cannot run {self.z3_out_path}')
            print(f'{process.stderr.decode()}' + Style.RESET_ALL)
            exit()

    # From this point on, all functions needed to create SharedXPAT
    def import_json_model(self, this_path=None):
        self.json_model = []
        self.json_status = []

        if this_path:
            self.json_in_path = this_path
        else:
            self.json_in_path = self.set_path(sxpatpaths.OUTPUT_PATH[JSON])

        with open(self.json_in_path, 'r') as f:
            data = json.load(f)
        for d in data:
            for key in d.keys():
                if key == RESULT:
                    if d[key] == SAT:
                        self.json_model.append(d[MODEL])
                        self.json_status.append(SAT)
                    elif d[key] == UNSAT:
                        self.json_model.append(None)
                        self.json_status.append(UNSAT)
                    else:
                        self.json_model.append(None)
                        self.json_status.append(UNKNOWN)

    def get_json_runtime(self, this_id: int = 0):
        with open(self.json_in_path, 'r') as f:
            data = json.load(f)

        for d in data:
            for key in d.keys():
                if key == "total_time":
                    return float(d[key])

    def z3_generate_z3pyscript(self):
        if self.subxpat:
            if self.shared:  # Shared Subxpat (The best)
                imports = self.z3_generate_imports()  # parent
                config = self.z3_generate_config()
                z3_abs_function = self.z3_generate_z3_abs_function()  # parent
                input_variables_declaration = self.z3_generate_declare_input_variables()
                exact_integer_function_declaration = self.z3_generate_declare_integer_function(F_EXACT)
                approximate_integer_function_declaration = self.z3_generate_declare_integer_function(F_APPROXIMATE)
                utility_variables = self.z3_generate_utility_variables()

                implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters_subxpat_shared()

                exact_circuit_wires_declaration = self.z3_generate_exact_circuit_wires_declaration()
                exact_circuit_outputs_declaration = self.z3_generate_exact_circuit_outputs_declaration()
                exact_circuit_constraints = self.z3_generate_exact_circuit_constraints()

                approximate_circuit_wires_declaration = self.z3_generate_approximate_circuit_wires_declaration()
                approximate_circuit_outputs_declaration = self.z3_generate_approximate_circuit_outputs_declaration()
                approximate_circuit_constraints_shared = self.z3_generate_approximate_circuit_constraints_subxpat_shared()

                for_all_solver = self.z3_generate_forall_solver_subxpat_shared()
                verification_solver = self.z3_generate_verification_solver()
                parameter_constraint_list = self.z3_generate_parameter_constraint_list()
                find_wanted_number_of_models = self.z3_generate_find_wanted_number_of_models()
                store_data = self.z3_generate_store_data()

                self.z3pyscript = imports + config + z3_abs_function + input_variables_declaration + exact_integer_function_declaration + approximate_integer_function_declaration \
                    + utility_variables + implicit_parameters_declaration + exact_circuit_wires_declaration \
                    + approximate_circuit_wires_declaration \
                    + exact_circuit_outputs_declaration \
                    + approximate_circuit_outputs_declaration \
                    + exact_circuit_constraints \
                    + approximate_circuit_constraints_shared \
                    + for_all_solver + verification_solver + parameter_constraint_list + find_wanted_number_of_models \
                    + store_data
            elif not self.shared:
                print(Fore.RED + f'For this functionality, please run the code with --subxpat flag alone!' + Style.RESET_ALL)
                exit()
        # ===========================CATA's Logic Sharing ===========================================
        # ===========================================================================================
        # ===========================================================================================
        # ===========================================================================================
        elif not self.subxpat:
            if self.shared:  # Shared XPAT (Cata's work)
                # print(Fore.LIGHTCYAN_EX + f'Shared XPAT runner generation!' + Style.RESET_ALL)
                imports = self.z3_generate_imports()  # parent
                config = self.z3_generate_config()
                z3_abs_function = self.z3_generate_z3_abs_function()  # parent
                input_variables_declaration = self.z3_generate_declare_input_variables()
                exact_integer_function_declaration = self.z3_generate_declare_integer_function(F_EXACT)
                approximate_integer_function_declaration = self.z3_generate_declare_integer_function(F_APPROXIMATE)
                utility_variables = self.z3_generate_utility_variables()
                implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters_shared()
                exact_circuit_wires_declaration = self.z3_generate_exact_circuit_wires_declaration()
                exact_circuit_outputs_declaration = self.z3_generate_exact_circuit_outputs_declaration()
                exact_circuit_constraints = self.z3_generate_exact_circuit_constraints()
                approximate_circuit_constraints = self.z3_generate_approximate_circuit_constraints_shared()

                for_all_solver = self.z3_generate_forall_solver_shared()
                verification_solver = self.z3_generate_verification_solver()
                parameter_constraint_list = self.z3_generate_parameter_constraint_list()
                find_wanted_number_of_models = self.z3_generate_find_wanted_number_of_models()
                store_data = self.z3_generate_store_data()
                self.z3pyscript = imports + config + z3_abs_function + input_variables_declaration + exact_integer_function_declaration + approximate_integer_function_declaration \
                    + utility_variables + implicit_parameters_declaration + exact_circuit_wires_declaration \
                    + exact_circuit_outputs_declaration + exact_circuit_constraints + approximate_circuit_constraints \
                    + for_all_solver + verification_solver + parameter_constraint_list + find_wanted_number_of_models \
                    + store_data
            elif not self.shared:  # Vanilla XPAT
                imports = self.z3_generate_imports()  # parent
                config = self.z3_generate_config()
                z3_abs_function = self.z3_generate_z3_abs_function()  # parent
                input_variables_declaration = self.z3_generate_declare_input_variables()
                exact_integer_function_declaration = self.z3_generate_declare_integer_function(F_EXACT)
                approximate_integer_function_declaration = self.z3_generate_declare_integer_function(F_APPROXIMATE)
                utility_variables = self.z3_generate_utility_variables()
                implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters()
                exact_circuit_wires_declaration = self.z3_generate_exact_circuit_wires_declaration()
                exact_circuit_outputs_declaration = self.z3_generate_exact_circuit_outputs_declaration()
                exact_circuit_constraints = self.z3_generate_exact_circuit_constraints()
                approximate_circuit_constraints = self.z3_generate_approximate_circuit_constraints()
                for_all_solver = self.z3_generate_forall_solver()
                verification_solver = self.z3_generate_verification_solver()
                parameter_constraint_list = self.z3_generate_parameter_constraint_list()
                find_wanted_number_of_models = self.z3_generate_find_wanted_number_of_models()
                store_data = self.z3_generate_store_data()
                self.z3pyscript = imports + config + z3_abs_function + input_variables_declaration + exact_integer_function_declaration + approximate_integer_function_declaration \
                    + utility_variables + implicit_parameters_declaration + exact_circuit_wires_declaration \
                    + exact_circuit_outputs_declaration + exact_circuit_constraints + approximate_circuit_constraints \
                    + for_all_solver + verification_solver + parameter_constraint_list + find_wanted_number_of_models \
                    + store_data
        self.export_z3pyscript()

    # NM
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

    # NM
    def declare_gate(self, this_key: str, this_dict: dict = None):
        if this_dict is None:
            declaration = f"{this_key} = {Z3BOOL}('{this_key}')\n"
        else:
            declaration = f"{this_dict[this_key]} = {Z3BOOL}('{this_dict[this_key]}')\n"
        return declaration

    # NM
    def z3_generate_declare_input_variables(self):
        input_variables = ''
        input_variables += f'# Inputs variables declaration\n'
        for inp_key in self.exact_graph.input_dict.keys():
            input_variables += self.declare_gate(inp_key, self.exact_graph.input_dict)
        input_variables += '\n'
        return input_variables

    # NM
    def z3_generate_declare_integer_function(self, function_name):
        integer_function = ''
        integer_function += f'# Integer function declaration\n'
        temp_arg_list = ', '.join(repeat(BOOLSORT, self.graph.num_inputs))
        temp_arg_list += ', ' + INTSORT
        integer_function += f"{function_name} = {FUNCTION}('{function_name}', {temp_arg_list})\n"
        return integer_function

    # NM
    def z3_generate_utility_variables(self):
        utility_variables = ''
        utility_variables += f'# utility variables'
        utility_variables += f"\n" \
                             f"difference = z3_abs({F_EXACT}({', '.join(self.exact_graph.input_dict.values())}) - " \
                             f"{F_APPROXIMATE}({', '.join(self.exact_graph.input_dict.values())})" \
                             f")\n" \
                             f"error = {Z3INT}('error')\n"

        utility_variables += '\n'
        return utility_variables

    # NM
    def z3_generate_o_subxpat_shared(self):
        temp_o = ''
        for idx in range(self.graph.subgraph_num_outputs):
            temp_name = f'{PRODUCT_PREFIX}{idx}'
            temp_o += self.declare_gate(temp_name)
        return temp_o

    def z3_generate_o(self):
        temp_o = ''
        for idx in range(self.graph.num_outputs):
            temp_name = f'{PRODUCT_PREFIX}{idx}'
            temp_o += self.declare_gate(temp_name)
        return temp_o

    def z3_generate_oti_subxpat_shared(self):
        temp_oti = ''
        for o_idx in range(self.graph.subgraph_num_outputs):
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.graph.subgraph_num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    temp_oti += self.declare_gate(p_s)
                    temp_oti += self.declare_gate(p_l)
        return temp_oti

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

    def z3_generate_ti_subxpat_shared(self):
        temp_ti = ''
        for pit_idx in range(self.pit):
            for input_idx in range(self.graph.subgraph_num_inputs):
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                temp_ti += self.declare_gate(p_s)
                temp_ti += self.declare_gate(p_l)
        return temp_ti

    def z3_generate_ti(self):
        temp_ti = ''
        for pit_idx in range(self.pit):
            for input_idx in range(self.graph.num_inputs):
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                temp_ti += self.declare_gate(p_s)
                temp_ti += self.declare_gate(p_l)
        return temp_ti

    def z3_generate_pto_subxpat_shared(self):
        temp_pto = f''

        for output_idx in range(self.graph.subgraph_num_outputs):
            for pit_idx in range(self.pit):
                # sth like this: p_pr0_o0
                name = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                temp_pto += self.declare_gate(name)

        return temp_pto

    def z3_generate_pto(self):
        temp_pto = f''

        for output_idx in range(self.graph.num_outputs):
            for pit_idx in range(self.pit):
                # sth like this: p_pr0_o0
                name = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                temp_pto += self.declare_gate(name)

        return temp_pto

    # New --> ti added

    def z3_generate_declare_implicit_parameters_subxpat_shared(self):
        implicit_parameters = ''
        implicit_parameters += f'# Parameters variables declaration\n'
        implicit_parameters += self.z3_generate_o_subxpat_shared()
        implicit_parameters += self.z3_generate_ti_subxpat_shared()
        implicit_parameters += self.z3_generate_pto_subxpat_shared()
        implicit_parameters += '\n'
        return implicit_parameters

    def z3_generate_declare_implicit_parameters_shared(self):
        implicit_parameters = ''
        implicit_parameters += f'# Parameters variables declaration\n'
        implicit_parameters += self.z3_generate_o()
        implicit_parameters += self.z3_generate_ti()
        implicit_parameters += self.z3_generate_pto()
        implicit_parameters += '\n'
        return implicit_parameters

    def z3_generate_declare_implicit_parameters(self):
        implicit_parameters = ''
        implicit_parameters += f'# Parameters variables declaration\n'
        implicit_parameters += self.z3_generate_o()
        implicit_parameters += self.z3_generate_oti()
        implicit_parameters += '\n'
        return implicit_parameters

    # NM
    def z3_generate_exact_circuit_wires_declaration(self):
        exact_wires_declaration = ''
        exact_wires_declaration += f'# wires functions declaration for exact circuit\n'

        for g_idx in self.exact_graph.gate_dict:
            exact_wires_declaration += f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))}" \
                                       f", {BOOLSORT}" \
                                       f")\n"

        for g_idx in self.exact_graph.constant_dict:
            # print(f'{g_idx = }')
            exact_wires_declaration += f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx} = " \
                                       f"{FUNCTION}('{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}', " \
                                       f"{', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))}" \
                                       f", {BOOLSORT}" \
                                       f")\n"
        exact_wires_declaration += '\n'
        return exact_wires_declaration

    # NM
    def z3_generate_approximate_circuit_wires_declaration(self):
        approximate_wires_declaration = ''
        approximate_wires_declaration += f'# wires functions declaration for approximate circuit\n'
        # TODO:
        # Fix when PIs are not the subgrpah's inputs

        gate_key_list = list(self.current_graph.gate_dict.keys())
        constant_key_list = list(self.current_graph.constant_dict.keys())
        # gates
        for g_idx in gate_key_list:
            g_label = self.current_graph.gate_dict[g_idx]
            if self.current_graph.is_subgraph_member(g_label):
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.subgraph_num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
            else:
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
        # constants
        for g_idx in constant_key_list:
            g_label = self.current_graph.constant_dict[g_idx]
            if self.current_graph.is_subgraph_member(g_label):
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.subgraph_num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
            else:
                approximate_wires_declaration += f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx} = " \
                                                 f"{FUNCTION}('{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}', " \
                                                 f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs))}" \
                                                 f", {BOOLSORT}" \
                                                 f")\n"
        approximate_wires_declaration += '\n'
        return approximate_wires_declaration

    # NM
    def z3_generate_exact_circuit_outputs_declaration(self):
        exact_circuit_output_declaration = ''
        exact_circuit_output_declaration += f'# outputs functions declaration for exact circuit\n'
        for output_idx in range(self.exact_graph.num_outputs):
            exact_circuit_output_declaration += f"{EXACT_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{EXACT_OUTPUT_PREFIX}{OUT}{output_idx}', " \
                                                f"{', '.join(repeat(BOOLSORT, self.graph.num_inputs + 1))}" \
                                                f")\n"
        exact_circuit_output_declaration += '\n'
        return exact_circuit_output_declaration

    # NM
    def z3_generate_approximate_circuit_outputs_declaration(self):
        approximate_circuit_output_declaration = ''
        approximate_circuit_output_declaration = f'# outputs functions declaration for approximate circuit\n'
        for output_idx in range(self.current_graph.num_outputs):
            approximate_circuit_output_declaration += f"{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} ('{APPROXIMATE_OUTPUT_PREFIX}{OUT}{output_idx}', " \
                                                      f"{', '.join(repeat(BOOLSORT, self.current_graph.num_inputs + 1))}" \
                                                      f")\n"
        approximate_circuit_output_declaration += '\n'
        return approximate_circuit_output_declaration

    # NM
    def get_predecessors(self, node: str) -> List[str]:
        return list(self.graph.graph.predecessors(node))

    def get_predecessors_exact(self, node: str) -> List[str]:
        return list(self.exact_graph.graph.predecessors(node))

    # NM
    def get_logical_function(self, node: str) -> str:
        return self.graph.graph.nodes[node][LABEL]

    def get_logical_function_exact(self, node: str) -> str:
        return self.exact_graph.graph.nodes[node][LABEL]

    def z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(self, node: str):
        assert node in list(self.exact_graph.input_dict.values()) or node in list(self.exact_graph.gate_dict.values()) \
            or node in list(self.exact_graph.output_dict.values()) or node in list(self.exact_graph.constant_dict.values()) \
            or node.startswith(APPROXIMATE_WIRE_PREFIX)
        if node in list(self.exact_graph.input_dict.values()):
            return node
        elif node in list(self.exact_graph.gate_dict.values()):
            node_id = -1
            for key in self.exact_graph.gate_dict.keys():
                if self.exact_graph.gate_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + node_id}({','.join(list(self.exact_graph.input_dict.values()))})"
        elif node in list(self.exact_graph.output_dict.values()):
            for key in self.exact_graph.output_dict.keys():
                if self.exact_graph.output_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{OUT}{node_id}({','.join(list(self.exact_graph.input_dict.values()))})"
        elif node in list(self.exact_graph.constant_dict.values()):
            return Z3_GATES_DICTIONARY[self.exact_graph.graph.nodes[node][LABEL]]

    def z3_express_node_as_wire_constraints(self, node: str):
        assert node in list(self.graph.input_dict.values()) or node in list(self.graph.gate_dict.values()) \
            or node in list(self.graph.output_dict.values()) or node in list(self.graph.constant_dict.values()) \
            or node.startswith(APPROXIMATE_WIRE_PREFIX)
        if node in list(self.graph.input_dict.values()):
            return node
        elif node in list(self.graph.gate_dict.values()):
            node_id = -1
            for key in self.graph.gate_dict.keys():
                if self.graph.gate_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{self.graph.num_inputs + node_id}({','.join(list(self.graph.input_dict.values()))})"
        elif node in list(self.graph.output_dict.values()):
            for key in self.graph.output_dict.keys():
                if self.graph.output_dict[key] == node:
                    node_id = key
            return f"{EXACT_WIRES_PREFIX}{OUT}{node_id}({','.join(list(self.graph.input_dict.values()))})"
        elif node in list(self.graph.constant_dict.values()):
            return Z3_GATES_DICTIONARY[self.graph.graph.nodes[node][LABEL]]

    # NM
    def z3_generate_exact_circuit_wire_constraints(self):
        exact_wire_constraints = ''
        exact_wire_constraints += f'# exact circuit constraints\n'
        exact_wire_constraints += f'{EXACT_CIRCUIT} = And(\n'
        exact_wire_constraints += f'{TAB}# wires\n'

        for g_idx in (self.exact_graph.gate_dict.keys()):
            g_label = self.exact_graph.gate_dict[g_idx]
            g_predecessors = self.get_predecessors_exact(g_label)
            g_function = self.get_logical_function_exact(g_label)

            assert len(g_predecessors) == 1 or len(g_predecessors) == 2, Fore.RED + f'ERROR!!! {len(g_predecessors) = }' + Style.RESET_ALL
            assert g_function == NOT or g_function == AND or g_function == OR
            if len(g_predecessors) == 1:
                if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:

                    pred_1 = self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(g_predecessors[0])
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
            else:
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

                if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:
                    pred_1 = self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(g_predecessors[0])
                if g_predecessors[1] in list(self.exact_graph.input_dict.values()):
                    pred_2 = g_predecessors[1]
                else:
                    pred_2 = self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(g_predecessors[1])

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
        return exact_wire_constraints

    # NM
    def z3_generate_exact_circuit_output_constraints(self):
        exact_output_constraints = ''
        exact_output_constraints += f'{TAB}# boolean outputs (from the least significant)\n'
        for output_idx in self.exact_graph.output_dict.keys():
            output_label = self.exact_graph.output_dict[output_idx]
            output_predecessors = list(self.exact_graph.graph.predecessors(output_label))
            assert len(output_predecessors) == 1
            pred = self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(output_predecessors[0])
            output = self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(output_label)
            exact_output_constraints += f'{TAB}{output} == {pred},\n'
        return exact_output_constraints

    # NM
    def z3_generate_exact_circuit_integer_output_constraints(self):
        exact_integer_outputs = ''
        exact_integer_outputs += f'{TAB}# exact_integer_outputs\n'
        exact_integer_outputs += f"{TAB}{F_EXACT}({','.join(self.exact_graph.input_dict.values())}) == \n"

        for idx in range(self.exact_graph.num_outputs):
            output_label = self.exact_graph.output_dict[idx]
            if idx == self.exact_graph.num_outputs - 1:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(output_label)},\n"
            else:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat_shared_exact_circuit(output_label)} +\n"
        return exact_integer_outputs

    # NM
    def z3_generate_exact_circuit_constraints(self):
        wires = self.z3_generate_exact_circuit_wire_constraints()
        outputs = self.z3_generate_exact_circuit_output_constraints()
        integer_outputs = self.z3_generate_exact_circuit_integer_output_constraints()
        wires += '\n'
        outputs += '\n'
        integer_outputs += '\n'
        exact_circuit_constraints = wires + outputs + integer_outputs + ')\n'

        return exact_circuit_constraints

    def z3_generate_approximate_circuit_constraints(self):
        approximate_circuit_constraints = ''
        approximate_circuit_constraints += f'# Approximate circuit\n'
        approximate_circuit_constraints += f'# constraints\n'
        approximate_circuit_constraints += f'{APPROXIMATE_CIRCUIT} = {Z3_AND}(\n'
        approximate_circuit_constraints += f"{TAB}{F_APPROXIMATE}({','.join(self.graph.input_dict.values())}) == \n"
        approximate_circuit_constraints += f"{TAB}{SUM}("
        for o_idx in range(self.graph.num_outputs):
            if o_idx > 0:
                approximate_circuit_constraints += f"{TAB}{TAB}"  # fixing the indentations
            approximate_circuit_constraints += f"{INTVAL}({2 ** o_idx}) * {Z3_AND} ( {PRODUCT_PREFIX}{o_idx}, {Z3_OR}("
            for ppo_idx in range(self.ppo):
                approximate_circuit_constraints += f'{Z3_AND}('
                for input_idx in range(self.graph.num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                    loop_1_last_iter_flg = o_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1

                    approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {self.graph.input_dict[input_idx]})'

                    if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
                        approximate_circuit_constraints += ')))\n))\n'
                    elif loop_3_last_iter_flg and loop_2_last_iter_flg:
                        approximate_circuit_constraints += '))),\n'
                    elif loop_3_last_iter_flg:
                        approximate_circuit_constraints += '), '
                    else:
                        approximate_circuit_constraints += ','
        return approximate_circuit_constraints

    def __z3_get_subgraph_input_list(self):
        input_list = list(self.current_graph.subgraph_input_dict.values())
        input_list_tmp = list(self.current_graph.subgraph_input_dict.values())

        input_list_tmp = self.__fix_order()
        for idx, inp in enumerate(input_list):
            if inp in self.current_graph.gate_dict.values():
                input_list_tmp[
                    idx] = f"{self.__z3_get_approximate_label(inp)}({', '.join(list(self.current_graph.input_dict.values()))})"
        return input_list_tmp

    def __fix_order(self):
        subpgraph_input_list = list(self.current_graph.subgraph_input_dict.values())
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

    def __z3_get_approximate_label(self, node: str):
        graph_gates = list(self.current_graph.gate_dict.values())

        if node in list(self.current_graph.gate_dict.values()):
            for gate_idx in self.current_graph.gate_dict.keys():
                if self.current_graph.gate_dict[gate_idx] == node:
                    return f'{APPROXIMATE_WIRE_PREFIX}{gate_idx + self.current_graph.num_inputs}'
        else:
            return node

    def get_predecessors(self, node: str) -> List[str]:
        return list(self.exact_graph.graph.predecessors(node))

    def get_logical_function(self, node: str) -> str:
        return self.exact_graph.graph.nodes[node][LABEL]

    def get_predecessors_xpat(self, node: str) -> List[str]:
        return list(self.current_graph.subgraph.predecessors(node))

    def get_logical_function_xpat(self, node: str) -> str:
        return self.current_graph.subgraph.nodes[node][LABEL]

    def z3_express_node_as_wire_constraints_subxpat(self, node: str):
        assert node in list(self.current_graph.input_dict.values()) or node in list(
            self.current_graph.gate_dict.values()) \
            or node in list(self.current_graph.output_dict.values()) or node in list(
            self.current_graph.constant_dict.values()) \
            or node.startswith(APPROXIMATE_WIRE_PREFIX)

        if node in list(self.current_graph.input_dict.values()):
            return node
        elif node in list(self.current_graph.gate_dict.values()):
            if self.current_graph.is_subgraph_member(node):
                node_id = -1
                for key in self.current_graph.gate_dict.keys():
                    if self.current_graph.gate_dict[key] == node:
                        node_id = key

                input_list = self.__z3_get_subgraph_input_list()
                # print(f'for the subgraph = {input_list}')
                return f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + node_id}({','.join(input_list)})"
            else:
                node_id = -1
                for key in self.current_graph.gate_dict.keys():
                    if self.current_graph.gate_dict[key] == node:
                        node_id = key
                return f"{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + node_id}({','.join(list(self.current_graph.input_dict.values()))})"
        elif node in list(self.current_graph.output_dict.values()):
            for key in self.current_graph.output_dict.keys():
                if self.current_graph.output_dict[key] == node:
                    node_id = key
            return f"{APPROXIMATE_WIRE_PREFIX}{OUT}{node_id}({','.join(list(self.current_graph.input_dict.values()))})"
        elif node in list(self.current_graph.constant_dict.values()):
            # print(f'{self.current_graph.graph.nodes[node] = }')
            return Z3_GATES_DICTIONARY[self.current_graph.graph.nodes[node][LABEL]]

    def z3_generate_approximate_circuit_wire_constraints_shared(self):
        exact_wire_constraints = ''
        exact_wire_constraints += f'# approximate circuit constraints\n'
        exact_wire_constraints += f'{APPROXIMATE_CIRCUIT} = And(\n'
        exact_wire_constraints += f'{TAB}# wires\n'
        subgraph_input_list = self.__z3_get_subgraph_input_list()
        gate_key_list = list(self.current_graph.gate_dict.keys())
        for g_idx in gate_key_list:
            g_label = self.current_graph.gate_dict[g_idx]
            # print(f'{g_label = }')
            if not self.current_graph.is_subgraph_member(g_label):
                g_predecessors = self.get_predecessors_xpat(g_label)
                # print(f'{g_predecessors = }')
                g_function = self.get_logical_function_xpat(g_label)
                assert len(g_predecessors) == 1 or len(g_predecessors) == 2
                assert g_function == NOT or g_function == AND or g_function == OR
                if len(g_predecessors) == 1:
                    if g_predecessors[0] in list(self.current_graph.input_dict.values()):
                        pred_1 = g_predecessors[0]
                    else:
                        pred_1 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[0])

                    exact_wire_constraints += f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                              f"{','.join(list(self.current_graph.input_dict.values()))}) == "
                    exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
                else:
                    exact_wire_constraints += f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                              f"{','.join(list(self.current_graph.input_dict.values()))}) == "
                    if g_predecessors[0] in list(self.current_graph.input_dict.values()):
                        pred_1 = g_predecessors[0]
                    else:
                        pred_1 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[0])
                    if g_predecessors[1] in list(self.current_graph.input_dict.values()):
                        pred_2 = g_predecessors[1]
                    else:
                        pred_2 = self.z3_express_node_as_wire_constraints_subxpat(g_predecessors[1])
                    exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
            elif self.current_graph.is_subgraph_member(g_label) and self.current_graph.is_subgraph_output(g_label):
                # outputs are g10, g16, g20
                # print(Fore.LIGHTCYAN_EX + f'{self.graph.subgraph_num_outputs = }')
                output_list = list(self.current_graph.subgraph_output_dict.values())
                # print(f'{self.current_graph.subgraph_output_dict = }')
                o_idx = output_list.index(g_label)
                # print(f'{self.graph.subgraph_input_dict = }')
                # print(f'{g_label = } -> {o_idx = }')
                # print(f'{subgraph_input_list= }')
                # print(Style.RESET_ALL)

                approximate_circuit_constraints = f"{TAB}{APPROXIMATE_WIRE_PREFIX}{self.current_graph.num_inputs + g_idx}(" \
                                                  f"{','.join(subgraph_input_list)}) == "
                approximate_circuit_constraints += f"{Z3_AND} ({SHARED_PARAM_PREFIX}_{SHARED_OUTPUT_PREFIX}{o_idx}, {Z3_OR}("
                for pit_idx in range(self.pit):

                    approximate_circuit_constraints += f"{Z3_AND}({SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{o_idx},"

                    for input_idx in range(self.graph.subgraph_num_inputs):

                        p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                        p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                        loop_1_last_iter_flg = o_idx == self.graph.subgraph_num_outputs - 1
                        loop_2_last_iter_flg = pit_idx == self.pit - 1
                        loop_3_last_iter_flg = input_idx == self.graph.subgraph_num_inputs - 1

                        approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {subgraph_input_list[input_idx]})'

                        if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
                            approximate_circuit_constraints += '))),\n'
                        elif loop_3_last_iter_flg and loop_2_last_iter_flg:
                            approximate_circuit_constraints += '))),\n'
                        elif loop_3_last_iter_flg:
                            approximate_circuit_constraints += '),'
                            pass
                        else:
                            approximate_circuit_constraints += ','

                exact_wire_constraints += approximate_circuit_constraints
        return exact_wire_constraints

    def z3_generate_approximate_circuit_output_constraints_shared(self):
        approximate_output_constraints = ''
        approximate_output_constraints += f'{TAB}# boolean outputs (from the least significant)\n'

        for output_idx in self.current_graph.output_dict.keys():
            output_label = self.current_graph.output_dict[output_idx]
            output_predecessors = list(self.current_graph.graph.predecessors(output_label))

            assert len(output_predecessors) == 1
            # print(f'{self.current_graph.subgraph_gate_dict = }')
            # print(f'{self.current_graph.graph.nodes = }')
            # print(f'{output_predecessors = }')
            pred = self.z3_express_node_as_wire_constraints_subxpat(output_predecessors[0])
            output = self.z3_express_node_as_wire_constraints_subxpat(output_label)
            approximate_output_constraints += f'{TAB}{output} == {pred},\n'
        return approximate_output_constraints

    def z3_generate_exact_circuit_integer_output_constraints_shared(self):
        exact_integer_outputs = ''
        exact_integer_outputs += f'{TAB}# approximate_integer_outputs\n'
        exact_integer_outputs += f"{TAB}{F_APPROXIMATE}({','.join(self.current_graph.input_dict.values())}) == \n"

        for idx in range(self.current_graph.num_outputs):
            output_label = self.current_graph.output_dict[idx]
            if idx == self.current_graph.num_outputs - 1:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat(output_label)},\n"
            else:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints_subxpat(output_label)} +\n"
        return exact_integer_outputs

    # NM
    def z3_generate_approximate_circuit_constraints_shared(self):
        approximate_circuit_constraints = ''
        approximate_circuit_constraints += f'# Approximate circuit\n'
        approximate_circuit_constraints += f'# constraints\n'
        approximate_circuit_constraints += f'{APPROXIMATE_CIRCUIT} = {Z3_AND}(\n'
        approximate_circuit_constraints += f"{TAB}{F_APPROXIMATE}({','.join(self.graph.input_dict.values())}) == \n"
        approximate_circuit_constraints += f"{TAB}{SUM}("
        for o_idx in range(self.graph.num_outputs):

            if o_idx > 0:
                approximate_circuit_constraints += f"{TAB}{TAB}"
            approximate_circuit_constraints += f"{INTVAL}({2 ** o_idx}) * {Z3_AND} ({SHARED_PARAM_PREFIX}_{SHARED_OUTPUT_PREFIX}{o_idx}, {Z3_OR}("
            for pit_idx in range(self.pit):

                approximate_circuit_constraints += f"{Z3_AND}({SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{o_idx},"

                for input_idx in range(self.graph.num_inputs):

                    p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                    loop_1_last_iter_flg = o_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = pit_idx == self.pit - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1

                    approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {self.graph.input_dict[input_idx]})'

                    if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
                        approximate_circuit_constraints += '))))\n)\n'
                    elif loop_3_last_iter_flg and loop_2_last_iter_flg:
                        approximate_circuit_constraints += '))),\n'
                    elif loop_3_last_iter_flg:
                        approximate_circuit_constraints += '),'
                    else:
                        approximate_circuit_constraints += ','

        # exit()
        return approximate_circuit_constraints

    def z3_generate_approximate_circuit_constraints_subxpat_shared(self):
        wires = self.z3_generate_approximate_circuit_wire_constraints_shared()
        outputs = self.z3_generate_approximate_circuit_output_constraints_shared()
        integer_outputs = self.z3_generate_exact_circuit_integer_output_constraints_shared()
        wires += '\n'
        outputs += '\n'
        integer_outputs += '\n'

        approximate_circuit_constraints_shared = wires + outputs + integer_outputs + ')\n'

        # approximate_circuit_constraints = ''
        # approximate_circuit_constraints += f'{APPROXIMATE_CIRCUIT} = {Z3_AND}(\n'
        # approximate_circuit_constraints += f"{TAB}{F_APPROXIMATE}({','.join(self.graph.input_dict.values())}) == \n"
        # approximate_circuit_constraints += f"{TAB}{SUM}("
        # for o_idx in range(self.graph.num_outputs):
        #
        #     if o_idx > 0:
        #         approximate_circuit_constraints += f"{TAB}{TAB}"
        #     approximate_circuit_constraints += f"{INTVAL}({2 ** o_idx}) * {Z3_AND} ({SHARED_PARAM_PREFIX}_{SHARED_OUTPUT_PREFIX}{o_idx}, {Z3_OR}("
        #     for pit_idx in range(self.pit):
        #
        #         approximate_circuit_constraints += f"{Z3_AND}({SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{o_idx},"
        #
        #         for input_idx in range(self.graph.num_inputs):
        #
        #             p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
        #             p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
        #
        #             loop_1_last_iter_flg = o_idx == self.graph.num_outputs - 1
        #             loop_2_last_iter_flg = pit_idx == self.pit - 1
        #             loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
        #
        #             approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {self.graph.input_dict[input_idx]})'
        #
        #             if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
        #                 approximate_circuit_constraints += '))))\n)\n'
        #             elif loop_3_last_iter_flg and loop_2_last_iter_flg:
        #                 approximate_circuit_constraints += '))),\n'
        #             elif loop_3_last_iter_flg:
        #                 approximate_circuit_constraints += '),'
        #             else:
        #                 approximate_circuit_constraints += ','

        # exit()
        return approximate_circuit_constraints_shared

    def z3_generate_forall_solver_preperation(self):
        prep = ''
        prep += '# forall solver\n'
        prep += f'{FORALL_SOLVER} = {SOLVER}\n' \
                f'{FORALL_SOLVER}.{ADD}({FORALL}(\n' \
                f"{TAB}[{','.join(list(self.graph.input_dict.values()))}],\n" \
                f"{TAB}{Z3_AND}(\n"
        return prep

    # NM
    def z3_generate_forall_solver_error_constraint(self):
        error = ''
        error += f'{TAB}{TAB}# error constraints\n'
        error += f'{TAB}{TAB}{DIFFERENCE} <= {ET},\n'
        return error

    # NM
    def z3_generate_forall_solver_circuits(self):
        circuits = ''
        circuits += f'{TAB}{TAB}# circuits\n'
        circuits += f'{TAB}{TAB}{EXACT_CIRCUIT},\n' \
                    f'{TAB}{TAB}{APPROXIMATE_CIRCUIT},\n'
        return circuits

    def z3_generate_forall_solver_atmost_constraints_subxpat_shared(self):
        atmost = ''
        atmost += f'{TAB}{TAB}# AtMost constraints\n'
        # print(f'{self.graph.subgraph_num_inputs = }')
        for pit_idx in range(self.pit):
            atmost += f"{TAB}{TAB}("
            for input_idx in range(self.graph.subgraph_num_inputs):
                # loop_2_last_iter_flg = pit_idx == self.pit - 1
                loop_3_last_iter_flg = input_idx == self.graph.subgraph_num_inputs - 1
                # sth like this: p_pr0_i0_s
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                atmost += f"{IF}({p_s}, 1, 0)"

                if loop_3_last_iter_flg:
                    atmost += f') <= {self.lpp},\n'
                else:
                    atmost += f' + '
        atmost += '\n'

        return atmost

    def z3_generate_forall_solver_atmost_constraints_shared(self):
        atmost = ''
        atmost += f'{TAB}{TAB}# AtMost constraints\n'

        for pit_idx in range(self.pit):
            atmost += f"{TAB}{TAB}("
            for input_idx in range(self.graph.num_inputs):
                # loop_2_last_iter_flg = pit_idx == self.pit - 1
                loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                # sth like this: p_pr0_i0_s
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                atmost += f"{IF}({p_s}, 1, 0)"

                if loop_3_last_iter_flg:
                    atmost += f') <= {self.lpp},\n'
                else:
                    atmost += f' + '
        atmost += '\n'

        return atmost

    def z3_generate_forall_solver_atmost_constraints(self):
        atmost = ''
        atmost += f'{TAB}{TAB}# AtMost constraints\n'

        for output_idx in range(self.graph.num_outputs):
            for ppo_idx in range(self.ppo):
                atmost += f"{TAB}{TAB}("
                for input_idx in range(self.graph.num_inputs):
                    loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    atmost += f"{IF}({p_s}, 1, 0)"

                    # print(f'{atmost = }')

                    if loop_3_last_iter_flg:
                        atmost += f') <= {self.lpp},\n'
                    else:
                        atmost += f' + '
        atmost += '\n'

        return atmost

    def z3_generate_forall_solver_redundancy_constraints_subxpat_shared(self):
        redundancy = ''
        redundancy += f'{TAB}{TAB}# Redundancy constraints\n'
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care_subxpat_shared()
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_subxpat_shared()
        remove_unused_products = self.z3_generate_forall_solver_redundancy_constraints_remove_unused_products_subxpat_shared()
        set_pit_order = self.z3_generate_forall_solver_redundancy_constraints_set_pit_order_subxpat_shared()
        set_order = f''
        double_no_care += '\n'
        remove_constant_zero_permutation += '\n'
        set_order += '\n'
        end = f"{TAB})\n))\n"
        redundancy += double_no_care + remove_constant_zero_permutation + remove_unused_products + set_pit_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints_shared(self):
        redundancy = ''
        redundancy += f'{TAB}{TAB}# Redundancy constraints\n'
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care_shared()
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_shared()
        remove_unused_products = self.z3_generate_forall_solver_redundancy_constraints_remove_unused_products_shared()
        set_pit_order = self.z3_generate_forall_solver_redundancy_constraints_set_pit_order()
        set_order = f''
        double_no_care += '\n'
        remove_constant_zero_permutation += '\n'
        set_order += '\n'
        end = f"{TAB})\n))\n"
        redundancy += double_no_care + remove_constant_zero_permutation + remove_unused_products + set_pit_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints(self):
        redundancy = ''
        redundancy += f'{TAB}{TAB}# Redundancy constraints\n'
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care()
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation()
        set_ppo_order = self.z3_generate_forall_solver_redundancy_constraints_set_ppo_order()

        double_no_care += '\n'
        remove_constant_zero_permutation += '\n'
        set_ppo_order += '\n'
        end = f"{TAB})\n))\n"
        redundancy += double_no_care + remove_constant_zero_permutation + set_ppo_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints_set_pit_order_subxpat_shared(self):
        """
        this will also remove duplicates
        :return:
        """
        # sth like this: imaging that pit = 3
        # (IntVal(1) * p_pr0_i0_s + IntVal(2) * p_pr0_i0_l + IntVal(4) * p_pr0_i1_s + IntVal(8) * p_pr0_i1_l > \
        # IntVal(1) * p_pr1_i0_s + IntVal(2) * p_pr1_i0_l + IntVal(4) * p_pr1_i1_s + IntVal(8) * p_pr1_i1_l),
        # IntVal(1) * p_pr1_i0_s + IntVal(2) * p_pr1_i0_l + IntVal(4) * p_pr1_i1_s + IntVal(8) * p_pr1_i1_l) > \
        # IntVal(1) * p_pr2_i0_s + IntVal(2) * p_pr2_i0_l + IntVal(4) * p_pr2_i1_s + IntVal(8) * p_pr2_i1_l)

        pit_order = ''
        pit_order += f'{TAB}{TAB}# set order of pits\n'
        if self.pit >= 1:

            for pit_idx in range(self.pit - 1):
                pit_order += f"{TAB}{TAB}("

                # left side
                for input_idx in range(self.graph.subgraph_num_inputs):
                    p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                    p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                    loop_1_last_iter_flag = pit_idx == self.pit - 1
                    loop_2_last_iter_flag = input_idx == self.graph.subgraph_num_inputs - 1
                    pit_order += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'
                    if loop_2_last_iter_flag:
                        pit_order += f') > ('
                    else:
                        pit_order += f' + '

                # right side
                for input_idx in range(self.graph.subgraph_num_inputs):
                    p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx + 1}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                    p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx + 1}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                    loop_1_last_iter_flag = pit_idx + 1 == self.pit - 1
                    loop_2_last_iter_flag = input_idx == self.graph.subgraph_num_inputs - 1
                    pit_order += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'

                    if loop_2_last_iter_flag:
                        pit_order += f'), \n'
                    else:
                        pit_order += f' + '

        return pit_order

    def z3_generate_forall_solver_redundancy_constraints_set_pit_order(self):
        """
        this will also remove duplicates
        :return:
        """
        # sth like this: imaging that pit = 3
        # (IntVal(1) * p_pr0_i0_s + IntVal(2) * p_pr0_i0_l + IntVal(4) * p_pr0_i1_s + IntVal(8) * p_pr0_i1_l > \
        # IntVal(1) * p_pr1_i0_s + IntVal(2) * p_pr1_i0_l + IntVal(4) * p_pr1_i1_s + IntVal(8) * p_pr1_i1_l),
        # IntVal(1) * p_pr1_i0_s + IntVal(2) * p_pr1_i0_l + IntVal(4) * p_pr1_i1_s + IntVal(8) * p_pr1_i1_l) > \
        # IntVal(1) * p_pr2_i0_s + IntVal(2) * p_pr2_i0_l + IntVal(4) * p_pr2_i1_s + IntVal(8) * p_pr2_i1_l)

        pit_order = ''
        pit_order += f'{TAB}{TAB}# set order of pits\n'
        if self.pit >= 1:

            for pit_idx in range(self.pit - 1):
                pit_order += f"{TAB}{TAB}("

                # left side
                for input_idx in range(self.graph.num_inputs):
                    p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                    p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                    loop_1_last_iter_flag = pit_idx == self.pit - 1
                    loop_2_last_iter_flag = input_idx == self.graph.num_inputs - 1
                    pit_order += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'
                    if loop_2_last_iter_flag:
                        pit_order += f') > ('
                    else:
                        pit_order += f' + '

                # right side
                for input_idx in range(self.graph.num_inputs):
                    p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx + 1}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                    p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx + 1}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                    loop_1_last_iter_flag = pit_idx + 1 == self.pit - 1
                    loop_2_last_iter_flag = input_idx == self.graph.num_inputs - 1
                    pit_order += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'

                    if loop_2_last_iter_flag:
                        pit_order += f'), \n'
                    else:
                        pit_order += f' + '

        return pit_order

    def z3_generate_forall_solver_redundancy_constraints_set_ppo_order(self):
        ppo_order = ''
        ppo_order += f'{TAB}{TAB}# set order of trees\n'

        if self.ppo == 1:
            # print(f'No need for ordering the PPOs!')
            ppo_order += f'{TAB}{TAB}True, \n'
        else:
            for output_idx in range(self.graph.num_outputs):
                for ppo_idx in range(self.ppo - 1):

                    current_product = f'{TAB}{TAB}('
                    next_product = f'('
                    for input_idx in range(self.graph.num_inputs):

                        loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                        loop_2_last_iter_flg = ppo_idx == self.ppo - 2
                        loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                        p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                        p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'

                        p_l_next = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx + 1}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                        p_s_next = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx + 1}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'

                        current_product += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l}'
                        next_product += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s_next} + {INTVAL}({2 ** (2 * input_idx + 1)}) * {p_l_next}'

                        if loop_3_last_iter_flg:
                            current_product += ')'
                            next_product += '),\n'
                            ppo_order += f'{current_product} >= {next_product}'
                        else:
                            current_product += f' + '
                            next_product += f' + '

        # exit()
        return ppo_order

    def z3_generate_forall_solver_redundancy_constraints_double_no_care_subxpat_shared(self):
        """
        sth like this (imagine pit equals k+1)
        Implies(p_pr0_i0_l, p_pr0_i0_s), Implies(p_pr0_i1_l, p_pr0_i1_s), ... Implies(p_pr0_in_l, p_pr0_in_s),
        Implies(p_pr1_i0_l, p_pr1_i0_s), Implies(p_pr1_i1_l, p_pr1_i1_s), ... Implies(p_pr1_in_l, p_pr1_in_s),
        ...
        Implies(p_prk_i0_l, p_prk_i0_s), Implies(p_prk_i1_l, p_prk_i1_s), ... Implies(p_prk_in_l, p_prk_in_s),
        """
        double = ''
        double += f'{TAB}{TAB}# remove double no-care\n'

        for pit_idx in range(self.pit):  # the number of lines
            double += f"{TAB}{TAB}"
            for input_idx in range(self.graph.subgraph_num_inputs):
                loop_2_last_iter_flg = pit_idx == self.pit - 1
                loop_3_last_iter_flg = input_idx == self.graph.subgraph_num_inputs - 1
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                double += f'{IMPLIES}({p_l}, {p_s}), '

                if loop_3_last_iter_flg:
                    double += f'\n'

        return double

    def z3_generate_forall_solver_redundancy_constraints_double_no_care_shared(self):
        """
        sth like this (imagine pit equals k+1)
        Implies(p_pr0_i0_l, p_pr0_i0_s), Implies(p_pr0_i1_l, p_pr0_i1_s), ... Implies(p_pr0_in_l, p_pr0_in_s),
        Implies(p_pr1_i0_l, p_pr1_i0_s), Implies(p_pr1_i1_l, p_pr1_i1_s), ... Implies(p_pr1_in_l, p_pr1_in_s),
        ...
        Implies(p_prk_i0_l, p_prk_i0_s), Implies(p_prk_i1_l, p_prk_i1_s), ... Implies(p_prk_in_l, p_prk_in_s),
        """
        double = ''
        double += f'{TAB}{TAB}# remove double no-care\n'

        for pit_idx in range(self.pit):  # the number of lines
            double += f"{TAB}{TAB}"
            for input_idx in range(self.graph.num_inputs):
                loop_2_last_iter_flg = pit_idx == self.pit - 1
                loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                double += f'{IMPLIES}({p_l}, {p_s}), '

                if loop_3_last_iter_flg:
                    double += f'\n'

        return double

    def z3_generate_forall_solver_redundancy_constraints_double_no_care(self):
        double = ''
        double += f'{TAB}{TAB}# remove double no-care\n'
        for output_idx in range(self.graph.num_outputs):
            double += f"{TAB}{TAB}"
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.graph.num_inputs):
                    loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                    p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    double += f'{IMPLIES}({p_l}, {p_s}), '

                    if loop_2_last_iter_flg and loop_3_last_iter_flg:
                        double += f'\n'

        return double

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_subxpat_shared(self):
        """
        We have to generate something like this:
        # 		Implies(Not(p_o0), Not(Or(p_pr0_o0, p_pr1_o0, ..., p_prk_o0))),
        # 		Implies(Not(p_o1), Not(Or(p_pr0_o1, p_pr1_o1, ..., p_prk_o1)))
        # 			...
        # 		Implies(Not(p_om), Not(Or(p_pr0_om, p_pr1_om, ..., p_prk_om)))
        """
        const_zero_perm = ''
        const_zero_perm += f'{TAB}{TAB}# remove constant 0 parameters permutations\n'
        for output_idx in range(self.graph.subgraph_num_outputs):
            const_zero_perm += f"{TAB}{TAB}{IMPLIES}({Z3_NOT}({SHARED_PARAM_PREFIX}_{SHARED_OUTPUT_PREFIX}{output_idx}), {Z3_NOT}({Z3_OR}("
            for pit_idx in range(self.pit):
                loop_1_last_iter_flg = output_idx == self.graph.subgraph_num_outputs - 1
                loop_2_last_iter_flg = pit_idx == self.pit - 1
                pto = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                const_zero_perm += f'{pto}'

                if loop_2_last_iter_flg:
                    const_zero_perm += f'))), \n'
                else:
                    const_zero_perm += f', '

        return const_zero_perm

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation_shared(self):
        """
        We have to generate something like this:
        # 		Implies(Not(p_o0), Not(Or(p_pr0_o0, p_pr1_o0, ..., p_prk_o0))),
        # 		Implies(Not(p_o1), Not(Or(p_pr0_o1, p_pr1_o1, ..., p_prk_o1)))
        # 			...
        # 		Implies(Not(p_om), Not(Or(p_pr0_om, p_pr1_om, ..., p_prk_om)))
        """
        const_zero_perm = ''
        const_zero_perm += f'{TAB}{TAB}# remove constant 0 parameters permutations\n'
        for output_idx in range(self.graph.num_outputs):
            const_zero_perm += f"{TAB}{TAB}{IMPLIES}({Z3_NOT}({SHARED_PARAM_PREFIX}_{SHARED_OUTPUT_PREFIX}{output_idx}), {Z3_NOT}({Z3_OR}("
            for pit_idx in range(self.pit):
                loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                loop_2_last_iter_flg = pit_idx == self.pit - 1
                pto = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                const_zero_perm += f'{pto}'

                if loop_2_last_iter_flg:
                    const_zero_perm += f'))), \n'
                else:
                    const_zero_perm += f', '

        return const_zero_perm

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation(self):
        const_zero_perm = ''
        const_zero_perm += f'{TAB}{TAB}# remove constant 0 parameters permutations\n'
        for output_idx in range(self.graph.num_outputs):
            const_zero_perm += f"{TAB}{TAB}{IMPLIES}({Z3_NOT}({PRODUCT_PREFIX}{output_idx}), {Z3_NOT}({Z3_OR}("
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.graph.num_inputs):
                    loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                    p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    const_zero_perm += f'{p_s}, {p_l}'
                    if loop_2_last_iter_flg and loop_3_last_iter_flg:
                        const_zero_perm += f'))),\n'
                    else:
                        const_zero_perm += f', '
        return const_zero_perm

    def z3_generate_forall_solver_redundancy_constraints_remove_unused_products_subxpat_shared(self):
        """
        sth like this (if pit equals k+1):
        Implies(Not(Or(p_pr0_o0, p_pr0_o1, ..., p_pr0_om)), Not(Or(p_pr0_i0_l, p_pr0_i0_s, ..., p_pr0_in_l, p_pr0_in_s))),
        Implies(Not(Or(p_pr1_o0, p_pr1_o1, ..., p_pr1_om)), Not(Or(p_pr1_i0_l, p_pr1_i0_s, ..., p_pr1_in_l, p_pr1_in_s))),
        ...
        Implies(Not(Or(p_prk_o0, p_prk_o1, ..., p_prk_om)), Not(Or(p_prk_i0_l, p_prk_i0_s, ..., p_prk_in_l, p_prk_in_s))),
        """
        unused_products = f'{TAB}{TAB}# remove unused products\n'
        for pit_idx in range(self.pit):
            loop1_last_iter_flg = pit_idx == self.pit - 1
            unused_products += f'{TAB}{TAB}{IMPLIES}({Z3_NOT}({Z3_OR}('
            for output_idx in range(self.graph.subgraph_num_outputs):
                unused_products += f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                if output_idx == self.graph.subgraph_num_outputs - 1:
                    unused_products += f')), '
                else:
                    unused_products += f', '

            unused_products += f'{Z3_NOT}({Z3_OR}('
            for input_idx in range(self.graph.subgraph_num_inputs):
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                unused_products += f'{p_l}, {p_s}'
                if input_idx == self.graph.subgraph_num_inputs - 1:
                    unused_products += f'))), \n'
                else:
                    unused_products += f', '

        return unused_products

    def z3_generate_forall_solver_redundancy_constraints_remove_unused_products_shared(self):
        """
        sth like this (if pit equals k+1):
        Implies(Not(Or(p_pr0_o0, p_pr0_o1, ..., p_pr0_om)), Not(Or(p_pr0_i0_l, p_pr0_i0_s, ..., p_pr0_in_l, p_pr0_in_s))),
        Implies(Not(Or(p_pr1_o0, p_pr1_o1, ..., p_pr1_om)), Not(Or(p_pr1_i0_l, p_pr1_i0_s, ..., p_pr1_in_l, p_pr1_in_s))),
        ...
        Implies(Not(Or(p_prk_o0, p_prk_o1, ..., p_prk_om)), Not(Or(p_prk_i0_l, p_prk_i0_s, ..., p_prk_in_l, p_prk_in_s))),
        """
        unused_products = f'{TAB}{TAB}# remove unused products\n'
        for pit_idx in range(self.pit):
            loop1_last_iter_flg = pit_idx == self.pit - 1
            unused_products += f'{TAB}{TAB}{IMPLIES}({Z3_NOT}({Z3_OR}('
            for output_idx in range(self.graph.num_outputs):
                unused_products += f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_OUTPUT_PREFIX}{output_idx}'
                if output_idx == self.graph.num_outputs - 1:
                    unused_products += f')), '
                else:
                    unused_products += f', '

            unused_products += f'{Z3_NOT}({Z3_OR}('
            for input_idx in range(self.graph.num_inputs):
                p_l = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_s'
                p_s = f'{SHARED_PARAM_PREFIX}_{SHARED_PRODUCT_PREFIX}{pit_idx}_{SHARED_INPUT_LITERAL_PREFIX}{input_idx}_l'
                unused_products += f'{p_l}, {p_s}'
                if input_idx == self.graph.num_inputs - 1:
                    unused_products += f'))), \n'
                else:
                    unused_products += f', '

        return unused_products

    def z3_generate_forall_solver_subxpat_shared(self):
        prep = self.z3_generate_forall_solver_preperation()
        error = self.z3_generate_forall_solver_error_constraint()
        circuits = self.z3_generate_forall_solver_circuits()
        atmost_constraints = self.z3_generate_forall_solver_atmost_constraints_subxpat_shared()
        redundancy_constraints = self.z3_generate_forall_solver_redundancy_constraints_subxpat_shared()
        prep += '\n'
        error += '\n'
        circuits += '\n'
        atmost_constraints += '\n'
        redundancy_constraints += '\n'
        forall_solver = prep + error + circuits + atmost_constraints + redundancy_constraints

        return forall_solver

    def z3_generate_forall_solver_shared(self):
        prep = self.z3_generate_forall_solver_preperation()
        error = self.z3_generate_forall_solver_error_constraint()
        circuits = self.z3_generate_forall_solver_circuits()
        atmost_constraints = self.z3_generate_forall_solver_atmost_constraints_shared()
        redundancy_constraints = self.z3_generate_forall_solver_redundancy_constraints_shared()
        prep += '\n'
        error += '\n'
        circuits += '\n'
        atmost_constraints += '\n'
        redundancy_constraints += '\n'
        forall_solver = prep + error + circuits + atmost_constraints + redundancy_constraints

        return forall_solver

    def z3_generate_forall_solver(self):
        prep = self.z3_generate_forall_solver_preperation()
        error = self.z3_generate_forall_solver_error_constraint()
        circuits = self.z3_generate_forall_solver_circuits()
        atmost_constraints = self.z3_generate_forall_solver_atmost_constraints()
        redundancy_constraints = self.z3_generate_forall_solver_redundancy_constraints()
        prep += '\n'
        error += '\n'
        circuits += '\n'
        atmost_constraints += '\n'
        redundancy_constraints += '\n'
        forall_solver = prep + error + circuits + atmost_constraints + redundancy_constraints

        return forall_solver

    # NM
    def z3_generate_verification_solver(self):
        verification_solver = ''
        verification_solver += f'{VERIFICATION_SOLVER} = {SOLVER}\n' \
                               f'{VERIFICATION_SOLVER}.{ADD}(\n' \
                               f'{TAB}{ERROR} == {DIFFERENCE},\n' \
                               f'{TAB}{EXACT_CIRCUIT},\n' \
                               f'{TAB}{APPROXIMATE_CIRCUIT},\n' \
                               f')\n'
        return verification_solver

    # NM
    def z3_generate_parameter_constraint_list(self):
        parameter_list = ''
        parameter_list += f'parameters_constraints: List[Tuple[BoolRef, bool]] = []\n'
        return parameter_list

    # NM
    def z3_generate_find_wanted_number_of_models(self):
        prep_loop1 = self.z3_generate_find_wanted_number_of_models_prep_loop1()
        prep_loop2 = self.z3_generate_find_wanted_number_of_models_prep_loop2()
        prep_loop3 = self.z3_generate_find_wanted_number_of_models_prep_loop3()
        final_prep = self.z3_generate_find_wanted_number_of_models_final_prep()
        prep_loop1 += '\n'
        prep_loop2 += '\n'
        prep_loop3 += '\n'
        final_prep += '\n'
        find_wanted_number_of_models = prep_loop1 + prep_loop2 + prep_loop3 + final_prep
        return find_wanted_number_of_models

    # NM
    def z3_generate_find_wanted_number_of_models_prep_loop1(self):
        prep_loop1 = ''
        prep_loop1 += f'found_data = []\n' \
                      f'while(len(found_data) < wanted_models and timeout > 0):\n' \
                      f'{TAB}time_total_start = time()\n' \
                      f'{TAB}\n' \
                      f'{TAB}attempts = 1\n' \
                      f'{TAB}result: CheckSatResult = None\n' \
                      f'{TAB}attempts_times: List[Tuple[float, float, float]] = []\n'

        return prep_loop1

    # NM
    def z3_generate_find_wanted_number_of_models_prep_loop2(self):
        find_valid_model = ''
        find_valid_model += f'{TAB}while result != sat:\n' \
                            f'{TAB}{TAB}time_attempt_start = time()\n' \
                            f'{TAB}{TAB}time_parameters_start = time_attempt_start\n'

        find_valid_model += f'{TAB}{TAB}# add constrain to prevent the same parameters to happen\n' \
                            f'{TAB}{TAB}if parameters_constraints:\n' \
                            f'{TAB}{TAB}{TAB}forall_solver.add(Or(*map(lambda x: x[0] != x[1], parameters_constraints)))\n'

        find_valid_model += f'{TAB}{TAB}parameters_constraints = []\n'
        find_valid_model += f"{TAB}{TAB}forall_solver.set(\"timeout\", int(timeout * 1000))\n" \
                            f"{TAB}{TAB}result = forall_solver.check()\n" \
                            f"{TAB}{TAB}time_parameters = time() - time_attempt_start\n" \
                            f"{TAB}{TAB}time_attempt = time() - time_attempt_start\n" \
                            f"{TAB}{TAB}timeout -= time_parameters # removed the time used from the timeout\n"
        find_valid_model += f'{TAB}{TAB}if result != sat:\n' \
                            f'{TAB}{TAB}{TAB}attempts_times.append((time_attempt, time_parameters, None))\n' \
                            f'{TAB}{TAB}{TAB}break\n'
        find_valid_model += f'{TAB}{TAB}m = forall_solver.model()\n' \
                            f'{TAB}{TAB}parameters_constraints = []\n' \
                            f'{TAB}{TAB}for k, v in map(lambda k: (k, m[k]), m):\n' \
                            f'{TAB}{TAB}{TAB}if str(k)[0] == "p":\n' \
                            f'{TAB}{TAB}{TAB}{TAB}parameters_constraints.append((Bool(str(k)), v))\n'

        find_valid_model += f'{TAB}{TAB}# verify parameters\n' \
                            f'{TAB}{TAB}WCE: int = None\n' \
                            f'{TAB}{TAB}verification_ET: int = 0\n' \
                            f'{TAB}{TAB}time_verification_start = time()\n' \
                            f'{TAB}{TAB}# save state\n' \
                            f'{TAB}{TAB}verification_solver.push()\n' \
                            f'{TAB}{TAB}# parameters constraints\n' \
                            f'{TAB}{TAB}verification_solver.add(\n' \
                            f'{TAB}{TAB}{TAB}*map(lambda x: x[0] == x[1], parameters_constraints),\n' \
                            f'{TAB}{TAB})\n'

        return find_valid_model

    # NM
    def z3_generate_find_wanted_number_of_models_prep_loop3(self):
        prep_loop3 = f'{TAB}{TAB}while verification_ET < max_possible_ET:\n' \
                     f'{TAB}{TAB}{TAB}# add constraint\n' \
                     f'{TAB}{TAB}{TAB}verification_solver.add(difference > verification_ET)\n' \
                     f'{TAB}{TAB}{TAB}# run solver\n' \
                     f'{TAB}{TAB}{TAB}verification_solver.set("timeout", int(timeout * 1000))\n' \
                     f'{TAB}{TAB}{TAB}v_result = verification_solver.check()\n'

        prep_loop3 += f'{TAB}{TAB}{TAB}if v_result == unsat:\n' \
                      f'{TAB}{TAB}{TAB}{TAB}# unsat, WCE found\n' \
                      f'{TAB}{TAB}{TAB}{TAB}WCE = verification_ET\n' \
                      f'{TAB}{TAB}{TAB}{TAB}break\n'

        prep_loop3 += f'{TAB}{TAB}{TAB}elif v_result == sat:\n' \
                      f'{TAB}{TAB}{TAB}{TAB}# sat, need to search again\n' \
                      f'{TAB}{TAB}{TAB}{TAB}m = verification_solver.model()\n' \
                      f'{TAB}{TAB}{TAB}{TAB}verification_ET = m[error].as_long()\n' \
                      f'{TAB}{TAB}{TAB}else:\n' \
                      f'{TAB}{TAB}{TAB}{TAB} # unknown (probably a timeout)\n' \
                      f'{TAB}{TAB}{TAB}{TAB}WCE = -1\n' \
                      f'{TAB}{TAB}{TAB}{TAB}break\n'

        return prep_loop3

    # NM
    def z3_generate_find_wanted_number_of_models_final_prep(self):
        final_prep = ''
        final_prep += f'{TAB}{TAB}if WCE is None:\n' \
                      f'{TAB}{TAB}{TAB}WCE = max_possible_ET\n'

        final_prep += f'{TAB}{TAB}# revert state\n' \
                      f'{TAB}{TAB}verification_solver.pop()\n' \
                      f'{TAB}{TAB}time_verification = time() - time_verification_start\n' \
                      f'{TAB}{TAB}time_attempt = time() - time_attempt_start\n' \
                      f'{TAB}{TAB}timeout -= time_verification  # remove the time used from the timeout\n' \
                      f'{TAB}{TAB}attempts_times.append((time_attempt, time_parameters, time_verification))\n' \
                      f'{TAB}{TAB}\n'

        final_prep += f'{TAB}{TAB}# ==== continue or exit\n' \
                      f'{TAB}{TAB}if WCE > ET:\n' \
                      f'{TAB}{TAB}{TAB}result = None\n' \
                      f'{TAB}{TAB}{TAB}attempts += 1\n' \
                      f'{TAB}{TAB}{TAB}invalid_parameters = parameters_constraints\n' \
                      f'{TAB}{TAB}elif WCE < 0:  # caused by unknown\n' \
                      f'{TAB}{TAB}{TAB}break\n'

        return final_prep

    # NM
    def z3_generate_store_data(self):
        store_data = ''
        store_data += f'{TAB}# store data\n'
        extract_info = self.z3_generate_store_data_define_extract_info_function()
        key_function = self.z3_generate_store_data_define_extract_key_function()
        stats = self.z3_generate_stats()
        results = self.z3_dump_results_onto_json()
        extract_info += '\n'
        key_function += '\n'
        stats += '\n'
        results += '\n'
        store_data += extract_info + key_function + stats + results
        return store_data

    # NM
    def z3_generate_store_data_define_extract_info_function(self):
        extract_info = ''
        extract_info += f'{TAB}def extract_info(pattern: Union[Pattern, str], string: str,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}parser: Callable[[Any], Any] = lambda x: x,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}default: Union[Callable[[], None], Any] = None) -> Any:\n' \
                        f'{TAB}{TAB}import re\n' \
                        f'{TAB}{TAB}return (parser(match[1]) if (match := re.search(pattern, string))\n' \
                        f'{TAB}{TAB}{TAB}{TAB}else (default() if callable(default) else default))\n'

        return extract_info

    # NM
    def z3_generate_store_data_define_extract_key_function(self):
        """
        :return:
        """
        key_function = ''
        key_function += f"{TAB}def key_function(parameter_constraint):\n" \
                        f'{TAB}{TAB}p = str(parameter_constraint[0])\n' \
                        f"{TAB}{TAB}o_id = extract_info(r'_o(\d+)', p, int, -1)\n" \
                        f"{TAB}{TAB}pr_id = extract_info(r'_pr(\d+)', p, int, 0)\n" \
                        f"{TAB}{TAB}i_id = extract_info(r'_i(\d+)', p, int, 0)\n" \
                        f"{TAB}{TAB}typ = extract_info(r'_(l|s)', p, {{'s': 1, 'l': 2}}.get, 0)\n" \
                        f'{TAB}{TAB}if o_id < 0:\n' \
                        f'{TAB}{TAB}{TAB}return (pr_id * 1000 + i_id * 10 + typ)\n' \
                        f'{TAB}{TAB}return (o_id * 100000\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ pr_id * 1000\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ i_id * 10\n' \
                        f'{TAB}{TAB}{TAB}{TAB}+ typ)\n'

        return key_function

    # NM
    def z3_generate_stats(self):
        stats = ''
        stats += f'{TAB}time_total = time() - time_total_start\n'
        stats += f'{TAB}data_object = {{\n' \
                 f"{TAB}{TAB}'result': str(result),\n" \
                 f"{TAB}{TAB}'total_time': time_total,\n" \
                 f"{TAB}{TAB}'attempts': attempts,\n" \
                 f"{TAB}{TAB}'attempts_times': [list(map(lambda tup: [*tup], attempts_times))]\n" \
                 f"{TAB}}}\n"

        stats += f'{TAB}if result == sat:\n' \
                 f"{TAB}{TAB}data_object['model'] = dict(map(lambda item: (str(item[0]), is_true(item[1])),\n" \
                 f"{TAB}{TAB}{TAB}sorted(parameters_constraints,\n" \
                 f"{TAB}{TAB}{TAB}key=key_function)))\n"

        stats += f'{TAB}found_data.append(data_object)\n' \
                 f'{TAB}if result != sat:\n' \
                 f'{TAB}{TAB}break\n'

        # stats += f'print(json.dumps(found_data, separators=(",", ":"),))\n'

        return stats

    # NM
    def z3_generate_config(self):
        config = ''
        config += f'ET = int(sys.argv[1])\n' \
                  f'wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])\n' \
                  f'timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])\n' \
                  f'max_possible_ET: int = 2 ** 3 - 1\n' \
                  f'\n'

        return config

    # NM
    def z3_dump_results_onto_json(self):
        results = ''

        results += f"with open('{self.json_out_path}', 'w') as ofile:\n" \
                   f"{TAB}ofile.write(json.dumps(found_data, separators=(\",\", \":\"), indent=4))\n"
        return results
