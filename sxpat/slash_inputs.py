from __future__ import annotations
from typing import Callable, List, Optional, Sequence, Tuple

import os
from os.path import join as path_join

from sxpat.converting import VerilogExporter
from sxpat.definitions.templates.InputsReplace import InputsReplace
from sxpat.graph.graph import IOGraph
from sxpat.newag import load_circuit_from_verilog
from sxpat.solvers import get_specialized as get_solver
from sxpat.specifications import SlashType, Specifications
from sxpat.utils.print import pprint
from sxpat.utils.timer import default_counter


__all__ = ['remove_inputs']


# number of groups the inputs of a benchmark are split into when slashing
# NOTE: this is benchmark specific, a more general strategy should be investigated
INPUT_GROUPS: dict[str, int] = {
    'abs_diff': 2,
    'adder': 2,
    'madd': 3,
    'mul': 2,
    'sad': 5,
}


def input_groups(benchmark_name: str) -> int:
    """
        Returns the number of groups the inputs of the given benchmark are split into.

        Unknown benchmarks are treated as a single group.
    """

    benchmark = os.path.basename(benchmark_name)
    for name, groups in INPUT_GROUPS.items():
        if benchmark.startswith(name):
            return groups

    pprint.warning(f'Unknown benchmark {benchmark!r}, defaulting to a single input group for the slash pass')
    return 1


def _selected_nodes(exact: IOGraph, inputs_per_group: int, groups: int) -> List[str]:
    """
        Given a circuit and the wanted number of inputs to remove from each group,
        returns the names of the inputs to slash.

        The inputs are split into `groups` consecutive chunks of equal size; the
        first `inputs_per_group` inputs of each chunk are selected.
    """
    chunk_size = len(exact.inputs_names) // groups
    return [
        f'in{group * chunk_size + offset}'
        for group in range(groups)
        for offset in range(inputs_per_group)
    ]


def calculate(exact: IOGraph, specs_obj: Specifications, inputs_per_group: int, groups: int) -> Tuple[bool, Optional[bool]]:
    """
        Attempts to replace `inputs_per_group` inputs of each group with a single
        shared boolean value.

        :returns: whether the replacement keeps the circuit within `error_for_slash`
            of the original, and (if so) the boolean value to use.
    """

    selected_nodes = _selected_nodes(exact, inputs_per_group, groups)
    p_graph, c_graph = InputsReplace.define(exact, specs_obj, selected_nodes)
    status, model = get_solver(specs_obj).solve((exact, p_graph, c_graph), specs_obj)

    if status == 'sat':
        return (True, model['constant_ID'])
    return (False, None)


def slash_iteratively(exact: IOGraph, specs_obj: Specifications, groups: int) -> Tuple[List[str], bool]:
    """
        Slashes as many inputs as possible (uniformly across the groups) while keeping
        the resulting circuit within `error_for_slash` of the original.

        :returns: the names of the slashed inputs and the boolean value they are tied to.
    """

    inputs_per_group = len(exact.inputs_names) // groups
    while inputs_per_group > 0:
        status, constant = calculate(exact, specs_obj, inputs_per_group, groups)
        if status:
            return (_selected_nodes(exact, inputs_per_group, groups), constant)
        inputs_per_group -= 1

    return ([], False)


SLASH_STRATEGIES: dict[SlashType, Callable[[IOGraph, Specifications, int], Tuple[List[str], bool]]] = {
    SlashType.SLASH_INPUT_ITERATIVE: slash_iteratively,
}


def _slash_graph(exact: IOGraph, selected_nodes: Sequence[str], constant: bool) -> IOGraph:
    """
        Builds the circuit resulting from replacing the selected inputs with the given constant.

        All the original inputs are kept (the slashed ones become unused), so that the
        resulting circuit shares its input space with the original one and the error
        between the two can be evaluated.
    """

    graph = InputsReplace.build(exact, selected_nodes, replace_output=False, replace_with_constant=constant)
    return IOGraph(graph.nodes, graph.inputs_names, graph.outputs_names)


def _slash_error(exact: IOGraph, slashed: IOGraph, specs_obj: Specifications) -> int:
    """Evaluates the maximum error between the exact circuit and the slashed one."""

    from sxpat.xplore import error_evaluation
    return error_evaluation(exact, slashed, specs_obj)


def remove_inputs(specs_obj: Specifications, benchmark_name: str) -> Tuple[str, int]:
    """
        Runs the "slash of inputs" pass on the exact benchmark and exports the
        resulting circuit in Verilog format.

        :param benchmark_name: the name of the original benchmark, used to determine
            the input grouping (as `specs_obj.exact_benchmark` points to the stored copy).
        :returns: the path of the generated Verilog file and the maximum error between
            the exact circuit and the slashed one.
    """

    # load the exact circuit
    exact = load_circuit_from_verilog(specs_obj.exact_benchmark, specs_obj.path.run)

    if specs_obj.error_for_slash is None:
        raise ValueError('The slash pass requires an error threshold, set `--error-for-slash`')

    # determine the strategy and the number of groups
    groups = input_groups(benchmark_name)
    strategy = SLASH_STRATEGIES[specs_obj.slash]

    # find the inputs to slash
    start = default_counter()
    selected_nodes, constant = strategy(exact, specs_obj, groups)
    pprint.info2(f'slash of inputs: slashed {len(selected_nodes)}/{len(exact.inputs_names)} inputs '
                 f'to {int(constant)} {selected_nodes} in {default_counter() - start:.2f}s')

    # build the slashed circuit (sharing the inputs with the exact one) and evaluate it
    slashed = _slash_graph(exact, selected_nodes, constant)
    error = _slash_error(exact, slashed, specs_obj)

    # export the slashed circuit in Verilog format
    # NOTE: all the original inputs are kept (the slashed ones are unused), so that the
    #       circuit keeps the same input space as the exact one throughout the pipeline
    circuit_id = 'gen_slash'
    verilog_path = path_join(specs_obj.path.run.verilog, f'{circuit_id}.v')
    VerilogExporter.to_file(
        slashed, verilog_path,
        VerilogExporter.Info(model_number=0),
    )

    return (verilog_path, error)
