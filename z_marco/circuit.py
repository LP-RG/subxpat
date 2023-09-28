from __future__ import annotations

from typing import Dict, Iterable, Iterator, List, Tuple, Union

import dataclasses as dc
import io
from itertools import chain
import re
import z3
from sxpat.annotatedGraph import AnnotatedGraph


@dc.dataclass(frozen=True)
class Gate:
    name: str
    annotation: str
    def to_z3(self) -> z3.ExprRef: ...


@dc.dataclass(frozen=True)
class UnaryGate(Gate):
    child: Gate


@dc.dataclass(frozen=True)
class NaryGate(Gate):
    children: Tuple[Gate]


@dc.dataclass(frozen=True)
class BoolLiteral(Gate):
    def to_z3(self) -> z3.BoolRef:
        return z3.Bool(self.name)


@dc.dataclass(frozen=True)
class Not(UnaryGate):
    def to_z3(self) -> z3.BoolRef:
        return z3.Not(self.child.to_z3())


@dc.dataclass(frozen=True)
class And(NaryGate):
    def to_z3(self) -> z3.BoolRef:
        return z3.And(*(g.to_z3() for g in self.children))


@dc.dataclass(frozen=True)
class Or(NaryGate):
    def to_z3(self) -> z3.BoolRef:
        return z3.Or(*(g.to_z3() for g in self.children))


@dc.dataclass(frozen=True)
class Circuit:
    _inputs: List[str]   # list of names of input gates
    _outputs: List[str]  # list of names of output gates
    _gates: Dict[str, Gate]

    @property
    def inputs(self) -> Dict[str, Gate]:
        return {g: self._gates[g] for g in self._inputs}

    @property
    def outputs(self) -> Dict[str, Gate]:
        return {g: self._gates[g] for g in self._outputs}

    @property
    def internals(self) -> Dict[str, Gate]:
        in_out = set(chain(self._inputs, self._outputs))
        return dict(filter(lambda g: g[0] not in in_out, self._gates.items()))

    def normalized(self) -> Circuit:
        """Returns a normalized version of the circuit."""
        raise "To be defined."


def load_annotated(graph: AnnotatedGraph) -> Circuit:
    print("LOADING MARCO AAAAAA")
    print(type(graph.graph.nodes), graph.graph.nodes)


def load_verilog(*, file_path: str = None, code: str = None) -> Circuit:
    assert (file_path is None) != (code is None), "Exactly one of `file_path` or `code` must be given."

    if code is None:
        with open(file_path, "r") as f:
            code = f.read()

    INPUTS_PATTERN = r"input\s+(?:(\[\d+:\d+\])\s+)?((?:[\d\w]+(?:\s*,\s*)?)+);"
    OUTPUTS_PATTERN = r"output\s+(?:(\[\d+:\d+\])\s+)?((?:[\d\w]+(?:\s*,\s*)?)+);"
    ASSIGN_PATTERN = r"assign\s+([\d\w]+(?:\[\d+\])?)\s*=\s*((?:~?[\d\w]+(?:\[\d+\])?(?:\s*[&\|]\s*)?)+);"

    inputs: List[str] = list()   # list of names of input gates
    outputs: List[str] = list()  # list of names of output gates
    all_gates: Dict[str, Gate] = dict()

    for size, names in re.findall(INPUTS_PATTERN, code):
        # sanitize names
        names = list(map(str.strip, names.split(",")))
        if len(size) > 0:
            # generate vector kind names
            size = tuple(map(int, size.strip(" []").split(":")))
            names = list(chain(*(
                [f"{n}_{i}" for i in range(size[0], size[1]-1, -1)]
                for n in names
            )))
        # add variables
        inputs.extend(names)
        all_gates.update({n: BoolLiteral(n, None) for n in names})

    for size, names in re.findall(OUTPUTS_PATTERN, code):
        # sanitize names
        names = list(map(str.strip, names.split(",")))
        if len(size) > 0:
            # generate vector kind names
            size = tuple(map(int, size.strip(" []").split(":")))
            names = list(chain(*(
                [f"{n}_{i}" for i in range(size[0], size[1]-1, -1)]
                for n in names
            )))
        # add variables
        outputs.extend(names)

    for target, expression in re.findall(ASSIGN_PATTERN, code):
        all_gates[devectorize_name(target)] = parse_or(expression)

    return Circuit(inputs, outputs, all_gates)


def parse_or(expr: str) -> Union[Or, Gate]:
    terms = [parse_and(group) for group in expr.split("|")]
    if len(terms) == 1:
        return terms[0]
    return z3.Or(*terms)


def parse_and(expr: str) -> Union[And, Gate]:
    terms = [parse_not(group) for group in expr.split("&")]
    if len(terms) == 1:
        return terms[0]
    return z3.And(*terms)


def parse_not(expr: str) -> Union[Not, Gate]:
    expr = devectorize_name(expr)
    if expr.startswith("~"):
        return z3.Not(z3.Bool(expr.strip("~")))
    return z3.Bool(expr)


def devectorize_name(name: str) -> str:
    return name.strip(" ]").replace("[", "_")


def extract_sub_circuit(circuit: Circuit, sub_circuit_gates: List[str]) -> Circuit:
    pass
