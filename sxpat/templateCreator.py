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
from .config import paths as sxpatpaths
from .annotatedGraph import AnnotatedGraph

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
        temp_graph_obj = AnnotatedGraph(self.benchmark_name, is_clean=False)
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
        self.__json_out_path = self.set_path(sxpatpaths.OUTPUT_PATH['json'])

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

    @property
    def json_out_path(self):
        return self.__json_out_path

    def set_path(self, this_path: Tuple[str, str]):
        folder, extenstion = this_path
        return f'{folder}/{self.benchmark_name}_{LPP}{self.lpp}_{PPO}{self.ppo}_{self.template_name}.{extenstion}'

    def export_z3pyscript(self):
        print(f'Storing in {self.z3_out_path}')
        with open(self.z3_out_path, 'w') as z:
            z.writelines(self.z3pyscript)

    def z3_generate_z3pyscript(self):
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
                                       f", {BOOLSORT}" \
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

    def get_predecessors(self, node: str) -> List[str]:
        return list(self.graph.graph.predecessors(node))

    def get_logical_function(self, node: str) -> str:
        return self.graph.graph.nodes[node][LABEL]

    def z3_express_node_as_wire_constraints(self, node: str):
        assert node in list(self.graph.input_dict.values()) or node in list(self.graph.gate_dict.values()) \
               or node in list(self.graph.output_dict.values())
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

    def z3_generate_exact_circuit_wire_constraints(self):
        exact_wire_constraints = f'{EXACT_CIRCUIT} = And(\n'

        for g_idx in range(self.graph.num_gates):
            g_label = self.graph.gate_dict[g_idx]
            g_predecessors = self.get_predecessors(g_label)
            g_function = self.get_logical_function(g_label)

            assert len(g_predecessors) == 1 or len(g_predecessors) == 2
            assert g_function == NOT or g_function == AND or g_function == OR
            if len(g_predecessors) == 1:
                if g_predecessors[0] in list(self.graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:

                    pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.graph.input_dict.values()))}) == "

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
            else:
                exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.graph.num_inputs + g_idx}(" \
                                          f"{','.join(list(self.graph.input_dict.values()))}) == "

                if g_predecessors[0] in list(self.graph.input_dict.values()):
                    pred_1 = g_predecessors[0]
                else:
                    pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])
                if g_predecessors[1] in list(self.graph.input_dict.values()):
                    pred_2 = g_predecessors[1]
                else:
                    pred_2 = self.z3_express_node_as_wire_constraints(g_predecessors[1])

                exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
        return exact_wire_constraints

    def z3_generate_exact_circuit_output_constraints(self):
        exact_output_constraints = ''
        for output_idx in self.graph.output_dict.keys():
            output_label = self.graph.output_dict[output_idx]
            output_predecessors = list(self.graph.graph.predecessors(output_label))
            assert len(output_predecessors) == 1
            pred = self.z3_express_node_as_wire_constraints(output_predecessors[0])
            output = self.z3_express_node_as_wire_constraints(output_label)
            exact_output_constraints += f'{TAB}{output} == {pred},\n'
        return exact_output_constraints

    def z3_generate_exact_circuit_integer_output_constraints(self):
        exact_integer_outputs = f"{TAB}{F_EXACT}({','.join(self.graph.input_dict.values())}) == \n"

        for idx in range(self.graph.num_outputs):
            output_label = self.graph.output_dict[idx]
            if idx == self.graph.num_outputs - 1:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints(output_label)},\n"
            else:
                exact_integer_outputs += f"{TAB}{2 ** idx} * {self.z3_express_node_as_wire_constraints(output_label)} +\n"
        return exact_integer_outputs

    def z3_generate_exact_circuit_constraints(self):
        exact_circuit_constraints = ''
        wires = self.z3_generate_exact_circuit_wire_constraints()
        outputs = self.z3_generate_exact_circuit_output_constraints()
        integer_outputs = self.z3_generate_exact_circuit_integer_output_constraints()
        wires += '\n'
        outputs += '\n'
        integer_outputs += '\n'
        exact_circuit_constraints = wires + outputs + integer_outputs + ')\n'

        return exact_circuit_constraints

    def z3_generate_approximate_circuit_constraints(self):
        approximate_circuit_constraints = f'{APPROXIMATE_CIRCUIT} = {Z3_AND}(\n'
        approximate_circuit_constraints += f"{TAB}{F_APPROXIMATE}({','.join(self.graph.input_dict.values())}) == \n"
        approximate_circuit_constraints += f"{TAB}{SUM}("
        for o_idx in range(self.graph.num_outputs):
            if o_idx > 0:
                approximate_circuit_constraints += f"{TAB}{TAB}"  # fixing the indentations
            approximate_circuit_constraints += f"{INTVAL}({2 ** o_idx}) * {Z3_AND} ( {PRODUCT_PREFIX}{o_idx}, {Z3_OR}({Z3_AND}("
            for ppo_idx in range(self.ppo):
                for input_idx in range(self.graph.num_inputs):
                    p_s = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    p_l = f'{PRODUCT_PREFIX}{o_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'

                    loop_1_last_iter_flg = o_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1

                    approximate_circuit_constraints += f'{Z3_OR}({Z3_NOT}({p_s}), {p_l} == {self.graph.input_dict[input_idx]})'

                    if loop_1_last_iter_flg and loop_2_last_iter_flg and loop_3_last_iter_flg:
                        approximate_circuit_constraints += '))))\n)\n'
                    elif loop_3_last_iter_flg and loop_2_last_iter_flg:
                        approximate_circuit_constraints += '))),\n'
                    else:
                        approximate_circuit_constraints += ','
        return approximate_circuit_constraints

    def z3_generate_forall_solver(self):
        forall_solver = ''
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

    def z3_generate_forall_solver_preperation(self):
        prep = ''
        prep += f'{FORALL_SOLVER} = {SOLVER}\n' \
                f'{FORALL_SOLVER}.{ADD}({FORALL}(\n' \
                f"{TAB}[{','.join(list(self.graph.input_dict.values()))}],\n" \
                f"{TAB}{Z3_AND}(\n"
        return prep

    def z3_generate_forall_solver_error_constraint(self):
        error = ''
        error += f'{TAB}{TAB}{DIFFERENCE} <= {ET},\n'
        return error

    def z3_generate_forall_solver_circuits(self):
        circuits = ''
        circuits += f'{TAB}{TAB}{EXACT_CIRCUIT},\n' \
                    f'{TAB}{TAB}{APPROXIMATE_CIRCUIT},\n'
        return circuits

    def z3_generate_forall_solver_atmost_constraints(self):
        atmost = ''

        for output_idx in range(self.graph.num_outputs):
            for ppo_idx in range(self.ppo):
                atmost += f"{TAB}{TAB}("
                for input_idx in range(self.graph.num_inputs):
                    loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    atmost += f"{IF}({p_s}, 1, 0)"

                    if loop_3_last_iter_flg:
                        atmost += f') <= {self.ppo},\n'
                    else:
                        atmost += f' + '
        atmost += '\n'

        return atmost

    def z3_generate_forall_solver_redundancy_constraints(self):
        double_no_care = self.z3_generate_forall_solver_redundancy_constraints_double_no_care()
        remove_constant_zero_permutation = self.z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation()
        set_ppo_order = self.z3_generate_forall_solver_redundancy_constraints_set_ppo_order()

        double_no_care += '\n'
        remove_constant_zero_permutation += '\n'
        set_ppo_order += '\n'
        end = f"{TAB})\n))\n"
        redundancy = double_no_care + remove_constant_zero_permutation + set_ppo_order + end
        return redundancy

    def z3_generate_forall_solver_redundancy_constraints_double_no_care(self):
        double = ''
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

    def z3_generate_forall_solver_redundancy_constraints_remove_constant_zero_permutation(self):
        const_zero_perm = ''
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

    def z3_generate_forall_solver_redundancy_constraints_set_ppo_order(self):
        ppo_order = ''
        for output_idx in range(self.graph.num_outputs):
            ppo_order += f"{TAB}{TAB}"
            for ppo_idx in range(self.ppo):
                ppo_order += '('
                for input_idx in range(self.graph.num_inputs):
                    loop_1_last_iter_flg = output_idx == self.graph.num_outputs - 1
                    loop_2_last_iter_flg = ppo_idx == self.ppo - 1
                    loop_3_last_iter_flg = input_idx == self.graph.num_inputs - 1
                    p_l = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{LITERAL_PREFIX}'
                    p_s = f'{PRODUCT_PREFIX}{output_idx}_{TREE_PREFIX}{ppo_idx}_{INPUT_LITERAL_PREFIX}{input_idx}_{SELECT_PREFIX}'
                    ppo_order += f'{INTVAL}({2 ** (2 * input_idx)}) * {p_s} + {INTVAL}({2 ** (2*input_idx + 1)}) * {p_l}'

                    if loop_2_last_iter_flg and loop_3_last_iter_flg:
                        ppo_order += '),\n'
                    elif loop_3_last_iter_flg:
                        ppo_order += ') >= '
                    else:
                        ppo_order += ' + '

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

    def z3_generate_find_wanted_number_of_models_prep_loop1(self):
        prep_loop1 = ''
        prep_loop1+= f'found_data = []\n' \
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
        extract_info = self.z3_generate_sotre_data_define_extract_info_function()
        key_function = self.z3_generate_sotre_data_define_extract_key_function()
        stats = self.z3_generate_stats()
        results = self.z3_dump_results_onto_json()
        extract_info += '\n'
        key_function += '\n'
        stats += '\n'
        results += '\n'
        store_data += extract_info + key_function + stats + results
        return store_data

    def z3_generate_sotre_data_define_extract_info_function(self):
        extract_info = ''
        extract_info += f'{TAB}def extract_info(pattern: Union[Pattern, str], string: str,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}parser: Callable[[Any], Any] = lambda x: x,\n' \
                        f'{TAB}{TAB}{TAB}{TAB}default: Union[Callable[[], None], Any] = None) -> Any:\n' \
                        f'{TAB}{TAB}import re\n' \
                        f'{TAB}{TAB}return (parser(match[1]) if (match := re.search(pattern, string))\n' \
                        f'{TAB}{TAB}{TAB}{TAB}else (default() if callable(default) else default))\n'

        return extract_info

    def z3_generate_sotre_data_define_extract_key_function(self):

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

        results += f"with open('{self.json_out_path}', 'w') as ofile:\n" \
                   f"{TAB}ofile.write(json.dumps(found_data, separators=(\",\", \":\"), indent=4))\n"
        return results

# TODO: Later (Cata)
class Template_SOP1ShareLogic(TemplateCreator):
    def __init__(self, template_specs: TemplateSpecs):
        super().__init__(template_specs)


class Template_MUX(TemplateCreator):
    pass
