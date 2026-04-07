from __future__ import annotations
from typing import Any, Callable, Dict, Iterable, Iterator, List, Tuple, TypeVar
import dataclasses as dc
from pathlib import Path

from tabulate import tabulate
import functools as ft
import csv
import json
import time
import math
import re
import networkx as nx
from Z3Log.config import path as z3logpath

from sxpat.labeling import labeling_explicit
from sxpat.metrics import MetricsEstimator
from sxpat.specifications import (
    Specifications,
    TemplateType,
    ErrorPartitioningType,
    MetricType,
    CnnErrorConstraintTypes,
    TerminationMode,
)
from sxpat.config import paths as sxpatpaths
from sxpat.config.config import *
from sxpat.utils.filesystem import FS
from sxpat.utils.name import NameData
from sxpat.verification import erroreval_verification_wce
from sxpat.stats import Stats, sxpatconfig, Model
from sxpat.annotatedGraph import AnnotatedGraph

from sxpat.templating import get_specialized as get_templater
from sxpat.solving import get_specialized as get_solver
from sxpat.templating.constraints_definition import (
    ERROR_THRESHOLD_ARRAYS_PATH,
    generate_zone_aet_thresholds,
)

from sxpat.converting import VerilogExporter
from sxpat.converting import iograph_from_legacy, sgraph_from_legacy
from sxpat.converting import set_bool_constants, prevent_combination

from sxpat.utils.utils import pprint

# todo: try picking up the different zones values, for instance 270 (max aet) minus the zone number * zone error introcued

_BENCHMARK_WIDTHS_RE = re.compile(r'_i(?P<input_bits>\d+)_o(?P<output_bits>\d+)$')


def _parse_benchmark_widths(benchmark_name: str) -> Tuple[int | None, int | None]:
    """
    Parse benchmark names like `mul_i10_o10`.

    Returns:
        A pair `(input_bits, output_bits)`, for example `(10, 10)`.
        If the benchmark name does not match the expected suffix format,
        returns `(None, None)`.
    """
    if (match := _BENCHMARK_WIDTHS_RE.search(benchmark_name)) is None:
        return (None, None)
    return (int(match.group('input_bits')), int(match.group('output_bits')))


def _get_operand_input_bits(benchmark_name: str) -> int | None:
    """
    Get the `input_bits` from the names like `mul_i10_o10`
    """
    input_bits, _ = _parse_benchmark_widths(benchmark_name)
    if input_bits is None or input_bits <= 0 or input_bits % 2 != 0:
        return None
    return input_bits // 2


def _get_max_output_node(specs_obj: Specifications) -> int | None:
    """
    Get the `output_bits` or the last node of the exact benchmark from the `Specifications`
    """
    _, output_bits = _parse_benchmark_widths(specs_obj.exact_benchmark)
    if output_bits is None or output_bits <= 0:
        return None
    return output_bits


