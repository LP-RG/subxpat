# typing
from __future__ import annotations
from typing import TextIO, Tuple, List

# libs
from itertools import chain

# Z3Log libs
from Z3Log.config.config import *

# sxpat libs
from sxpat.config.config import *
from sxpat.config import paths as sxpatpaths
from sxpat.distance_function import DistanceFunction
from z_marco.ma_graph import MaGraph

# package
from .runner_creator import RunnerCreator
from .utils import format_lines, indent_lines


class XPatRunnerCreator(RunnerCreator):
    def __init__(self,
                 exact_graph: MaGraph, exact_name: str,
                 literal_per_product: int, product_per_output: int,
                 error_function: DistanceFunction,
                 exact_circuit_name: str = "c1", template_circuit_name: str = "c2") -> None:
        self.exact_graph: MaGraph = exact_graph

        self.exact_name: str = exact_name

        self.literal_per_product: int = literal_per_product
        self.product_per_output: int = product_per_output

        self.exact_circuit_name: str = exact_circuit_name
        self.template_circuit_name: str = template_circuit_name

        self.error_function: DistanceFunction = error_function

    lpp = property(lambda s: s.literal_per_product)
    ppo = property(lambda s: s.product_per_output)

    def generate_script(self, output: TextIO = None) -> str:
        text = format_lines([
            # generics
            *self.gen_imports(),
            "",
            *self.gen_arguments_parsing(),
            "",
            # inputs
            *self.gen_declare_input_variables(),
            "",
            # exact circuit
            # *self.gen_exact_circuit_wires(),
            *self.gen_exact_circuit_wires_declaration(),
            "",
            *self.gen_exact_circuit_outputs(),
            "",
            # template
            *self.gen_declare_template_parameters(),
            "",
            *self.gen_template_circuit_trees(),
            "",
            *self.gen_template_circuit_outputs(),
            "",
            # solver
            *self.gen_error_computation(),
            "",
            *self.gen_solver(),
            "",
            # verifier
            *self.gen_verifier(),
            "",
            # executer
            *self.gen_executer(),
            ""
        ])

        if output is not None:
            output.write(text)

        return text

    def gen_arguments_parsing(self) -> List[str]:
        return [
            f"ET: int = int(sys.argv[1])",
            f"wanted_models: int = 1 if len(sys.argv) < 3 else int(sys.argv[2])",
            f"timeout: float = float(sys.maxsize if len(sys.argv) < 4 else sys.argv[3])",
            # TODO: NOTE: this was the constant `2 ** 3 - 1`
            f"max_possible_ET: int = 2 ** {len(self.exact_graph.outputs)} - 1",
        ]

    def gen_declare_input_variables(self) -> List[str]:
        return [
            "# inputs variables declaration",
            *map(self.declare_gate, self.exact_graph.inputs)
        ]

    def gen_declare_template_parameters(self) -> List[str]:
        return [
            "# parameters variables declaration",
            *self.gen_declare_output_parameters(),
            *self.gen_declare_products_parameters(),
        ]

    def gen_declare_output_parameters(self) -> List[str]:
        return [
            self.declare_gate(f"p_{out_name}")
            for out_name in self.exact_graph.outputs
        ]

    def gen_declare_products_parameters(self) -> List[str]:
        # # NOTE: alternative, using comprehension
        return list(chain.from_iterable((
            map(
                self.declare_gate,
                self.gen_parameter_pair(out_name, tree_i, in_name)
            )
            for out_name in self.exact_graph.outputs
            for tree_i in range(self.ppo)
            for in_name in self.exact_graph.inputs
        )))

    def gen_exact_circuit_wires_declaration(self):
        # NOTE: MANGO
        return [
            "# exact gates declaration",
            *(
                self.declare_gate(f"{self.exact_circuit_name}_{gate_name}")
                for gate_name in self.exact_graph.gates
            )
        ]

    def gen_exact_circuit_wires_assignment(self):
        # NOTE: MANGO

        lines = []
        for gate_name in self.exact_graph.gates:
            gate_preds = [
                name if name in self.exact_graph.inputs else f"{self.exact_circuit_name}_{name}"
                for name in self.exact_graph.predecessors(gate_name)
            ]
            gate_func = self.exact_graph.function_of(gate_name)

            assert len(gate_preds) in [1, 2]
            assert gate_func in [NOT, AND, OR]

            lines.append(f"{self.exact_circuit_name}_{gate_name} == z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)}),")

        return [
            f"# exact gates assignment",
            *lines,
        ]

    # def z3_generate_exact_circuit_wire_constraints(self):
    #     exact_wire_constraints = ''
    #     exact_wire_constraints += f'# exact circuit constraints\n'
    #     exact_wire_constraints += f'{EXACT_CIRCUIT} = And(\n'
    #     exact_wire_constraints += f'{TAB}# wires\n'
    #     for g_idx in range(self.exact_graph.num_gates):
    #         g_label = self.exact_graph.gate_dict[g_idx]
    #         g_predecessors = self.get_predecessors(g_label)
    #         g_function = self.get_logical_function(g_label)

    #         assert len(g_predecessors) == 1 or len(g_predecessors) == 2
    #         assert g_function == NOT or g_function == AND or g_function == OR
    #         if len(g_predecessors) == 1:
    #             if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
    #                 pred_1 = g_predecessors[0]
    #             else:
    #                 pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])

    #             exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
    #                                       f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

    #             exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}), \n"
    #         else:
    #             exact_wire_constraints += f"{TAB}{EXACT_WIRES_PREFIX}{self.exact_graph.num_inputs + g_idx}(" \
    #                                       f"{','.join(list(self.exact_graph.input_dict.values()))}) == "

    #             if g_predecessors[0] in list(self.exact_graph.input_dict.values()):
    #                 pred_1 = g_predecessors[0]
    #             else:
    #                 pred_1 = self.z3_express_node_as_wire_constraints(g_predecessors[0])
    #             if g_predecessors[1] in list(self.exact_graph.input_dict.values()):
    #                 pred_2 = g_predecessors[1]
    #             else:
    #                 pred_2 = self.z3_express_node_as_wire_constraints(g_predecessors[1])

    #             exact_wire_constraints += f"{TO_Z3_GATE_DICT[g_function]}({pred_1}, {pred_2}),\n"
    #     return exact_wire_constraints

    def gen_exact_circuit_wires(self) -> List[str]:
        lines = ["# exact circuit gates"]
        for gate_name in self.exact_graph.gates:
            gate_preds = [
                name if name in self.exact_graph.inputs else f"{self.exact_circuit_name}_{name}"
                for name in self.exact_graph.predecessors(gate_name)
            ]
            gate_func = self.exact_graph.function_of(gate_name)

            assert len(gate_preds) in [1, 2]
            assert gate_func in [NOT, AND, OR]

            lines.append(f"{self.exact_circuit_name}_{gate_name} = z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)})")

        return lines

    def gen_exact_circuit_outputs(self):
        lines = ["# exact circuit outputs (from the least significant)"]

        for out_name in self.exact_graph.outputs:
            out_preds = [
                name if name in self.exact_graph.inputs else f"{self.exact_circuit_name}_{name}"
                for name in self.exact_graph.predecessors(out_name)
            ]

            assert len(out_preds) == 1

            lines.append(f"{self.exact_circuit_name}_{out_name} = {out_preds[0]}")

        return lines

    def gen_select_parameter(self, out_name: str, tree_i: int, in_name: str) -> str:
        return f"p_{out_name}_t{tree_i}_{in_name}_{SELECT_PREFIX}"

    def gen_literal_parameter(self, out_name: str, tree_i: int, in_name: str) -> str:
        return f"p_{out_name}_t{tree_i}_{in_name}_{LITERAL_PREFIX}"

    def gen_parameter_pair(self,  out_name: str, tree_i: int, in_name: str) -> Tuple[str, str]:
        """returns (select_parameter, literal_parameter)"""
        prefix = f"p_{out_name}_t{tree_i}_{in_name}"
        return (f"{prefix}_{SELECT_PREFIX}", f"{prefix}_{LITERAL_PREFIX}")

    def gen_template_circuit_leaf(self, out_name: str, tree_i: int, in_name: str) -> str:
        select_param, literal_param = self.gen_parameter_pair(out_name, tree_i, in_name)
        return f"z3.Or(z3.Not({select_param}), {literal_param} == {in_name})"

    def gen_template_circuit_trees(self) -> List[str]:
        lines = ["# template circuit trees"]
        for out_name in self.exact_graph.outputs:
            for tree_i in range(self.ppo):
                leaves = [
                    self.gen_template_circuit_leaf(out_name, tree_i, in_name)
                    for in_name in self.exact_graph.inputs
                ]
                lines.append(f"{self.template_circuit_name}_{out_name}_t{tree_i} = z3.And({', '.join(leaves)})")
        return lines

    def gen_template_circuit_outputs(self):
        lines = ["# template circuit outputs (from the least significant)"]

        for out_name in self.exact_graph.outputs:
            trees = []
            for tree_i in range(self.ppo):
                trees.append(f"{self.template_circuit_name}_{out_name}_t{tree_i}")
            lines.append(
                f"{self.template_circuit_name}_{out_name} = "
                f"z3.And(p_{out_name}, {', '.join(trees)})"
            )

        return lines

    def gen_error_computation(self):
        exact_outputs = [
            f"{self.exact_circuit_name}_{out_name}"
            for out_name in self.exact_graph.outputs
        ]
        template_outputs = [
            f"{self.template_circuit_name}_{out_name}"
            for out_name in self.exact_graph.outputs
        ]
        return [
            f"# error computation",
            *self.error_function.declare(exact_outputs, template_outputs)
        ]

    def gen_constraints_error(self):
        return [
            "# error constraints",
            "out_dist <= ET,",
        ]

    def get_constraints_atmost(self):
        constraints = []
        for out_name in self.exact_graph.outputs:
            for tree_i in range(self.ppo):
                parameters = []
                for in_name in self.exact_graph.inputs:
                    param_name = self.gen_select_parameter(out_name, tree_i, in_name)
                    parameters.append(f"z3.If({param_name}, 1, 0)")
                constraints.append(f"({' + '.join(parameters)}) <= {self.lpp},")

        return [
            f"# literals_per_product constraints",
            *constraints,
        ]

    def gen_constraints_double_no_care(self):
        constraints = []
        for out_name in self.exact_graph.outputs:
            implies = []
            for tree_i in range(self.ppo):
                for in_name in self.exact_graph.inputs:
                    p_s, p_l = self.gen_parameter_pair(out_name, tree_i, in_name)
                    implies.append(f"z3.Implies({p_l}, {p_s})")
            constraints.append(f"{', '.join(implies)},")

        return [
            "# remove double no-care",
            *constraints,
        ]

    def gen_constraints_constant_zero_permutations(self):
        constraints = []
        for out_name in self.exact_graph.outputs:
            parameters = []
            for tree_i in range(self.ppo):
                for in_name in self.exact_graph.inputs:
                    parameters.extend(self.gen_parameter_pair(out_name, tree_i, in_name))
            constraints.append(f"z3.Implies(z3.Not(p_{out_name}), z3.Not(z3.Or({', '.join(parameters)}))),")

        return [
            "# remove constant 0 permutations (ignored trees permutations)",
            *constraints,
        ]

    def gen_constraints_tree_order(self):
        if self.ppo == 1:
            return [
                "# set order of trees",
                "# No order needed for only one tree (product)",
            ]

        def gen_leaf(out_name: str, tree_i: int, in_name: str, in_i: int) -> str:
            p_s, p_l = self.gen_parameter_pair(out_name, tree_i, in_name)
            return f"z3.IntVal({2 ** (2 * in_i)}) * {p_s} + z3.IntVal({2 ** (2 * in_i + 1)}) * {p_l}"

        def gen_tree(out_name: str, tree_i: int) -> str:
            return " + ".join(
                gen_leaf(out_name, tree_i, in_name, in_i)
                for in_i, in_name in enumerate(self.exact_graph.inputs)
            )

        constraints = []
        for out_name in self.exact_graph.outputs:
            trees = [gen_tree(out_name, tree_i) for tree_i in range(self.ppo)]
            trees_comparisons = [f"({tree_1} >= {tree_2})," for tree_1, tree_2 in zip(trees, trees[1:])]
            constraints.extend(trees_comparisons)

        return [
            "# set order of trees",
            *constraints,
        ]

    def gen_constraints_redundancy(self):
        return [
            "# redundancy constraints",
            *self.gen_constraints_double_no_care(),
            *self.gen_constraints_constant_zero_permutations(),
            *self.gen_constraints_tree_order(),
        ]

    def gen_solver(self):
        return [
            f"forall_solver = z3.Solver()",
            f"forall_solver.add(z3.ForAll(",
            f"{TAB}[{', '.join(self.exact_graph.inputs)}],",
            f"{TAB}z3.And(",
            *indent_lines(self.gen_exact_circuit_wires_assignment(), 2),
            "",
            *indent_lines(self.gen_constraints_error(), 2),
            "",
            *indent_lines(self.get_constraints_atmost(), 2),
            "",
            *indent_lines(self.gen_constraints_redundancy(), 2),
            f"{TAB})",
            f"))"
        ]

    def gen_verifier(self):
        return [
            f"# verification solver",
            f"error = z3.Int('error')",
            f"verification_solver = z3.Solver()",
            f"verification_solver.add(",
            f"{TAB}# error variable",
            f"{TAB}error == out_dist,",
            ")",
        ]

    def gen_json_outfile_name(self):
        folder, extension = sxpatpaths.OUTPUT_PATH[JSON]
        return (
            f"{folder}/{self.exact_name}"
            f"_{LPP}{self.literal_per_product}"
            f"_{PPO}{self.product_per_output}"
            f"_{DST}{self.error_function.abbreviation}"
            f"_{TEMPLATE_SPEC_ET}{{ET}}"
            f"_XPat"
            f".{extension}"
        )

    def gen_executer(self):
        return f"""
        # parameters
        parameters_constraints: List[Tuple[z3.BoolRef, bool]] = []

        # find the wanted number of models
        found_data = []
        while (len(found_data) < wanted_models
            and timeout > 0):
            time_total_start = time()

            attempts = 1
            result: z3.CheckSatResult = None
            attempts_times: List[Tuple[float, float, float]] = []

            # find a valid model
            while result != z3.sat:
                time_attempt_start = time()
                time_parameters_start = time_attempt_start

                # ==== find parameters

                # add constrain to prevent the same parameters to happen
                if parameters_constraints:
                    forall_solver.add(z3.Or(*map(lambda x: x[0] != x[1], parameters_constraints)))

                parameters_constraints = []

                forall_solver.set("timeout", int(timeout * 1000))  # add timeout in millideconds
                result = forall_solver.check()

                time_parameters = time() - time_attempt_start
                time_attempt = time() - time_attempt_start
                timeout -= time_parameters  # remove the time used from the timeout

                if result != z3.sat:
                    attempts_times.append((time_attempt, time_parameters, None))
                    break

                m = forall_solver.model()
                parameters_constraints = []
                for k, v in map(lambda k: (k, m[k]), m):
                    if str(k)[0] == "p":
                        parameters_constraints.append((z3.Bool(str(k)), v))

                # ==== verify parameters

                WCE: int = None
                verification_ET: int = 0
                time_verification_start = time()

                # save state
                verification_solver.push()

                # parameters constraints
                verification_solver.add(
                    *map(lambda x: x[0] == x[1], parameters_constraints),
                )

                while verification_ET < max_possible_ET:
                    # add constraint
                    verification_solver.add(out_dist > verification_ET)

                    # run solver
                    verification_solver.set("timeout", int(timeout * 1000))  # add timeout in millideconds
                    v_result = verification_solver.check()

                    if v_result == z3.unsat:
                        # unsat, WCE found
                        WCE = verification_ET
                        break

                    elif v_result == z3.sat:
                        # sat, need to search again
                        m = verification_solver.model()
                        verification_ET = m[error].as_long()

                    else:
                        # unknown (probably a timeout)
                        WCE = -1
                        break

                if WCE is None:
                    WCE = max_possible_ET

                # revert state
                verification_solver.pop()

                time_verification = time() - time_verification_start
                time_attempt = time() - time_attempt_start
                timeout -= time_verification  # remove the time used from the timeout

                attempts_times.append((time_attempt, time_parameters, time_verification))

                # ==== continue or exit

                if WCE > ET:
                    # Z3 hates us and decided it doesn't like being appreciated
                    result = None
                    attempts += 1
                    invalid_parameters = parameters_constraints

                elif WCE < 0:  # caused by unknown
                    break

            # ==== store data
            def extract_info(pattern: Union[re.Pattern, str], string: str,
                            parser: Callable[[Any], Any] = lambda x: x,
                            default: Union[Callable[[], None], Any] = None) -> Any:
                return (parser(match[1]) if (match := re.search(pattern, string))
                        else (default() if callable(default) else default))

            def key_function(parameter_constraint):

                p = str(parameter_constraint[0])
                o_id = extract_info(r'_o(\d+)', p, int, -1)
                t_id = extract_info(r'_t(\d+)', p, int, 0)
                i_id = extract_info(r'_i(\d+)', p, int, 0)
                typ = extract_info(r'_(l|s)', p, {{'s': 1, 'l': 2}}.get, 0)

                if o_id < 0:
                    return 0

                return (o_id * 100000
                        + t_id * 1000
                        + i_id * 10
                        + typ)

            time_total = time() - time_total_start
            data_object = {{
                'result': str(result),
                'total_time': time_total,
                'attempts': attempts,
                'attempts_times': [list(map(lambda tup: [*tup], attempts_times))]
            }}

            if result == z3.sat:
                data_object['model'] = dict(map(lambda item: (str(item[0]), z3.is_true(item[1])),
                                                sorted(parameters_constraints,
                                                    key=key_function)))

            found_data.append(data_object)

            if result != z3.sat:
                break

        # ==== output data
        print(json.dumps(found_data, separators=(',', ':'),))
        with open(f'{self.gen_json_outfile_name()}', 'w') as ofile:
            ofile.write(json.dumps(found_data, separators=(',', ':'), indent=4))
        """.replace("\n        ", "\n").replace("    ", TAB).split("\n")
