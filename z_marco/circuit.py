import dataclasses as dc
from functools import cached_property
import io
from itertools import chain
import itertools
import re
from typing import Dict, Iterable, Iterator, List, Union
import z3


@dc.dataclass(frozen=True)
class Circuit:
    _inputs: List[str]   # list of names of input gates
    _outputs: List[str]  # list of names of output gates
    _gates: Dict[str, Union[z3.BoolRef, 'Circuit']]

    @property
    def inputs(self) -> Dict[str, z3.BoolRef]:
        return {g: self._gates[g] for g in self._inputs}

    @property
    def outputs(self) -> Dict[str, z3.BoolRef]:
        return {g: self._gates[g] for g in self._outputs}

    @property
    def internals(self) -> Dict[str, z3.BoolRef]:
        return dict(filter(lambda g: g[0] not in chain(self._inputs, self._outputs), self._gates.items()))

    def normalized(self) -> 'Circuit':
        """Returns a normalized version of the circuit."""
        raise "To be defined."


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
    all_gates: Dict[str, z3.BoolRef] = dict()

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
        all_gates.update({n: z3.Bool(n) for n in names})

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


def parse_or(expr: str) -> z3.BoolRef:
    terms = [parse_and(group) for group in expr.split("|")]
    if len(terms) == 1:
        return terms[0]
    return z3.Or(*terms)


def parse_and(expr: str) -> z3.BoolRef:
    terms = [parse_not(group) for group in expr.split("&")]
    if len(terms) == 1:
        return terms[0]
    return z3.And(*terms)


def parse_not(expr: str) -> z3.BoolRef:
    expr = devectorize_name(expr)
    if expr.startswith("~"):
        return z3.Not(z3.Bool(expr.strip("~")))
    return z3.Bool(expr)


def devectorize_name(name: str) -> str:
    return name.strip(" ]").replace("[", "_")


def extract_sub_circuit(circuit: Circuit, sub_circuit_gates: List[str]) -> Circuit:
    pass
