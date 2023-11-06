# typing
from __future__ import annotations
from typing import List
from abc import abstractmethod

# sxpat libs
from sxpat.config.config import AND, NOT, OR, TO_Z3_GATE_DICT
from z_marco.ma_graph import MaGraph


class RunnerCreator:
    @abstractmethod
    def generate_script(self, path: str = None) -> None:
        pass

    @staticmethod
    def empty_lines(num: int = 1) -> List[str]:
        return [""] * num

    def gen_imports(self) -> List[str]:
        return [
            "from typing import Tuple, List, Callable, Any, Union",
            "import z3",
            "import sys",
            "from time import time",
            "import json",
            "import re",
        ]

    @staticmethod
    def declare_gate(name: str) -> str:
        return f"{name} = z3.Bool('{name}')"

    # @classmethod
    # def _gen_circuit(cls, graph: MaGraph, prefix: str) -> List[str]:
    #     lines = [f"# circuit ({prefix})"]

    #     # gates
    #     lines.append("# gates")
    #     for gate_name in graph.gates:
    #         gate_preds = [
    #             name if name in graph.inputs else f"{prefix}_{name}"
    #             for name in graph.predecessors(gate_name)
    #         ]
    #         gate_func = graph.function_of(gate_name)

    #         assert len(gate_preds) in [1, 2]
    #         assert gate_func in [NOT, AND, OR]
    #         lines.append(f"{prefix}_{gate_name} = z3.{TO_Z3_GATE_DICT[gate_func]}({', '.join(gate_preds)})")

    #     # outputs
    #     lines.append("# outputs (from the least significant)")
    #     for out_name in graph.outputs:
    #         out_preds = [
    #             name if name in graph.inputs else f"{prefix}_{name}"
    #             for name in graph.predecessors(out_name)
    #         ]

    #         assert len(out_preds) == 1
    #         lines.append(f"{prefix}_{out_name} = {out_preds[0]}")

    #     return lines
