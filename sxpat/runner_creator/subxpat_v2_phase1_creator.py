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
from sxpat.utils.utils import call_z3_function, declare_z3_function, format_lines, indent_lines
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
        self.subcircuit_distance_function = subcircuit_distance_function.with_no_input()

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
            *self.gen_circuits(),
            # *self.gen_exact_circuit_wires(self.c1_name),
            # "",
            # *self.gen_exact_circuit_outputs(self.c1_name),
            # "",
            # *self.gen_exact_circuit_wires(self.c2_name),
            # "",
            # *self.gen_exact_circuit_outputs(self.c2_name),
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

    # START: << CIRCUIT >>

    def gen_circuits(self) -> List[str]:
        return [
            *self.gen_circuits_declarations(),
            "",
            f"circuits = z3.And(",
            *indent_lines(self.gen_circuits_assignments()),
            ")",
        ]

    def gen_circuits_declarations(self):
        def _gen_declarations(circuit_name: str):
            return [
                "# exact gates declaration",
                *(
                    declare_z3_function(
                        f"{circuit_name}_{gate_name}",
                        len(self.graph.inputs), "z3.BoolSort()",
                        "z3.BoolSort()"
                    )
                    for gate_name in self.graph.gates
                ),
                "# exact outputs declaration",
                *(
                    declare_z3_function(
                        f"{circuit_name}_{out_name}",
                        len(self.graph.inputs), "z3.BoolSort()",
                        "z3.BoolSort()"
                    )
                    for out_name in self.graph.outputs
                )
            ]

        return [
            *_gen_declarations(self.c1_name),
            "",
            *_gen_declarations(self.c2_name),
        ]

    def gen_circuits_assignments(self):
        def _gen_assignments(circuit_name: str):
            subout_preds = {self.subgraph.predecessors(n)[0]: n for n in self.subgraph.outputs}

            # => gates
            gates = []
            for gate_name in self.graph.gates:
                left_side = call_z3_function(f"{circuit_name}_{gate_name}", self.graph.inputs)

                if gate_name in subout_preds:
                    gates.append(f"{left_side} == {circuit_name}_{subout_preds[gate_name]},")
                    continue

                gate_preds = [
                    (
                        name
                        if name in self.graph.inputs
                        else call_z3_function(f"{circuit_name}_{name}", self.graph.inputs)
                    )
                    for name in self.graph.predecessors(gate_name)
                ]
                gate_func = self.graph.function_of(gate_name)

                assert len(gate_preds) in [1, 2]
                assert gate_func in [NOT, AND, OR]

                gates.append(f"{left_side} == z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)}),")

            # => outputs
            outputs = []
            for out_name in self.graph.outputs:
                out_preds = [
                    (
                        name
                        if name in self.graph.inputs
                        else call_z3_function(f"{circuit_name}_{name}", self.graph.inputs)
                    )
                    for name in self.graph.predecessors(out_name)
                ]

                assert len(out_preds) == 1

                left_side = call_z3_function(f"{circuit_name}_{out_name}", self.graph.inputs)
                outputs.append(f"{left_side} == {out_preds[0]},")

            return [
                f"# {circuit_name} gates assignment",
                *gates,
                f"# {circuit_name} outputs assignment",
                *outputs,
            ]

        return [
            *_gen_assignments(self.c1_name),
            "",
            *_gen_assignments(self.c2_name),
        ]

    # end: << CIRCUIT >>

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

    def gen_distance_functions(self):
        cir_vars_1 = [f"{self.c1_name}_{name}" for name in self.graph.outputs]
        cir_vars_2 = [f"{self.c2_name}_{name}" for name in self.graph.outputs]
        sub_vars_1 = [f"{self.c1_name}_{name}" for name in self.subgraph.outputs]
        sub_vars_2 = [f"{self.c2_name}_{name}" for name in self.subgraph.outputs]

        return [
            "# Distance variables",
            *self.circuit_distance_function.declare("cir"),
            "",
            *self.subcircuit_distance_function.declare("sub"),
            "",
            "distance_assignments = z3.And(",
            *indent_lines(self.circuit_distance_function.assign(cir_vars_1, cir_vars_2, "cir")),
            "",
            *indent_lines(self.subcircuit_distance_function.assign(sub_vars_1, sub_vars_2, "sub")),
            ")",
        ]

    def gen_optimizer(self):
        return [
            f"# optimizer",
            f"optimizer = z3.Optimize()",
            f"",
            f"# add constraints",
            f"optimizer.add(",
            f"    circuits,",
            f"    distance_assignments,",
            f"    cir_out_dist > ET,",
            f")",
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
        ]
