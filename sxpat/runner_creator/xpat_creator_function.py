# typing
from __future__ import annotations
from typing import TextIO, Tuple, List

# libs
from itertools import chain

# Z3Log libs
from Z3Log.config.config import *
from Z3Log.config import path as z3logpath

# sxpat libs
from sxpat.config.config import *
from sxpat.config import paths as sxpatpaths
from sxpat.distance_function import DistanceFunction
from z_marco.ma_graph import MaGraph

# package
from .runner_creator import RunnerCreator
from sxpat.utils.utils import declare_z3_function, call_z3_function, format_lines, indent_lines


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

    name = property(lambda _: "XPATF")
    """Deprecated"""

    @staticmethod
    def get_script_name(graph_name: str,
                        literals_per_product: int,
                        products_per_output: int,
                        distance_function_name: str
                        ) -> str:
        # compute base name
        name = '_'.join([
            graph_name,
            f"{NameParameters.LPP.value}{literals_per_product}",
            f"{NameParameters.PPO.value}{products_per_output}",
            f"{NameParameters.DST.value}{distance_function_name}",
            "XPATF"
        ])

        # get folder and extension
        folder, extension = z3logpath.OUTPUT_PATH['z3']

        return f"{folder}/{name}.{extension}"

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
            *self.gen_exact_circuit(),
            "",
            # template
            *self.gen_template_circuit(),
            "",
            # solver
            *self.gen_error(),
            "",
            *self.gen_solver(),  # Inside this, there are Second and Third Kinds
            "",
            # self.gen_smt_dump("function.smt2"),
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
            *map(self.declare_z3_gate, self.exact_graph.inputs)
        ]

    # EXACT CIRCUIT

    def gen_exact_circuit(self) -> List[str]:
        return [
            *self.gen_exact_circuit_declarations(),
            "",
            f"{self.exact_circuit_name} = z3.And(",
            *indent_lines(self.gen_exact_circuit_assignments()),
            ")",
            "",
        ]

    def gen_exact_circuit_declarations(self):
        return [
            "# exact gates declaration",
            *(
                declare_z3_function(
                    f"{self.exact_circuit_name}_{gate_name}",
                    len(self.exact_graph.inputs), "z3.BoolSort()", "z3.BoolSort()"
                )
                for gate_name in self.exact_graph.gates
            ),
            "# exact outputs declaration",
            *(
                declare_z3_function(
                    f"{self.exact_circuit_name}_{out_name}",
                    len(self.exact_graph.inputs), "z3.BoolSort()", "z3.BoolSort()"
                )
                for out_name in self.exact_graph.outputs
            )
        ]

    def gen_exact_circuit_assignments(self):
        # => gates
        gates = []
        for gate_name in self.exact_graph.gates:
            gate_preds = [
                (
                    name
                    if name in self.exact_graph.inputs
                    else call_z3_function(f"{self.exact_circuit_name}_{name}", self.exact_graph.inputs)
                )
                for name in self.exact_graph.predecessors(gate_name)
            ]
            gate_func = self.exact_graph.function_of(gate_name)

            assert len(gate_preds) in [1, 2]
            assert gate_func in [NOT, AND, OR]

            left_side = call_z3_function(
                f"{self.exact_circuit_name}_{gate_name}", self.exact_graph.inputs)
            gates.append(
                f"{left_side} == z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)}),")

        # => outputs
        outputs = []
        for out_name in self.exact_graph.outputs:
            out_preds = [
                (
                    name
                    if name in self.exact_graph.inputs
                    else call_z3_function(f"{self.exact_circuit_name}_{name}", self.exact_graph.inputs)
                )
                for name in self.exact_graph.predecessors(out_name)
            ]

            assert len(out_preds) == 1

            left_side = call_z3_function(
                f"{self.exact_circuit_name}_{out_name}", self.exact_graph.inputs)
            outputs.append(f"{left_side} == {out_preds[0]},")

        return [
            "# exact gates assignment",
            *gates,
            "# exact outputs assignment",
            *outputs,
        ]

    # TEMPLATE CIRCUIT

    def gen_template_circuit(self) -> List[str]:
        return [
            *self.gen_template_circuit_declarations(),
            "",
            f"{self.template_circuit_name} = z3.And(",
            *indent_lines(self.gen_template_circuit_assignments()),
            ")",
            "",
        ]

    def gen_template_circuit_declarations(self) -> List[str]:
        return [
            "# multiplexers parameters declaration",
            *chain.from_iterable((
                map(
                    self.declare_z3_gate,
                    self.gen_parameter_pair(out_name, tree_i, in_name)
                )
                for out_name in self.exact_graph.outputs
                for tree_i in range(self.ppo)
                for in_name in self.exact_graph.inputs
            )),
            "# outputs parameters declaration",
            *(
                self.declare_z3_gate(f"p_{out_name}")
                for out_name in self.exact_graph.outputs
            ),
            # "# template trees declaration",
            # *(
            #     declare_z3_function(
            #         f"{self.template_circuit_name}_{out_name}_t{tree_i}",
            #         len(self.exact_graph.inputs), "z3.BoolSort()", "z3.BoolSort()"
            #     )
            #     for out_name in self.exact_graph.outputs
            #     for tree_i in range(self.ppo)
            # ),
            "# template outputs declaration",
            *(
                declare_z3_function(
                    f"{self.template_circuit_name}_{out_name}",
                    len(self.exact_graph.inputs), "z3.BoolSort()", "z3.BoolSort()"
                )
                for out_name in self.exact_graph.outputs
            ),
        ]

    def gen_template_circuit_assignments(self) -> List[str]:
        def gen_leaf(out_name: str, tree_i: int, in_name: str) -> str:
            select_param, literal_param = self.gen_parameter_pair(
                out_name, tree_i, in_name)
            return f"z3.Or(z3.Not({select_param}), {literal_param} == {in_name})"

        outputs = []
        for out_name in self.exact_graph.outputs:
            trees = []
            for tree_i in range(self.ppo):
                leaves = [
                    gen_leaf(out_name, tree_i, in_name) + ","
                    for in_name in self.exact_graph.inputs
                ]
                trees.extend([
                    f"z3.And( # tree #{tree_i}",
                    *indent_lines(leaves),
                    "),"
                ])

            left_side = call_z3_function(
                f"{self.template_circuit_name}_{out_name}", self.exact_graph.inputs)
            outputs.extend([
                f"{left_side} == z3.And(p_{out_name}, z3.Or(",
                *indent_lines(trees),
                ")),",
            ])

        return [
            "# template circuit assignment",
            *outputs
        ]

    def gen_parameter_pair(self,  out_name: str, tree_i: int, in_name: str) -> Tuple[str, str]:
        """returns (select_parameter, literal_parameter)"""
        prefix = f"p_{out_name}_t{tree_i}_{in_name}"
        return (f"{prefix}_{SELECT_PREFIX}", f"{prefix}_{LITERAL_PREFIX}")

    def gen_select_parameter(self, out_name: str, tree_i: int, in_name: str) -> str:
        return f"p_{out_name}_t{tree_i}_{in_name}_{SELECT_PREFIX}"

    def gen_literal_parameter(self, out_name: str, tree_i: int, in_name: str) -> str:
        return f"p_{out_name}_t{tree_i}_{in_name}_{LITERAL_PREFIX}"

    # ERROR

    def gen_error(self):
        vars_1 = [
            f"{self.exact_circuit_name}_{v}"
            for v in self.exact_graph.outputs
        ]
        vars_2 = [
            f"{self.template_circuit_name}_{v}"
            for v in self.exact_graph.outputs
        ]

        return [
            f"# error declaration",
            *self.error_function.declare(),
            # *self.gen_error_declarations(),
            f"# error computation",
            "error_vars = z3.And(",
            *indent_lines(self.error_function.assign(vars_1, vars_2)),
            # *indent_lines(self.gen_error_assignmets()),
            ")",
        ]

    def gen_error_declarations(self) -> List[str]:
        return [
            declare_z3_function(
                "val1", len(self.exact_graph.inputs),
                "z3.BoolSort()", "z3.IntSort()"
            ),
            declare_z3_function(
                "val2", len(self.exact_graph.inputs),
                "z3.BoolSort()", "z3.IntSort()"
            ),
            # declare_z3_function(
            #     "out_dist", len(self.exact_graph.inputs),
            #     "z3.BoolSort()", "z3.IntSort()"
            # ),
            (
                f"out_dist = z3.Abs("
                + call_z3_function('val1', self.exact_graph.inputs)
                + " - "
                + call_z3_function('val2', self.exact_graph.inputs)
                + ")"
            )
        ]

    def gen_error_assignmets(self) -> List[str]:
        # TODO: can be regeneralized, this is just for testing "function" vs "direct"
        val1_call = call_z3_function("val1", self.exact_graph.inputs)
        # TODO: HERE: GENERALIZZARE FUNZIONE, IN MODO CHE FUNZIONI A `FUNZIONI`
        val1 = (
            f"{val1_call} == "
            + " + ".join([
                call_z3_function(
                    f"{self.exact_circuit_name}_{v}",
                    self.exact_graph.inputs
                ) + f"*{w}"
                for v, w in zip(self.exact_graph.outputs, self.error_function._weights)
            ])
            + ","
        )
        val2_call = call_z3_function("val2", self.exact_graph.inputs)
        val2 = (
            f"{val2_call} == "
            + " + ".join([
                call_z3_function(
                    f"{self.template_circuit_name}_{v}",
                    self.exact_graph.inputs
                ) + f"*{w}"
                for v, w in zip(self.exact_graph.outputs, self.error_function._weights)
            ])
            + ","
        )
        # out_dist = (
        #     call_z3_function("out_dist", self.exact_graph.inputs)
        #     + f" == z3.Abs({val1_call} - {val2_call}),"
        # )
        return [
            val1,
            val2,
            # out_dist
        ]

    # OTHER

    def gen_constraints_error(self):
        return [
            "# error constraints",
            "error_vars,",
            # f"{call_z3_function('out_dist', self.exact_graph.inputs)} <= ET,",
            f"out_dist <= ET,",
        ]

    def get_constraints_atmost(self):
        constraints = []
        for out_name in self.exact_graph.outputs:
            for tree_i in range(self.ppo):
                parameters = []
                for in_name in self.exact_graph.inputs:
                    param_name = self.gen_select_parameter(
                        out_name, tree_i, in_name)
                    parameters.append(f"z3.If({param_name}, 1, 0)")
                constraints.append(
                    f"({' + '.join(parameters)}) <= {self.lpp},")

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
                    p_s, p_l = self.gen_parameter_pair(
                        out_name, tree_i, in_name)
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
                    parameters.extend(self.gen_parameter_pair(
                        out_name, tree_i, in_name))
            constraints.append(
                f"z3.Implies(z3.Not(p_{out_name}), z3.Not(z3.Or({', '.join(parameters)}))),")

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
            trees_comparisons = [
                f"({tree_1} >= {tree_2})," for tree_1, tree_2 in zip(trees, trees[1:])]
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
            *indent_lines([
                "# add circuits",
                self.exact_circuit_name + ",",
                self.template_circuit_name + ",",
            ], 2),
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
            *indent_lines([
                "# add circuits",
                self.exact_circuit_name + ",",
                self.template_circuit_name + ",",
            ]),
            f"{TAB}# error variable",
            # f"{TAB}error == {call_z3_function('out_dist', self.exact_graph.inputs)},",
            f"{TAB}error_vars,",
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
            f"_{self.name}"
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

                forall_solver.set("timeout", int(timeout * 1000))  # add timeout in milliseconds
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
