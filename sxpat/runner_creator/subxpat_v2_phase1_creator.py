# typing
from __future__ import annotations
from typing import Tuple, List, Iterable

# libs
# from itertools import chain

# Z3Log libs
from Z3Log.config.config import *
from Z3Log.config import path as z3logpath
# from sxpat.annotatedGraph import AnnotatedGraph

# sxpat libs
from sxpat.config.config import *
# from sxpat.config import paths as sxpatpaths
from sxpat.distance_function import DistanceFunction
# from sxpat.runner_creator.xpat_creator_direct import XPatRunnerCreator
from z_marco.ma_graph import MaGraph

# package
from .runner_creator import RunnerCreator
from .utils import format_lines, indent_lines
# from sxpat.graph_utils.extract_subgraph import exctract_subgraph


class SubXPatV2Phase1RunnerCreator(RunnerCreator):
    def __init__(self,
                 # input
                 full_graph: MaGraph,
                 sub_graph: MaGraph,
                 graph_name: str,
                 # parameters
                 circuit_distance_function: DistanceFunction,
                 subcircuit_distance_function: DistanceFunction,
                 *,
                 circuit1_name: str = "c1",  # can be left as default
                 circuit2_name: str = "c2",  # can be left as default
                 ) -> None:

        self.graph = full_graph
        self.subgraph = sub_graph
        self.graph_name = graph_name

        self.c1_name = circuit1_name
        self.c2_name = circuit2_name

        self.circuit_distance_function = circuit_distance_function
        self.subcircuit_distance_function = subcircuit_distance_function

    name = property(lambda _: "V2P1")
    """DEPRECATED"""

    def get_script_name(self) -> str:
        # compute base name
        name = '_'.join([
            self.graph_name,
            f"{NameParameters.DST.value}ful{self.circuit_distance_function.abbreviation}",
            f"{NameParameters.DST.value}sub{self.subcircuit_distance_function.abbreviation}",
            "V2P1"
        ])

        # get folder and extension
        folder, extension = z3logpath.OUTPUT_PATH['z3']

        return f"{folder}/{name}.{extension}"

    # def gen_json_outfile_name(self):
    #     name = '_'.join([
    #         self.graph_name,
    #         f"{NameParameters.DST.value}ful{self.circuit_distance_function_name}",
    #         f"{NameParameters.DST.value}sub{self.subcircuit_distance_function_name}",
    #         "V2P1"
    #     ])
    #     folder, extension = sxpatpaths.OUTPUT_PATH[JSON]
    #     return f"{folder}/{name}.{extension}"

    def generate_script(self) -> str:
        text = format_lines([
            # generics
            *self.gen_imports(),
            "",
            *self.gen_arguments_parsing(),
            "",
            # PHASE 1
            # inputs
            *self.gen_declare_input_variables(),
            "",
            *self.gen_sub_outputs(),
            "",
            # circuits
            *self.gen_exact_circuit_wires(self.c1_name),
            "",
            *self.gen_exact_circuit_outputs(self.c1_name),
            "",
            *self.gen_exact_circuit_wires(self.c2_name),
            "",
            *self.gen_exact_circuit_outputs(self.c2_name),
            "",
            # distance
            *self.gen_distance_functions(),
            "",
            # optimizer
            *self.gen_optimizer(),
            "",
            # output
            *self.gen_output(),
            "",
        ])

        # if path is not None:
        #     with open(path, "w") as f:
        #         f.write(text)
        return text

    def gen_arguments_parsing(self) -> List[str]:
        return [
            f"ET: int = int(sys.argv[1])",
            f"wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])",
            f"timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])",
            # TODO: NOTE: this was the constant `2 ** 3 - 1`
            f"max_possible_ET: int = 2 ** {len(self.graph.outputs)} - 1",
        ]

    def gen_declare_input_variables(self) -> List[str]:
        return [
            "# inputs variables declaration",
            *map(self.declare_z3_gate, self.graph.inputs)
        ]

    def gen_sub_outputs(self):
        def prefixed(prefixes: Iterable[str], strings: Iterable[str]) -> Iterable[str]:
            return map(lambda s: "_".join((*prefixes, s)), strings)

        return [
            f"# Subgraph output variables declaration",
            *(
                self.declare_z3_gate(name)
                for name in prefixed((self.c1_name,), self.subgraph.outputs)
            ),
            *(
                self.declare_z3_gate(name)
                for name in prefixed((self.c2_name,), self.subgraph.outputs)
            )
        ]

    def gen_exact_circuit_wires(self, prefix: str) -> List[str]:
        subout_preds = {self.subgraph.predecessors(n)[0]: n for n in self.subgraph.outputs}

        lines = []
        for gate_name in self.graph.gates:

            if gate_name in subout_preds:
                lines.append(f"{prefix}_{gate_name} = {prefix}_{subout_preds[gate_name]}")
                continue

            gate_preds = [
                name if name in self.graph.inputs else f"{prefix}_{name}"
                for name in self.graph.predecessors(gate_name)
            ]
            gate_func = self.graph.function_of(gate_name)

            assert len(gate_preds) in [1, 2], "A gate must have exactly 1 or 2 predecessors."
            assert gate_func in [NOT, AND, OR], "Unknown gate function."

            lines.append(f"{prefix}_{gate_name} = z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)})")

        return [
            "# exact circuit gates",
            *lines
        ]

    def gen_exact_circuit_outputs(self, prefix: str):
        lines = []
        for out_name in self.graph.outputs:
            out_preds = [
                name if name in self.graph.inputs else f"{prefix}_{name}"
                for name in self.graph.predecessors(out_name)
            ]

            assert len(out_preds) == 1, "An output cannot have multiple predecessors."

            lines.append(f"{prefix}_{out_name} = {out_preds[0]}")

        return [
            "# exact circuit outputs",
            *lines
        ]

    def gen_distance_functions(self):
        cir_vars_1 = [f"{self.c1_name}_{name}" for name in self.graph.outputs]
        cir_vars_2 = [f"{self.c2_name}_{name}" for name in self.graph.outputs]
        sub_vars_1 = [f"{self.c1_name}_{name}" for name in self.subgraph.outputs]
        sub_vars_2 = [f"{self.c2_name}_{name}" for name in self.subgraph.outputs]

        return [
            "# Distance variables",
            *self.circuit_distance_function.declare(cir_vars_1, cir_vars_2, "cir"),
            "",
            *self.subcircuit_distance_function.declare(sub_vars_1, sub_vars_2, "sub"),
        ]

    def gen_optimizer(self):
        return [
            f"# optimizer",
            f"optimizer = z3.Optimize()",
            f"",
            f"# add constraints",
            f"optimizer.add(cir_out_dist > ET)",
            f"",
            f"# setup objective",
            f"objective = optimizer.minimize(sub_out_dist)",
            f"",
            f"# optimize",
            f"result = optimizer.check()",
            f"optimizer.lower(objective)",
            f"",
            f"# extract wanted distance",
            f"model = optimizer.model()",
        ]

    def gen_output(self):

        return [
            f"# print results",
            f"print(result)",
            f"print(model.evaluate(sub_out_dist) if result == z3.sat else '')",
            # f"print('e = cir_out_dist =', model.evaluate(cir_out_dist))",
            # f"print('d = sub_out_dist =', model.evaluate(sub_out_dist))",
        ]

    # # ! DOING ABOVE HERE

    # def get_cir_out(self, c_name: str = None, vars: Iterable[str] = None):
    #     c_name = "" if c_name is None else f"{c_name}_"
    #     vars = map(lambda v: EXACT_OUTPUT_PREFIX+v, self.current_graph.output_dict.values()) if vars is None else vars
    #     return [
    #         f"{c_name}{name}"
    #         for name in vars
    #     ]

    # def get_sub_out(self, c_name: str = None, vars: Iterable[str] = None):
    #     c_name = "" if c_name is None else f"{c_name}_sub_"
    #     vars = list(self.current_graph.subgraph_output_dict.values() if vars is None else vars)
    #     return [
    #         f"{c_name}{name}"
    #         for name in vars
    #     ]

    # def setup_distance_functions(self) -> List[int]:
    #     nodes = self.current_graph.subgraph.nodes
    #     weights = [nodes[n][WEIGHT] for n in self.get_sub_out()]

    #     self.cir_dist_func = IntegerAbsoluteDifference(len(self.get_cir_out()))
    #     self.sub_dist_func = WeightedAbsoluteDifference(weights)

    # def z3_generate_exact_circuit_constraints(self, c_name: str):
    #     return format_lines([
    #         self.z3_generate_exact_circuit_wire_constraints(c_name),    # wires
    #         self.z3_generate_exact_circuit_output_constraints(c_name),  # outputs
    #         ")"
    #     ])

    # def prefixed_name(self, raw: str, c_name: str) -> str:
    #     if raw in self.exact_graph.input_dict.values():
    #         return raw
    #     return f"{c_name}_{self.z3_express_node_as_wire_constraints(raw)}"

    # def z3_generate_exact_circuit_wire_constraints(self, c_name: str):
    #     def prefixed_name(raw): return self.prefixed_name(raw, c_name)

    #     lines = []
    #     lines.extend([f'# exact circuit constraints',
    #                   f'{c_name} = And(',
    #                   f'{TAB}# wires'])

    #     for g_idx in range(self.exact_graph):
    #         g_label = self.exact_graph.gate_dict[g_idx]
    #         g_predecessors = self.get_predecessors(g_label)
    #         g_function = self.get_logical_function(g_label)

    #         if g_label in self.current_graph.subgraph_output_dict.values():
    #             lines.append(
    #                 f"{TAB}{c_name}_{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}"
    #                 f"({','.join(self.exact_graph.input_dict.values())})"
    #                 f" == {c_name}_sub_{g_label},"
    #             )
    #             continue

    #         assert len(g_predecessors) == 1 or len(g_predecessors) == 2
    #         assert g_function in (NOT, AND, OR)

    #         if len(g_predecessors) == 1:
    #             pred_1 = prefixed_name(g_predecessors[0])
    #             lines.append(
    #                 f"{TAB}{c_name}_{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}"
    #                 f"({','.join(self.exact_graph.input_dict.values())})"
    #                 f" == {TO_Z3_GATE_DICT[g_function]}({pred_1}),"
    #             )

    #         else:
    #             pred_1 = prefixed_name(g_predecessors[0])
    #             pred_2 = prefixed_name(g_predecessors[1])
    #             lines.append(
    #                 f"{TAB}{c_name}_{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}"
    #                 f"({','.join(self.exact_graph.input_dict.values())})"
    #                 f" == {TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),"
    #             )

    #     return format_lines(lines)

    # def z3_generate_exact_circuit_output_constraints(self, c_name: str):
    #     exact_output_constraints = ''
    #     exact_output_constraints += f'{TAB}# boolean outputs (from the least significant)\n'
    #     for output_idx in self.exact_graph.output_dict.keys():
    #         output_label = self.exact_graph.output_dict[output_idx]
    #         output_predecessors = list(self.exact_graph.graph.predecessors(output_label))
    #         assert len(output_predecessors) == 1

    #         if output_predecessors[0] in list(self.exact_graph.input_dict.values()):
    #             pred = self.z3_express_node_as_wire_constraints(output_predecessors[0])
    #         else:
    #             pred = f"{c_name}_{self.z3_express_node_as_wire_constraints(output_predecessors[0])}"
    #         output = self.z3_express_node_as_wire_constraints(output_label)
    #         exact_output_constraints += f'{TAB}{c_name}_{output} == {pred},\n'
    #     return exact_output_constraints

    # def z3_generate_exact_circuit_outputs_declaration(self, c_name: str):
    #     return format_lines(
    #         [
    #             f"# outputs functions declaration for exact circuit",
    #             *(
    #                 (
    #                     f"{c_name}_{EXACT_OUTPUT_PREFIX}{OUT}{output_idx} = {FUNCTION} "
    #                     f"('{c_name}_{EXACT_OUTPUT_PREFIX}{OUT}{output_idx}', {', '.join(repeat(BOOLSORT, self.current_graph.num_inputs + 1))})"
    #                 )
    #                 for output_idx in range(self.current_graph.num_outputs)
    #             )
    #         ],
    #         extra_newlines=1
    #     )

    # def z3_generate_exact_circuit_wires_declaration(self, c_name: str):
    #     return format_lines([
    #         f"# wires functions declaration for exact circuit",
    #         *(
    #             (
    #                 f"{c_name}_{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx} = "
    #                 f"{FUNCTION}('{c_name}_{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}', "
    #                 f"{', '.join(repeat(BOOLSORT, self.exact_graph.num_inputs))}, {BOOLSORT})"
    #             )
    #             for g_idx in range(self.exact_graph.num_gates)
    #         )
    #     ])

    # def z3_generate_utility_variables(self):
    #     return format_lines([
    #         f'# utility variables',
    #         f"error = {Z3INT}('error')",
    #     ])

    # def generate_z3py_suboutput_variables(self, c_name: str):
    #     return format_lines([
    #         f"# Subgraph output variables declaration",
    #         *(
    #             self.declare_gate(name).strip()
    #             for name in self.get_sub_out(c_name)
    #         )
    #     ])

    # def z3_generate_distance_declaration(self):
    #     return format_lines([
    #         "# Distance variables",
    #         f"cir_out_dist = {Z3INT}('cir_out_dist')",
    #         *self.cir_dist_func.declaration_function("cir"),
    #         f"sub_out_dist = {Z3INT}('sub_out_dist')",
    #         *self.sub_dist_func.declaration_function("sub")
    #     ])

    # def z3_generate_distance_definition(self):
    #     fun_cir_vars = [
    #         f"{EXACT_OUTPUT_PREFIX}{v[1:]}({','.join(list(self.exact_graph.input_dict.values()))})"
    #         for v in self.get_cir_out()
    #     ]

    #     cir_vars_1 = self.get_cir_out(self.c1_name, fun_cir_vars)
    #     cir_vars_2 = self.get_cir_out(self.c2_name, fun_cir_vars)
    #     sub_vars_1 = self.get_sub_out(self.c1_name)
    #     sub_vars_2 = self.get_sub_out(self.c2_name)
    #     return format_lines(
    #         [
    #             "# circuits distance",
    #             *self.cir_dist_func.definition_function("cir", cir_vars_1, cir_vars_2),
    #             "",
    #             "# subcircuits distance",
    #             *self.sub_dist_func.definition_function("sub", sub_vars_1, sub_vars_2)
    #         ],
    #         indent_amount=1
    #     )

    # def z3_generate_forall_solver_circuits(self):
    #     return format_lines(
    #         [
    #             "# circuits",
    #             f"{self.c1_name},",
    #             f"{self.c2_name},",
    #         ],
    #         indent_amount=2
    #     )

    # def z3_generate_optimizer(self):
    #     return format_lines(
    #         [
    #             f"# optimizer",
    #             f"optimizer = z3.Optimize()",
    #             f"",
    #             f"# add circuits to optimizer",
    #             f"optimizer.add({self.c1_name}, {self.c2_name})",
    #             f"",
    #             f"# add distances",
    #             f"optimizer.add(",
    #             self.z3_generate_distance_definition(),
    #             f")",
    #             f"",
    #             f"# add constraints",
    #             f"optimizer.add(cir_out_dist > ET)",
    #             f"",
    #             f"# setup objective",
    #             f"objective = optimizer.minimize(sub_out_dist)",
    #             f"",
    #             f"# optimize",
    #             f"optimizer.check()",
    #             f"optimizer.lower(objective)",
    #             f"",
    #             f"# extract wanted distance",
    #             f"model = optimizer.model()",
    #         ],
    #         extra_newlines=1)

    # def z3_generate_script_output(self):
    #     return format_lines([
    #         f"# print results",
    #         f"print('e = cir_out_dist =', model[cir_out_dist])",
    #         f"print('d = sub_out_dist =', model[sub_out_dist])",
    #     ])

    # def generate_z3py_script_v2_phase1(self):
    #     # check
    #     assert None is not self.current_graph.subgraph, \
    #         "Subgraph is not defined, did you miss calling `import_graph` and `extract_subgraph`?"
    #     assert None not in [self.sub_dist_func, self.cir_dist_func], \
    #         "Distance functions are not defined, did you miss calling `setup_distance_functions`?"

    #     imports = self.z3_generate_imports()  # parent
    #     config = self.z3_generate_config()
    #     z3_abs_function = self.z3_generate_z3_abs_function()  # parent
    #     input_variables_declaration = self.z3_generate_declare_input_variables()

    #     subinputs_1 = self.generate_z3py_suboutput_variables(self.c1_name)
    #     subinputs_2 = self.generate_z3py_suboutput_variables(self.c2_name)

    #     integer_function_declaration_1 = self.z3_generate_declare_integer_function(f"{self.c1_name}_{F_EXACT}")
    #     integer_function_declaration_2 = self.z3_generate_declare_integer_function(f"{self.c2_name}_{F_EXACT}")

    #     utility_variables = self.z3_generate_utility_variables()
    #     # implicit_parameters_declaration = self.z3_generate_declare_implicit_parameters_subxpat()
    #     # TODO: MARCO
    #     circuit_1 = "".join([
    #         self.z3_generate_exact_circuit_wires_declaration(self.c1_name),  # exact_circuit_wires_declaration
    #         self.z3_generate_exact_circuit_outputs_declaration(self.c1_name),  # exact_circuit_outputs_declaration
    #         self.z3_generate_exact_circuit_constraints(self.c1_name),  # exact_circuit_constraints
    #     ])
    #     circuit_2 = "".join([
    #         self.z3_generate_exact_circuit_wires_declaration(self.c2_name),  # exact_circuit_wires_declaration
    #         self.z3_generate_exact_circuit_outputs_declaration(self.c2_name),  # exact_circuit_outputs_declaration
    #         self.z3_generate_exact_circuit_constraints(self.c2_name),  # exact_circuit_constraints
    #     ])
    #     distance_declaration = self.z3_generate_distance_declaration()

    #     optimizer = self.z3_generate_optimizer()
    #     output = self.z3_generate_script_output()

    #     z3pyscript = "".join([
    #         imports,
    #         config,
    #         z3_abs_function,
    #         input_variables_declaration,
    #         subinputs_1,
    #         subinputs_2,
    #         integer_function_declaration_1,
    #         integer_function_declaration_2,
    #         utility_variables,
    #         circuit_1,
    #         circuit_2,
    #         distance_declaration,
    #         optimizer,
    #         output,
    #         # verification_solver,
    #         # parameter_constraint_list,
    #         # find_wanted_number_of_models,
    #         # store_data
    #     ])

    #     with open("TMP.py", "w") as f:
    #         f.write(z3pyscript)