def _get_max_nine_zone_scale(specs_obj: Specifications) -> int | None:
    # get the operands bits
    operand_bits = _get_operand_input_bits(specs_obj.exact_benchmark)
    # handle the edge cases
    if operand_bits is None or specs_obj.alpha is None or specs_obj.beta is None or specs_obj.beta <= 0:
        return None

    max_input_value = (2 ** operand_bits) - 1
    half = max_input_value // 2
    max_distance_from_half = max(abs(max_input_value - half), half)
    # (|x - x_mid| * alpha + y) // beta
    # problem: taking the MAX value independently 
    numerator_max = (max_distance_from_half * specs_obj.alpha) + max_input_value
    return max(1, numerator_max // specs_obj.beta)


@ft.lru_cache(maxsize=None)
def _load_explicit_thresholds(threshold_array_idx: int) -> Tuple[int, ...] | None:
    try:
        with open(ERROR_THRESHOLD_ARRAYS_PATH, 'r') as thresholds_file:
            threshold_arrays = json.load(thresholds_file)
        return tuple(int(value) for value in threshold_arrays[threshold_array_idx]['values'])
    except (FileNotFoundError, IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def _get_termination_error_ceiling(specs_obj: Specifications) -> int | None:
    # extraction-mode 0 walks output bits from least to most significant.  this
    # helper converts the active error constraint into a single "largest legal
    # absolute error" ceiling so we can stop as soon as the next bit weight is
    # mathematically impossible.
    if specs_obj.metric is MetricType.ABSOLUTE:
        return specs_obj.max_error

    cnn_constraint = getattr(specs_obj, 'cnn_constraint', None)
    if cnn_constraint is None:
        return None

    if cnn_constraint is CnnErrorConstraintTypes.NINE:
        if (max_zone_scale := _get_max_nine_zone_scale(specs_obj)) is None:
            return None
        return max_zone_scale * specs_obj.max_error

    if cnn_constraint is CnnErrorConstraintTypes.NINE_PRIME:
        if (
            (max_zone_scale := _get_max_nine_zone_scale(specs_obj)) is None
            or specs_obj.c_constant is None
        ):
            return None

        constraint_validity = 45
        if max_zone_scale > constraint_validity:
            return None

        return specs_obj.max_error + (max_zone_scale * specs_obj.c_constant)

    if cnn_constraint is CnnErrorConstraintTypes.EXPLICIT:
        if specs_obj.beta is None or specs_obj.beta <= 0:
            return None

        if (thresholds := _load_explicit_thresholds(specs_obj.threshold_array_idx)) is None:
            return None

        expected_num_thresholds = (256 // specs_obj.beta) ** 2
        if len(thresholds) != expected_num_thresholds:
            return None

        return max(thresholds)

    if cnn_constraint is CnnErrorConstraintTypes.ZONE_AET:
        if (
            specs_obj.beta is None
            or specs_obj.beta <= 0
            or specs_obj.alpha is None
        ):
            return None

        thresholds = generate_zone_aet_thresholds(
            input_count=_get_operand_input_bits(specs_obj.exact_benchmark) * 2
            if _get_operand_input_bits(specs_obj.exact_benchmark) is not None else 0,
            base_error=specs_obj.max_error,
            beta=specs_obj.beta,
            alpha=specs_obj.alpha,
        )
        return max(thresholds) if thresholds else None

    return None


@dc.dataclass(frozen=True)
class TerminationSnapshot:
    # bundle the termination decision together with the values keep
    # in the human log and the machine-readable trace/summary files.
    mode: str
    out_node: int | None
    bit_weight: int | None
    ceiling: int | None
    should_stop: bool
    reason: str | None = None
    message_lines: Tuple[str, ...] = ()


def _check_termination(specs_obj: Specifications, max_out_node: int | None) -> TerminationSnapshot:
    if specs_obj.extraction_mode != 0:
        return TerminationSnapshot(
            mode=specs_obj.termination_mode.value,
            out_node=None,
            bit_weight=None,
            ceiling=None,
            should_stop=False,
        )

    out_node = specs_obj.out_node
    bit_weight = 2 ** out_node

    if specs_obj.termination_mode is TerminationMode.TRIVIAL:
        # if the current bit alone already exceeds the strongest legal
        # error permitted by the active constraint, there is no
        # point exploring higher bits.
        ceiling = _get_termination_error_ceiling(specs_obj)
        if ceiling is not None and bit_weight > ceiling:
            return TerminationSnapshot(
                mode=specs_obj.termination_mode.value,
                out_node=out_node,
                bit_weight=bit_weight,
                ceiling=ceiling,
                should_stop=True,
                reason='trivial_termination',
                message_lines=(
                    '',
                    '[!] TRIVIAL TERMINATION FIRED!',
                    f'Max legal error ceiling for the active constraint is {ceiling}.',
                    f'Bit {out_node} weight ({bit_weight}) is strictly impossible. Stopping exploration.',
                    '',
                ),
            )
    else:
        ceiling = None

    if max_out_node is not None and max_out_node == out_node:
        return TerminationSnapshot(
            mode=specs_obj.termination_mode.value,
            out_node=out_node,
            bit_weight=bit_weight,
            ceiling=ceiling,
            should_stop=True,
            reason='error_space_exhausted',
            message_lines=('The error space is exhausted (reached max bit)!',),
        )

    return TerminationSnapshot(
        mode=specs_obj.termination_mode.value,
        out_node=out_node,
        bit_weight=bit_weight,
        ceiling=ceiling,
        should_stop=False,
    )


def _verification_limit(specs_obj: Specifications) -> int:
    """
    Returns the error bound that verification should compare against
    """
    if specs_obj.metric is MetricType.ABSOLUTE:
        return specs_obj.et
    return specs_obj.max_error


def _is_plain_metric_verification(specs_obj: Specifications) -> bool:
    """
    true when:
     - metric is absolute, or
     - there is no CNN-style zone constraint
    """
    return specs_obj.metric is MetricType.ABSOLUTE or specs_obj.cnn_constraint is None


def _store_trace_row(trace_rows: List[Dict[str, Any]], **kwargs: Any) -> None:
    trace_rows.append(kwargs)


def _dominates_pareto(candidate: Dict[str, float], incumbent: Dict[str, float]) -> bool:
    candidate_metrics = (candidate['area'], candidate['power'], candidate['delay'])
    incumbent_metrics = (incumbent['area'], incumbent['power'], incumbent['delay'])
    return (
        all(c_metric <= i_metric for c_metric, i_metric in zip(candidate_metrics, incumbent_metrics))
        and any(c_metric < i_metric for c_metric, i_metric in zip(candidate_metrics, incumbent_metrics))
    )


def _update_pareto_frontier(frontier: List[Dict[str, Any]], point: Dict[str, Any]) -> bool:
    # return True iff the new point expands the frontier; otherwise it is
    # dominated by an existing point and provides no new Pareto tradeoff.
    if any(_dominates_pareto(existing, point) for existing in frontier):
        return False

    frontier[:] = [existing for existing in frontier if not _dominates_pareto(point, existing)]
    frontier.append(point)
    return True


def _write_termination_trace(summary_stem: str, trace_rows: List[Dict[str, Any]]) -> str:
    # the csv trace stores one row per outer exploration iteration so sweeps can
    # be analyzed without reparsing the verbose console log.
    folder = f"{sxpatpaths.OUTPUT_PATH['report'][0]}/termination_study"
    FS.mkdir(folder)
    trace_path = f'{folder}/{summary_stem}_trace.csv'
    fieldnames = [
        'iteration',
        'termination_mode',
        'stop_reason',
        'out_node',
        'bit_weight',
        'termination_ceiling',
        'et',
        'benchmark',
        'selected_cell',
        'status',
        'best_area',
        'best_power',
        'best_delay',
        'verified_error_exact',
        'verified_error_prev',
        'subgraph_available',
        'subgraph_repeated',
        'pareto_efficient',
        'pareto_frontier_size',
        'pareto_stagnation',
    ]
    with open(trace_path, 'w', newline='') as trace_file:
        writer = csv.DictWriter(trace_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in trace_rows:
            writer.writerow({key: row.get(key) for key in fieldnames})
    return trace_path


def _write_termination_summary(summary_stem: str, summary_data: Dict[str, Any]) -> str:
    # the json summary is the compact run-level companion to the per-iteration
    # trace above.
    folder = f"{sxpatpaths.OUTPUT_PATH['report'][0]}/termination_study"
    FS.mkdir(folder)
    summary_path = f'{folder}/{summary_stem}_summary.json'
    with open(summary_path, 'w') as summary_file:
        json.dump(summary_data, summary_file, indent=2, sort_keys=True)
    return summary_path


def _verify_candidate_errors(specs_obj: Specifications, candidate_name: str) -> Tuple[int, int]:
    if specs_obj.skip_verification:
        # negative sentinel so later ranking/reporting knows verification was
        # intentionally omitted rather than forgotten.
        return (-1, -1)

    candidate_benchmark = Path(candidate_name).stem
    exact_error = erroreval_verification_wce(
        specs_obj.exact_benchmark,
        candidate_benchmark,
        specs_obj.metric,
    )
    prev_error = erroreval_verification_wce(
        specs_obj.current_benchmark,
        candidate_benchmark,
        specs_obj.metric,
    )
    return (exact_error, prev_error)


def explore_grid(specs_obj: Specifications):
    previous_subgraphs = []

    labeling_time: float = -1
    subgraph_extraction_time: float = -1

    # used for remove_most_significant_output
    removed_output = False

    # Select toolname
    toolname = get_toolname(specs_obj)

    # initial setup
    exact_file_path = f'{sxpatpaths.INPUT_PATH["ver"][0]}/{specs_obj.exact_benchmark}.v'
    # create stat and template object
    stats_obj = Stats(specs_obj)
    # reuse the grid filename stem so every run also gets matching trace and
    # summary sidecars with predictable names.
    summary_stem = Path(stats_obj.grid_name).stem

    specs_obj.et = specs_obj.max_error
    obtained_wce_exact = 0
    specs_obj.iteration = 0
    persistance = 0
    persistance_limit = specs_obj.persistance
    prev_actual_error = 0 if specs_obj.subxpat else 1
    prev_given_error = 0
    max_out_node = _get_max_output_node(specs_obj) if specs_obj.extraction_mode == 0 else None
    pareto_frontier: List[Dict[str, Any]] = []
    pareto_stagnation = 0

    run_started_at = time.time()
    trace_rows: List[Dict[str, Any]] = []
    last_selected_result: Dict[str, Any] | None = None
    stop_snapshot: TerminationSnapshot | None = None
    stop_reason: str | None = None

    # gradual error budget relaxation
    if specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING:
        orig_et = specs_obj.max_error if specs_obj.zone_constraint is None else 100
        if orig_et <= 8:
            et_array = iter(list(range(1, orig_et + 1, 1)))
        else:
            step = orig_et // specs_obj.partition_divider if orig_et // specs_obj.partition_divider > 0 else 1
            list_values = list(range(step, orig_et + step, step))
            et_array = iter(list_values)
    elif specs_obj.error_partitioning is ErrorPartitioningType.EXPONENTIAL:
        et_array = iter([2 ** i for i in range(8)])

    while (obtained_wce_exact <= specs_obj.max_error or specs_obj.extraction_mode == 0):
        specs_obj.iteration += 1
        status = None
        best_data = None
        best_name = None
        selected_result_this_iteration = False

        # Record one trace row per outer iteration, even if we later discover
        # there was no usable subgraph or no SAT model in the selected cell.
        trace_row: Dict[str, Any] = {
            'iteration': specs_obj.iteration,
            'termination_mode': specs_obj.termination_mode.value,
            'stop_reason': None,
            'out_node': specs_obj.out_node if specs_obj.extraction_mode == 0 else None,
            'bit_weight': None,
            'termination_ceiling': None,
            'et': specs_obj.et,
            'benchmark': specs_obj.current_benchmark,
            'selected_cell': None,
            'status': None,
            'best_area': None,
            'best_power': None,
            'best_delay': None,
            'verified_error_exact': None,
            'verified_error_prev': None,
            'subgraph_available': None,
            'subgraph_repeated': False,
            'pareto_efficient': None,
            'pareto_frontier_size': len(pareto_frontier),
            'pareto_stagnation': pareto_stagnation,
        }

        if not specs_obj.subxpat:
            if prev_actual_error == 0:
                stop_reason = 'no_progress'
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                _store_trace_row(trace_rows, **trace_row)
                break
            specs_obj.et = specs_obj.max_error
        elif specs_obj.extraction_mode == 0:
            print(f"Current out_node: {specs_obj.out_node}")
            # termination logic
            snapshot = _check_termination(specs_obj, max_out_node)
            trace_row['out_node'] = snapshot.out_node
            trace_row['bit_weight'] = snapshot.bit_weight
            trace_row['termination_ceiling'] = snapshot.ceiling
            if snapshot.should_stop:
                stop_snapshot = snapshot
                stop_reason = snapshot.reason
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                if snapshot.reason == 'error_space_exhausted':
                    pprint.warning(snapshot.message_lines[0])
                else:
                    print('\n'.join(snapshot.message_lines))
                _store_trace_row(trace_rows, **trace_row)
                break
        elif (
            specs_obj.error_partitioning is ErrorPartitioningType.ASCENDING
            or specs_obj.error_partitioning is ErrorPartitioningType.EXPONENTIAL
        ):
            if persistance == persistance_limit or prev_actual_error == 0:
                persistance = 0
                try:
                    specs_obj.et = next(et_array)
                except StopIteration:
                    stop_reason = 'error_space_exhausted'
                    trace_row['stop_reason'] = stop_reason
                    trace_row['status'] = 'STOPPED'
                    pprint.warning('The error space is exhausted!')
                    _store_trace_row(trace_rows, **trace_row)
                    break
            else:
                persistance += 1
        elif specs_obj.error_partitioning is ErrorPartitioningType.DESCENDING:
            log2 = int(math.log2(specs_obj.max_error))
            specs_obj.et = 2 ** (log2 - specs_obj.iteration - 2)
        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_ASCENDING:
            specs_obj.et = 1 if specs_obj.iteration == 1 else prev_given_error * (2 if prev_actual_error == 0 else 1)
            prev_given_error = specs_obj.et
        elif specs_obj.error_partitioning is ErrorPartitioningType.SMART_DESCENDING:
            specs_obj.et = specs_obj.max_error if specs_obj.iteration == 1 else math.ceil(prev_given_error / (2 if prev_actual_error == 0 else 1))
            prev_given_error = specs_obj.et
        else:
            raise NotImplementedError('invalid status')

        trace_row['et'] = specs_obj.et

        if (specs_obj.et > specs_obj.max_error and specs_obj.metric != MetricType.RELATIVE) or specs_obj.et <= 0:
            stop_reason = 'invalid_et'
            trace_row['stop_reason'] = stop_reason
            trace_row['status'] = 'STOPPED'
            _store_trace_row(trace_rows, **trace_row)
            break

        pprint.info1(
            f'iteration {specs_obj.iteration} with et {specs_obj.et}, available error {specs_obj.max_error}'
            if specs_obj.subxpat else
            f'Only one iteration with et {specs_obj.et}'
        )

        if specs_obj.current_benchmark.endswith('.v'):
            specs_obj.current_benchmark = specs_obj.current_benchmark[:-2]
        pprint.info1(f'benchmark {specs_obj.current_benchmark}')
        trace_row['benchmark'] = specs_obj.current_benchmark

        # import the graph
        exact_graph = AnnotatedGraph(specs_obj.exact_benchmark, is_clean=False)
        current_graph = AnnotatedGraph(specs_obj.current_benchmark, is_clean=False)

        if specs_obj.remove_most_significant_output:
            if removed_output:
                specs_obj.extraction_mode = saved_extraction_mode
                specs_obj.baseet = saved_baseet
                specs_obj.remove_most_significant_output = False
            else:
                saved_extraction_mode = specs_obj.extraction_mode
                saved_baseet = specs_obj.baseet
                specs_obj.extraction_mode = 123
                specs_obj.baseet = 2 ** exact_graph.num_outputs - 1
                removed_output = True

        # label graph
        if specs_obj.requires_labeling:
            et_coefficient = 1
            print(f"Started labeling with et = {specs_obj.et}")
            label_timer, _label_graph = Timer.from_function(label_graph)

            _label_graph(
                current_graph,
                min_labeling=specs_obj.min_labeling,
                partial=specs_obj.partial_labeling,
                et=specs_obj.et * et_coefficient,
                parallel=specs_obj.parallel,
                metric=specs_obj.metric,
            )
            print(f'labeling_time = {(labeling_time := label_timer.total)}')

        # extract subgraph
        subex_timer, extract_subgraph = Timer.from_function(current_graph.extract_subgraph)
        subgraph_is_available = extract_subgraph(specs_obj)
        previous_subgraphs.append(current_graph.subgraph)
        print(f'subgraph_extraction_time = {(subgraph_extraction_time := subex_timer.total)}')

        trace_row['subgraph_available'] = subgraph_is_available

        FS.mkdir(folder := 'output/gv/subgraphs')
        graph_path = (
            f'{folder}/{specs_obj.current_benchmark}_et{specs_obj.et}_'
            f'term{specs_obj.termination_mode.value}_mode{specs_obj.extraction_mode}_omax{specs_obj.omax}.gv'
        )
        current_graph.export_annotated_graph(graph_path)
        print(f'subgraph exported at {graph_path}')

        if not subgraph_is_available:
            pprint.warning('No subgraph available.')
            trace_row['status'] = 'NO_SUBGRAPH'
            _store_trace_row(trace_rows, **trace_row)
            prev_actual_error = 0
            continue

        if (
            len(previous_subgraphs) >= 2
            and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        ):
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            trace_row['status'] = 'DUPLICATE_SUBGRAPH'
            trace_row['subgraph_repeated'] = True
            _store_trace_row(trace_rows, **trace_row)
            prev_actual_error = 0
            continue

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        exact_stats = MetricsEstimator.estimate_metrics(exact_file_path)

        for lpp, ppo in CellIterator.factory(specs_obj):
            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info1(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> DOMINATED')
                continue

            # > cell step settings
            # update the context
            update_context(specs_obj, lpp, ppo)

            # convert from legacy graph to new architecture graph
            e_graph = iograph_from_legacy(exact_graph)
            s_graph = sgraph_from_legacy(current_graph)

            # define template (and constraints)
            template_timer, define_template = Timer.from_function(get_templater(specs_obj).define)
            p_graph, c_graph = define_template(s_graph, specs_obj)

            # solve
            solve_timer, solve = Timer.from_function(get_solver(specs_obj).solve)
            models = []
            for _ in range(specs_obj.wanted_models):
                status, model = solve((e_graph, p_graph, c_graph), specs_obj)
                if status != 'sat':
                    break
                models.append(model)
                c_graph = prevent_combination(c_graph, model)

            # legacy adaptation
            execution_time = template_timer.total + solve_timer.total

            if len(models) == 0:
                pprint.warning(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {status.upper()}')

                # store model
                this_model_info = Model(
                    id=0,
                    status=status.upper(),
                    cell=(lpp, ppo),
                    et=specs_obj.et,
                    iteration=specs_obj.iteration,
                    out_node=specs_obj.out_node if specs_obj.extraction_mode == 0 else -1,
                    runtime=execution_time,
                    labeling_time=labeling_time,
                    subgraph_extraction_time=subgraph_extraction_time,
                    subgraph_number_inputs=current_graph.subgraph_num_inputs,
                    subgraph_number_outputs=current_graph.subgraph_num_outputs,
                    subxpat_v1_time=execution_time,
                )
                stats_obj.grid.cells[lpp][ppo].store_model_info(this_model_info)

                if status == UNKNOWN:
                    # store cell as dominant (to skip dominated subgrid)
                    dominant_cells.append((lpp, ppo))

            else:
                pprint.success(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {status.upper()} ({len(models)} models found)')

                # keep both qor metrics and verified errors for every candidate
                # so post-processing can reconstruct why a specific circuit was
                # chosen as "best" for this iteration.
                cur_model_results: Dict[str, List[float]] = {}
                for i, model in enumerate(models):
                    # finalize approximate graph
                    a_graph = set_bool_constants(p_graph, model)

                    # export approximate graph as verilog
                    # TODO:#15: use serious name generator
                    verilog_path = f'input/ver/{specs_obj.exact_benchmark}_{int(time.time())}_{i}.v'
                    VerilogExporter.to_file(a_graph, verilog_path)

                    # compute metrics
                    metrics = MetricsEstimator.estimate_metrics(verilog_path)
                    verilog_filename = verilog_path[10:]
                    verified_exact, verified_prev = _verify_candidate_errors(specs_obj, verilog_filename)
                    cur_model_results[verilog_filename] = [
                        metrics.area,
                        metrics.power,
                        metrics.delay,
                        (lpp, ppo),
                        verified_exact,
                        verified_prev,
                    ]

                with open(
                    f'{z3logpath.OUTPUT_PATH["report"][0]}/area_model_nummodels'
                    f'{specs_obj.wanted_models}_{specs_obj.current_benchmark}_{specs_obj.et}_'
                    f'{toolname}_term{specs_obj.termination_mode.value}.csv',
                    'w',
                ) as f:
                    csvwriter = csv.writer(f)
                    header = list(range(len(cur_model_results)))
                    all_values = list(cur_model_results.values())
                    content = [value for (value, *_) in all_values]
                    csvwriter.writerow(header)
                    csvwriter.writerow(content)

                if _is_plain_metric_verification(specs_obj):
                    verification_limit = _verification_limit(specs_obj)
                    for candidate_name, candidate_data in cur_model_results.items():
                        if candidate_data[4] >= 0 and candidate_data[4] > verification_limit:
                            pprint.warning(
                                f'Verification exceeded the configured error bound for {candidate_name}: '
                                f'{candidate_data[4]} > {verification_limit}'
                            )

                pprint.success('ErrorEval Verification PASSED')

                # sort circuits
                sorted_circuits = sorted(cur_model_results.items(), key=ft.cmp_to_key(model_compare))

                # select best circuit
                best_name, best_data = sorted_circuits[0]
                #obtained_wce_exact = best_data[4]
                if best_data[4] >= 0:
                    obtained_wce_exact = best_data[4]
                prev_actual_error = best_data[5] if best_data[5] >= 0 else 0

                specs_obj.current_benchmark = best_name
                best_model_info = Model(
                    id=0,
                    status=status.upper(),
                    cell=(lpp, ppo),
                    et=specs_obj.et,
                    iteration=specs_obj.iteration,
                    out_node=specs_obj.out_node if specs_obj.extraction_mode == 0 else -1,
                    runtime=execution_time,
                    area=best_data[0],
                    total_power=best_data[1],
                    delay=best_data[2],
                    verified_error_exact=best_data[4],
                    verified_error_prev=best_data[5],
                    labeling_time=labeling_time,
                    subgraph_extraction_time=subgraph_extraction_time,
                    subgraph_number_inputs=current_graph.subgraph_num_inputs,
                    subgraph_number_outputs=current_graph.subgraph_num_outputs,
                    subxpat_v1_time=execution_time,
                )

                stats_obj.grid.cells[lpp][ppo].store_model_info(best_model_info)
                pprint.success(f'ErrorEval PASS! with total wce = {best_data[4]}')

                trace_row['selected_cell'] = str((lpp, ppo))
                trace_row['status'] = status.upper()
                trace_row['best_area'] = best_data[0]
                trace_row['best_power'] = best_data[1]
                trace_row['best_delay'] = best_data[2]
                trace_row['verified_error_exact'] = best_data[4]
                trace_row['verified_error_prev'] = best_data[5]

                last_selected_result = {
                    'benchmark': best_name,
                    'area': best_data[0],
                    'power': best_data[1],
                    'delay': best_data[2],
                    'verified_error_exact': best_data[4],
                    'verified_error_prev': best_data[5],
                    'cell': (lpp, ppo),
                }
                selected_result_this_iteration = True

                if specs_obj.termination_mode is TerminationMode.PARETO:
                    is_pareto_efficient = _update_pareto_frontier(pareto_frontier, last_selected_result)
                    pareto_stagnation = 0 if is_pareto_efficient else pareto_stagnation + 1
                    trace_row['pareto_efficient'] = is_pareto_efficient
                    trace_row['pareto_frontier_size'] = len(pareto_frontier)
                    trace_row['pareto_stagnation'] = pareto_stagnation

                print_current_model(sorted_circuits, normalize=False, exact_stats=exact_stats)
                store_current_model(
                    cur_model_results,
                    exact_stats=exact_stats,
                    benchmark_name=specs_obj.current_benchmark,
                    et=specs_obj.et,
                    encoding=specs_obj.encoding,
                    subgraph_extraction_time=subgraph_extraction_time,
                    labeling_time=labeling_time,
                    termination_mode=specs_obj.termination_mode.value,
                )

                break

            prev_actual_error = 0

        if (
            specs_obj.termination_mode is TerminationMode.PARETO
            and selected_result_this_iteration
            and pareto_stagnation >= persistance_limit
        ):
            stop_reason = 'pareto_termination'
            trace_row['stop_reason'] = stop_reason
            trace_row['status'] = 'STOPPED'
            trace_row['pareto_frontier_size'] = len(pareto_frontier)
            trace_row['pareto_stagnation'] = pareto_stagnation
            pprint.warning(
                'Pareto termination fired: no new non-dominated '
                f'(area, power, delay) point in the last {pareto_stagnation} accepted iteration(s).'
            )
            _store_trace_row(trace_rows, **trace_row)
            break

        if trace_row['status'] is None and status is not None:
            trace_row['status'] = status.upper()
        if trace_row['pareto_frontier_size'] is None:
            trace_row['pareto_frontier_size'] = len(pareto_frontier)
        if trace_row['pareto_stagnation'] is None:
            trace_row['pareto_stagnation'] = pareto_stagnation
        _store_trace_row(trace_rows, **trace_row)

        if status == SAT and best_data[0] == 0:
            stop_reason = 'area_zero_found'
            pprint.info3('Area zero found!\nTerminated.')
            break

    stats_obj.store_grid()

    # emit one compact json blob at the end of the run so bulk experiments can
    # inspect the outcome without scanning the full console log.
    summary_data = {
        'exact_benchmark': specs_obj.exact_benchmark,
        'final_benchmark': specs_obj.current_benchmark,
        'termination_mode': specs_obj.termination_mode.value,
        'metric': specs_obj.metric.value,
        'cnn_constraint': specs_obj.cnn_constraint.value if specs_obj.cnn_constraint is not None else None,
        'extraction_mode': specs_obj.extraction_mode,
        'imax': specs_obj.imax,
        'omax': specs_obj.omax,
        'max_error': specs_obj.max_error,
        'alpha': specs_obj.alpha,
        'beta': specs_obj.beta,
        'c_constant': specs_obj.c_constant,
        'threshold_array_idx': specs_obj.threshold_array_idx,
        'skip_verification': specs_obj.skip_verification,
        'iterations': specs_obj.iteration,
        'runtime_seconds': round(time.time() - run_started_at, 6),
        'stop_reason': stop_reason,
        'stop_out_node': None if stop_snapshot is None else stop_snapshot.out_node,
        'bit_weight_at_stop': None if stop_snapshot is None else stop_snapshot.bit_weight,
        'termination_ceiling': None if stop_snapshot is None else stop_snapshot.ceiling,
        'final_area': None if last_selected_result is None else last_selected_result['area'],
        'final_power': None if last_selected_result is None else last_selected_result['power'],
        'final_delay': None if last_selected_result is None else last_selected_result['delay'],
        'final_verified_error_exact': None if last_selected_result is None else last_selected_result['verified_error_exact'],
        'final_verified_error_prev': None if last_selected_result is None else last_selected_result['verified_error_prev'],
        'final_cell': None if last_selected_result is None else last_selected_result['cell'],
        'pareto_frontier_size': len(pareto_frontier),
        'pareto_stagnation': pareto_stagnation,
        'grid_csv': stats_obj.grid_path,
    }

    trace_path = _write_termination_trace(summary_stem, trace_rows)
    summary_data['trace_csv'] = trace_path
    summary_path = _write_termination_summary(summary_stem, summary_data)
    pprint.info2(f'termination summary stored at {summary_path}')

    return stats_obj


class CellIterator:
    @classmethod
    def factory(cls, specs: Specifications) -> Iterator[Tuple[int, int]]:
        return {
            TemplateType.NON_SHARED: cls.non_shared,
            TemplateType.SHARED: cls.shared,
        }[specs.template](specs)

    @staticmethod
    def shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_pit = specs.max_pit

        # special cell
        yield (0, 1)

        # grid cells
        for pit in range(1, max_pit + 1):
            for its in range(pit, pit + 3 + 1):
                yield (its, pit)

    @staticmethod
    def non_shared(specs: Specifications) -> Iterator[Tuple[int, int]]:
        max_lpp = specs.max_lpp
        max_ppo = specs.max_ppo

        # special cell
        yield (0, 1)

        # grid cells
        for ppo in range(1, max_ppo + 1):
            for lpp in range(1, max_lpp + 1):
                yield (lpp, ppo)


def is_dominated(coords: Tuple[int, int], dominant_cells: Iterable[Tuple[int, int]]) -> bool:
    (lpp, ppo) = coords
    return any(
        lpp >= dom_lpp and ppo >= dom_ppo
        for (dom_lpp, dom_ppo) in dominant_cells
    )


def update_context(specs_obj: Specifications, lpp: int, ppo: int):
    specs_obj.lpp = lpp
    specs_obj.ppo = specs_obj.pit = ppo


def print_current_model(sorted_models: List[Tuple[str, List]], normalize: bool = True, exact_stats: List = None) -> None:
    data = []

    if exact_stats:
        # add exact circuit data
        e_area, e_power, e_delay, *_ = exact_stats
        data.append(['Exact', e_area, e_power, e_delay, 0])

        if normalize:
            for _, stats in sorted_models:
                stats[0] = (stats[0] / e_area) * 100
                stats[1] = (stats[1] / e_power) * 100
                stats[2] = (stats[2] / e_delay) * 100

    # keep wanted models
    if len(sorted_models) > 10:
        sorted_models = sorted_models[0:10]

    # add candidates data
    for c_name, c_stats in sorted_models:
        c_id = NameData.from_filename(c_name).total_id
        c_area, c_power, c_delay, _, c_error, _ = c_stats
        data.append([c_id, c_area, c_power, c_delay, c_error])

    pprint.success(tabulate(data, headers=['Design ID', 'Area', 'Power', 'Delay', 'Error']))


def store_current_model(
    cur_model_result: Dict,
    benchmark_name: str,
    et: int,
    encoding: int,
    subgraph_extraction_time: float,
    labeling_time: float,
    termination_mode: str,
    exact_stats: List = None,
) -> None:
    output_path = f"{z3logpath.OUTPUT_PATH['report'][0]}/area_power_delay.csv"
    write_header = not FS.exists(output_path)
    with open(output_path, 'a') as f:
        csvwriter = csv.writer(f)

        if write_header:
            csvwriter.writerow((
                'benchmark',
                'design_id',
                'area',
                'power',
                'delay',
                'verified_error_exact',
                'verified_error_prev',
                'et',
                'encoding',
                'termination_mode',
                'labeling_time',
                'subgraph_extraction_time',
            ))

        # to avoid duplicate data
        if exact_stats:
            e_area, e_power, e_delay, *_ = exact_stats
            exact_data = (
                benchmark_name,
                'Exact',
                e_area, e_power, e_delay,
                0, 0,
                et, encoding,
                termination_mode,
                labeling_time, subgraph_extraction_time,
            )
            csvwriter.writerow(exact_data)

        # get best candidate data
        sorted_candidates = sorted(cur_model_result.items(), key=ft.cmp_to_key(model_compare))
        c_name, c_stats = sorted_candidates[0]
        c_id = NameData.from_filename(c_name).total_id
        c_area, c_power, c_delay, _, c_error_exact, c_error_prev = c_stats

        approx_data = (
            benchmark_name,
            c_id,
            c_area, c_power, c_delay,
            c_error_exact, c_error_prev,
            et, encoding,
            termination_mode,
            labeling_time, subgraph_extraction_time,
        )
        csvwriter.writerow(approx_data)


def label_graph(current_graph: AnnotatedGraph,
                min_labeling: bool = False, partial: bool = False,
                et: int = -1, parallel: bool = False, metric: MetricType = MetricType.ABSOLUTE):
    labels, _ = labeling_explicit(current_graph.name, current_graph.name,
                                  constant_value=0, min_labeling=min_labeling,
                                  partial=partial, et=et, parallel=parallel, metric=metric)

    for n in current_graph.graph.nodes:
        current_graph.graph.nodes[n][WEIGHT] = int(labels[n]) if n in labels else -1


def get_toolname(specs_obj: Specifications) -> str:
    message, toolname = {
        (False, TemplateType.NON_SHARED): ('XPAT', sxpatconfig.XPAT),
        (False, TemplateType.SHARED): ('Shared XPAT', sxpatconfig.SHARED_XPAT),
        (True, TemplateType.NON_SHARED): ('SubXPAT', sxpatconfig.SUBXPAT),
        (True, TemplateType.SHARED): ('Shared SubXPAT', sxpatconfig.SHARED_SUBXPAT),
    }[(specs_obj.subxpat, specs_obj.template)]

    pprint.info2(f'{message} started...')
    return toolname


def node_matcher(n1: dict, n2: dict) -> bool:
    """Return if two node data dicts represent the same semantic node"""
    return (
        n1.get('label') == n2.get('label')
        and n1.get('subgraph', 0) == n2.get('subgraph', 0)
    )


def model_compare(a, b) -> bool:
    if a[1][0] < b[1][0]: return -1
    elif a[1][0] > b[1][0]: return +1
    elif a[1][4] < b[1][4]: return -1
    elif a[1][4] > b[1][4]: return +1
    else: return 0


@dc.dataclass(init=False, repr=False, eq=False, frozen=True)
class Timer:
    from time import time as now
    _C = TypeVar('_C', bound=Callable)

    total: float = 0
    last: float = 0

    def wrap(self, function: _C) -> _C:
        @ft.wraps(function)
        def wrapper(*args, **kwds):
            start_time = self.now()
            result = function(*args, **kwds)
            object.__setattr__(self, 'last', self.now() - start_time)
            object.__setattr__(self, 'total', self.total + self.last)
            return result
        return wrapper

    @classmethod
    def from_function(cls, function: _C) -> Tuple[Timer, _C]:
        timer = Timer()
        wrapped = timer.wrap(function)
        return (timer, wrapped)
