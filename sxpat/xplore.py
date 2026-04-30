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
import random
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
        ceiling, _, _ = _get_zone_aet_termination_threshold_selection(
            benchmark_name=specs_obj.exact_benchmark,
            base_error=specs_obj.max_error,
            beta=specs_obj.beta,
            alpha=specs_obj.alpha,
            rank_from_max=specs_obj.termination_zone_rank_from_max,
        )
        return ceiling

    return None


def _get_effective_zone_rank_from_max(specs_obj: Specifications, best_seen_stagnation: int) -> int:
    requested_rank = max(0, int(specs_obj.termination_zone_rank_from_max))
    if (
        specs_obj.cnn_constraint is not CnnErrorConstraintTypes.ZONE_AET
        or not specs_obj.adaptive_termination_zone_rank
    ):
        return requested_rank

    step_interval = max(1, int(specs_obj.adaptive_termination_zone_rank_step_interval))
    return requested_rank + (max(0, int(best_seen_stagnation)) // step_interval)


@ft.lru_cache(maxsize=None)
def _get_zone_aet_termination_threshold_selection(
    benchmark_name: str,
    base_error: int,
    beta: int | None,
    alpha: int | None,
    rank_from_max: int,
) -> Tuple[int | None, int | None, int | None]:
    operand_bits = _get_operand_input_bits(benchmark_name)
    if operand_bits is None or beta is None or beta <= 0 or alpha is None:
        return (None, None, None)

    thresholds = generate_zone_aet_thresholds(
        input_count=operand_bits * 2,
        base_error=base_error,
        beta=beta,
        alpha=alpha,
    )
    unique_levels = sorted(set(int(value) for value in thresholds))
    if not unique_levels:
        return (None, None, None)

    requested_rank = max(0, int(rank_from_max))
    applied_rank = min(requested_rank, len(unique_levels) - 1)
    return (unique_levels[-1 - applied_rank], applied_rank, len(unique_levels))


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
    zone_rank_requested: int | None = None
    zone_rank_effective: int | None = None
    zone_rank_applied: int | None = None
    zone_level_count: int | None = None
    best_seen_guard_blocked: bool = False
    best_seen_guard_gap_pct: float | None = None
    best_seen_stagnation: int | None = None


def _check_best_seen_guard(
    specs_obj: Specifications,
    current_result: Dict[str, Any] | None,
    best_seen_result: Dict[str, Any] | None,
) -> Tuple[bool, float | None, float | None, float | None]:
    guard_pct = float(getattr(specs_obj, 'best_seen_guard_pct', 0.0) or 0.0)
    if guard_pct <= 0.0 or current_result is None or best_seen_result is None:
        return (False, None, None, None)

    current_area = current_result.get('area')
    best_area = best_seen_result.get('area')
    if current_area is None or best_area is None or best_area <= 0:
        return (False, None, current_area, best_area)

    gap_pct = ((current_area - best_area) / best_area) * 100.0
    return (gap_pct > guard_pct, gap_pct, current_area, best_area)


def _check_termination(
    specs_obj: Specifications,
    max_out_node: int | None,
    current_result: Dict[str, Any] | None,
    best_seen_result: Dict[str, Any] | None,
    best_seen_stagnation: int,
) -> TerminationSnapshot:
    if specs_obj.extraction_mode != 0:
        return TerminationSnapshot(
            mode=specs_obj.termination_mode.value,
            out_node=None,
            bit_weight=None,
            ceiling=None,
            should_stop=False,
            zone_rank_requested=None,
            zone_rank_effective=None,
            zone_rank_applied=None,
            zone_level_count=None,
            best_seen_guard_blocked=False,
            best_seen_guard_gap_pct=None,
            best_seen_stagnation=best_seen_stagnation,
        )

    out_node = specs_obj.out_node
    bit_weight = 2 ** out_node
    zone_rank_requested = (
        specs_obj.termination_zone_rank_from_max
        if specs_obj.cnn_constraint is CnnErrorConstraintTypes.ZONE_AET
        else None
    )
    zone_rank_effective = zone_rank_requested
    zone_rank_applied = None
    zone_level_count = None

    if max_out_node is not None and max_out_node == out_node:
        return TerminationSnapshot(
            mode=specs_obj.termination_mode.value,
            out_node=out_node,
            bit_weight=bit_weight,
            ceiling=None,
            should_stop=True,
            reason='error_space_exhausted',
            message_lines=('The error space is exhausted (reached max bit)!',),
            zone_rank_requested=zone_rank_requested,
            zone_rank_effective=zone_rank_effective,
            zone_rank_applied=zone_rank_applied,
            zone_level_count=zone_level_count,
            best_seen_guard_blocked=False,
            best_seen_guard_gap_pct=None,
            best_seen_stagnation=best_seen_stagnation,
        )

    if specs_obj.termination_mode in {TerminationMode.TRIVIAL, TerminationMode.HYBRID, TerminationMode.SENTINEL}:
        # if the current bit alone already exceeds the strongest legal
        # error permitted by the active constraint, there is no
        # point exploring higher bits.
        if specs_obj.cnn_constraint is CnnErrorConstraintTypes.ZONE_AET:
            zone_rank_effective = _get_effective_zone_rank_from_max(specs_obj, best_seen_stagnation)
            ceiling, zone_rank_applied, zone_level_count = _get_zone_aet_termination_threshold_selection(
                benchmark_name=specs_obj.exact_benchmark,
                base_error=specs_obj.max_error,
                beta=specs_obj.beta,
                alpha=specs_obj.alpha,
                rank_from_max=zone_rank_effective,
            )
        else:
            ceiling = _get_termination_error_ceiling(specs_obj)
        if ceiling is not None and bit_weight > ceiling:
            guard_blocked, guard_gap_pct, current_area, best_area = _check_best_seen_guard(
                specs_obj,
                current_result=current_result,
                best_seen_result=best_seen_result,
            )
            if guard_blocked:
                return TerminationSnapshot(
                    mode=specs_obj.termination_mode.value,
                    out_node=out_node,
                    bit_weight=bit_weight,
                    ceiling=ceiling,
                    should_stop=False,
                    reason=None,
                    message_lines=(
                        '',
                        '[!] BEST-SEEN GUARD BLOCKED TRIVIAL TERMINATION!',
                        f'Current accepted area {current_area:.4f} is {guard_gap_pct:.2f}% above the run-best area {best_area:.4f}.',
                        f'Configured best-seen guard is {specs_obj.best_seen_guard_pct:.2f}%. Continuing exploration.',
                        '',
                    ),
                    zone_rank_requested=zone_rank_requested,
                    zone_rank_effective=zone_rank_effective,
                    zone_rank_applied=zone_rank_applied,
                    zone_level_count=zone_level_count,
                    best_seen_guard_blocked=True,
                    best_seen_guard_gap_pct=guard_gap_pct,
                    best_seen_stagnation=best_seen_stagnation,
                )
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
                zone_rank_requested=zone_rank_requested,
                zone_rank_effective=zone_rank_effective,
                zone_rank_applied=zone_rank_applied,
                zone_level_count=zone_level_count,
                best_seen_guard_blocked=False,
                best_seen_guard_gap_pct=guard_gap_pct,
                best_seen_stagnation=best_seen_stagnation,
            )
    else:
        ceiling = None

    return TerminationSnapshot(
        mode=specs_obj.termination_mode.value,
        out_node=out_node,
        bit_weight=bit_weight,
        ceiling=ceiling,
        should_stop=False,
        zone_rank_requested=zone_rank_requested,
        zone_rank_effective=zone_rank_effective,
        zone_rank_applied=zone_rank_applied,
        zone_level_count=zone_level_count,
        best_seen_guard_blocked=False,
        best_seen_guard_gap_pct=None,
        best_seen_stagnation=best_seen_stagnation,
    )


def _verification_limit(specs_obj: Specifications) -> int:
    """
    Returns the error bound that verification should compare against
    """
    if specs_obj.metric is MetricType.ABSOLUTE:
        return specs_obj.et
    return specs_obj.max_error


def _current_error_budget_snapshot(
    specs_obj: Specifications,
    current_result: Dict[str, Any] | None,
) -> Tuple[float, float | None, float | None, float | None]:
    verification_limit = float(_verification_limit(specs_obj))

    # At the first iteration the current benchmark is still exact, so the
    # consumed error is provably zero and the whole budget is still available.
    if current_result is None and specs_obj.current_benchmark == specs_obj.exact_benchmark:
        return (verification_limit, 0.0, 0.0, verification_limit)

    if current_result is None:
        return (verification_limit, None, None, None)

    exact_error_raw = current_result.get('verified_error_exact')
    prev_error_raw = current_result.get('verified_error_prev')

    exact_error = None
    if exact_error_raw is not None and float(exact_error_raw) >= 0:
        exact_error = float(exact_error_raw)

    prev_error = None
    if prev_error_raw is not None and float(prev_error_raw) >= 0:
        prev_error = float(prev_error_raw)

    available_error = None if exact_error is None else verification_limit - exact_error
    return (verification_limit, exact_error, prev_error, available_error)


def _format_optional_metric(value: float | None) -> str:
    if value is None:
        return 'n/a'
    if float(value).is_integer():
        return str(int(value))
    return f'{float(value):.6g}'


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


def _pareto_weights(specs_obj: Specifications) -> Tuple[float, float, float]:
    raw_weights = (
        max(0.0, float(specs_obj.pareto_area_weight)),
        max(0.0, float(specs_obj.pareto_power_weight)),
        max(0.0, float(specs_obj.pareto_delay_weight)),
    )
    total = sum(raw_weights)
    if total <= 0.0:
        return (1.0, 0.0, 0.0)
    return tuple(weight / total for weight in raw_weights)


def _pareto_regret(point: Dict[str, Any], incumbent: Dict[str, Any], weights: Tuple[float, float, float]) -> float:
    regret = 0.0
    for metric_name, weight in zip(('area', 'power', 'delay'), weights):
        incumbent_value = float(incumbent[metric_name])
        point_value = float(point[metric_name])
        baseline = max(incumbent_value, 1e-9)
        regret += weight * max(0.0, (point_value / baseline) - 1.0)
    return regret


def _effective_pareto_forgiveness(specs_obj: Specifications, best_seen_stagnation: int) -> float:
    aggressive_stagnation = max(
        0,
        int(best_seen_stagnation) - int(specs_obj.pareto_aggressive_after_stagnation),
    )
    return max(
        float(specs_obj.pareto_min_forgiveness),
        float(specs_obj.pareto_forgiveness) * (
            float(specs_obj.pareto_forgiveness_decay) ** aggressive_stagnation
        ),
    )


def _classify_pareto_point(
    frontier: List[Dict[str, Any]],
    point: Dict[str, Any],
    specs_obj: Specifications,
    best_seen_stagnation: int,
) -> Tuple[str, bool, float]:
    if not frontier:
        frontier.append(point)
        return ('frontier_expanding', True, 0.0)

    weights = _pareto_weights(specs_obj)
    effective_forgiveness = _effective_pareto_forgiveness(specs_obj, best_seen_stagnation)
    min_regret = min(_pareto_regret(point, existing, weights) for existing in frontier)
    if any(
        all(float(existing[metric_name]) == float(point[metric_name]) for metric_name in ('area', 'power', 'delay'))
        for existing in frontier
    ):
        return ('near_frontier', False, min_regret)
    is_exactly_dominated = any(_dominates_pareto(existing, point) for existing in frontier)
    if is_exactly_dominated:
        if min_regret <= effective_forgiveness:
            return ('near_frontier', False, min_regret)
        return ('dominated', False, min_regret)

    frontier[:] = [existing for existing in frontier if not _dominates_pareto(point, existing)]
    frontier.append(point)
    return ('frontier_expanding', True, min_regret)


def _update_pareto_annealed_score(
    current_score: float,
    classification: str,
    regret: float,
    specs_obj: Specifications,
    best_seen_stagnation: int,
) -> float:
    if classification == 'frontier_expanding':
        return max(0.0, current_score - 1.5)
    if classification == 'near_frontier':
        return current_score + float(specs_obj.pareto_near_frontier_penalty)
    effective_forgiveness = _effective_pareto_forgiveness(specs_obj, best_seen_stagnation)
    excess_regret = max(0.0, regret - effective_forgiveness)
    return (
        current_score
        + float(specs_obj.pareto_dominated_penalty)
        + (float(specs_obj.pareto_regret_scale) * excess_regret)
    )


def _pareto_annealed_temperature(
    specs_obj: Specifications,
    iteration: int,
    best_seen_stagnation: int,
    runtime_seconds: float,
) -> float:
    base_temperature = float(specs_obj.pareto_temperature_init) * (
        float(specs_obj.pareto_temperature_decay) ** max(0, int(iteration) - 1)
    )
    timeout = max(float(specs_obj.timeout), 1.0)
    runtime_ratio = max(0.0, float(runtime_seconds)) / timeout
    aggressive_stagnation = max(
        0,
        int(best_seen_stagnation) - int(specs_obj.pareto_aggressive_after_stagnation),
    )
    pressure = 1.0 + (
        float(specs_obj.pareto_runtime_pressure_scale)
        * runtime_ratio
        * aggressive_stagnation
    )
    return max(1e-6, base_temperature / pressure)


def _pareto_stop_probability(score: float, threshold: float, temperature: float) -> float:
    if temperature <= 1e-9:
        return 1.0 if score > threshold else 0.0
    scaled_margin = (score - threshold) / temperature
    scaled_margin = max(-60.0, min(60.0, scaled_margin))
    return 1.0 / (1.0 + math.exp(-scaled_margin))


def _pareto_candidate_stop_probability(
    candidate_streak: int,
    patience: int,
    step_stop_probability: float,
) -> float:
    effective_patience = max(1, int(patience))
    if int(candidate_streak) < effective_patience:
        return 0.0

    effective_step_probability = min(1.0, max(0.0, float(step_stop_probability)))
    eligible_steps = int(candidate_streak) - effective_patience + 1
    return 1.0 - ((1.0 - effective_step_probability) ** eligible_steps)


def _apply_pareto_candidate_termination(
    specs_obj: Specifications,
    *,
    selected_result_this_iteration: bool,
    iteration_status: str | None,
    pareto_stagnation: int,
    pareto_stagnation_score: float,
    persistance_limit: int,
    iteration: int,
    runtime_seconds: float,
    best_seen_stagnation: int,
    current_result: Dict[str, Any] | None,
    best_seen_result: Dict[str, Any] | None,
    trace_row: Dict[str, Any],
    pareto_rng: random.Random,
) -> Tuple[int, float, str | None, Tuple[str, ...] | None]:
    if specs_obj.termination_mode not in {
        TerminationMode.PARETO,
        TerminationMode.PARETO_ANNEALED,
        TerminationMode.HYBRID,
    }:
        return (pareto_stagnation, pareto_stagnation_score, None, None)

    trace_row['pareto_frontier_size'] = 0
    if selected_result_this_iteration:
        pareto_stagnation = 0
        pareto_stagnation_score = 0.0
        trace_row['pareto_efficient'] = True
        trace_row['pareto_classification'] = 'sat_candidate'
        trace_row['pareto_regret'] = 0.0
        trace_row['pareto_stagnation'] = pareto_stagnation
        trace_row['pareto_stagnation_score'] = pareto_stagnation_score
        return (pareto_stagnation, pareto_stagnation_score, None, None)

    pareto_stagnation += 1
    pareto_stagnation_score = float(pareto_stagnation)
    status_suffix = 'candidate' if iteration_status in (None, '') else str(iteration_status).lower()
    trace_row['pareto_efficient'] = False
    trace_row['pareto_classification'] = f'no_sat_{status_suffix}'
    trace_row['pareto_regret'] = None
    trace_row['pareto_stagnation'] = pareto_stagnation
    trace_row['pareto_stagnation_score'] = pareto_stagnation_score

    candidate_patience = max(int(specs_obj.pareto_candidate_patience), int(persistance_limit))
    temperature = None
    if specs_obj.termination_mode in {TerminationMode.PARETO, TerminationMode.HYBRID}:
        if pareto_stagnation < candidate_patience:
            trace_row['pareto_stop_probability'] = 0.0
            return (pareto_stagnation, pareto_stagnation_score, None, None)
        stop_probability = 1.0
    else:
        stop_probability = _pareto_candidate_stop_probability(
            pareto_stagnation,
            candidate_patience,
            specs_obj.pareto_candidate_step_stop_probability,
        )
        if stop_probability > 0.0:
            temperature = _pareto_annealed_temperature(
                specs_obj,
                iteration,
                best_seen_stagnation,
                runtime_seconds,
            )
            annealed_probability = _pareto_stop_probability(
                pareto_stagnation_score,
                float(candidate_patience) - 0.5,
                temperature,
            )
            stop_probability = max(stop_probability, annealed_probability)
            trace_row['pareto_temperature'] = temperature

    trace_row['pareto_stop_probability'] = stop_probability
    if stop_probability <= 0.0:
        return (pareto_stagnation, pareto_stagnation_score, None, None)

    random_draw = pareto_rng.random()
    trace_row['pareto_random_draw'] = random_draw

    guard_blocked, guard_gap_pct, current_area, best_area = _check_best_seen_guard(
        specs_obj,
        current_result=current_result,
        best_seen_result=best_seen_result,
    )
    trace_row['best_seen_guard_blocked'] = guard_blocked
    trace_row['best_seen_guard_gap_pct'] = guard_gap_pct
    if guard_blocked:
        return (
            pareto_stagnation,
            pareto_stagnation_score,
            None,
            (
                'Best-seen guard blocked pareto candidate termination: '
                f'current accepted area {current_area:.4f} is {guard_gap_pct:.2f}% '
                f'above run-best area {best_area:.4f}.',
            ),
        )

    if specs_obj.termination_mode is TerminationMode.PARETO_ANNEALED:
        if random_draw >= stop_probability:
            return (pareto_stagnation, pareto_stagnation_score, None, None)

        reason = 'pareto_annealed_termination'
        reason_lines = (
            'Pareto-annealed termination fired:',
            f'no accepted SAT candidate streak = {pareto_stagnation}',
            f'candidate patience = {candidate_patience}',
            f'temperature = {temperature:.3f}' if temperature is not None else 'temperature = n/a',
            f'stop probability = {stop_probability:.3f}',
            f'draw = {random_draw:.3f}',
        )
        return (pareto_stagnation, pareto_stagnation_score, reason, reason_lines)

    reason = 'pareto_termination'
    reason_lines = (
        'Pareto termination fired:',
        f'no accepted SAT candidate streak = {pareto_stagnation}',
        f'candidate patience = {candidate_patience}',
        'stop probability = 1.000',
        f'draw = {random_draw:.3f}',
    )
    return (pareto_stagnation, pareto_stagnation_score, reason, reason_lines)


def _sentinel_should_stop(
    specs_obj: Specifications,
    *,
    best_seen_stagnation: int,
    best_seen_iteration_age: int,
    best_seen_improvement_pct: float | None,
    same_subgraph_streak: int,
    structural_stall_streak: int,
    negative_ratio: float | None,
    timeout_count: int,
    runtime_seconds: float,
    current_result: Dict[str, Any] | None,
    best_seen_result: Dict[str, Any] | None,
) -> Tuple[bool, float | None, float | None, float | None, Tuple[str, ...] | None]:
    if int(specs_obj.beta or 0) < int(specs_obj.sentinel_min_beta):
        return (False, None, None, None, None)
    if best_seen_stagnation < int(specs_obj.sentinel_best_seen_patience):
        return (False, None, None, None, None)
    if best_seen_iteration_age < int(specs_obj.sentinel_best_seen_iteration_patience):
        return (False, None, None, None, None)

    gain_is_marginal = (
        best_seen_improvement_pct is None
        or best_seen_improvement_pct < float(specs_obj.sentinel_marginal_gain_pct)
    )
    repeated_subgraph_tail = same_subgraph_streak >= int(specs_obj.sentinel_same_subgraph_streak)
    structurally_stalled = (
        repeated_subgraph_tail
        or structural_stall_streak >= int(specs_obj.sentinel_structural_stall_streak)
    )
    if not (gain_is_marginal and structurally_stalled):
        return (False, None, None, None, None)

    runtime_fraction = float(runtime_seconds) / max(float(specs_obj.timeout), 1.0)
    timeout_tail = timeout_count >= int(specs_obj.sentinel_min_timeout_count)
    negative_tail = (
        negative_ratio is not None
        and negative_ratio >= float(specs_obj.sentinel_negative_cell_ratio)
        and runtime_fraction >= float(specs_obj.sentinel_min_runtime_fraction)
    )
    if negative_ratio is not None and negative_ratio < float(specs_obj.sentinel_negative_cell_ratio) and not repeated_subgraph_tail:
        return (False, None, None, None, None)
    if not (repeated_subgraph_tail or timeout_tail or negative_tail):
        return (False, None, None, None, None)

    guard_blocked, guard_gap_pct, current_area, best_area = _check_best_seen_guard(
        specs_obj,
        current_result=current_result,
        best_seen_result=best_seen_result,
    )
    if guard_blocked:
        return (
            False,
            guard_gap_pct,
            current_area,
            best_area,
            (
                'Best-seen guard blocked sentinel termination: '
                f'current accepted area {current_area:.4f} is {guard_gap_pct:.2f}% '
                f'above run-best area {best_area:.4f}.',
            ),
        )

    reason_lines = (
        'Sentinel termination fired:',
        f'best-seen stagnation = {best_seen_stagnation}',
        f'iterations since best-seen improved = {best_seen_iteration_age}',
        f'same-subgraph streak = {same_subgraph_streak}',
        f'structural-stall streak = {structural_stall_streak}',
        f'negative-cell ratio = {negative_ratio:.3f}' if negative_ratio is not None else 'negative-cell ratio = n/a',
        f'timeout count this iteration = {timeout_count}',
        f'elapsed runtime fraction = {runtime_fraction:.3f}',
        f'best-seen improvement this iteration = {best_seen_improvement_pct:.3f}%'
        if best_seen_improvement_pct is not None else
        'best-seen improvement this iteration = none',
    )
    return (True, guard_gap_pct, current_area, best_area, reason_lines)


_PREDICTOR_MODEL_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_predictor_model(model_path: str) -> Dict[str, Any]:
    resolved = str(Path(model_path).expanduser().resolve())
    cached = _PREDICTOR_MODEL_CACHE.get(resolved)
    if cached is not None:
        return cached
    with open(resolved) as model_file:
        model = json.load(model_file)
    _PREDICTOR_MODEL_CACHE[resolved] = model
    return model


def _predictor_feature_vector(
    specs_obj: Specifications,
    *,
    iteration: int,
    out_node: int | None,
    bit_weight: float | None,
    termination_ceiling: float | None,
    best_seen_stagnation: int,
    best_seen_iteration_age: int,
    same_subgraph_streak: int,
    structural_stall_streak: int,
    negative_ratio: float | None,
    timeout_count: int,
    runtime_seconds: float,
    best_seen_improvement_pct: float | None,
) -> Dict[str, float]:
    runtime_fraction = float(runtime_seconds) / max(float(specs_obj.timeout), 1.0)
    ceiling = float(termination_ceiling) if termination_ceiling not in (None, '') else 0.0
    weight = float(bit_weight) if bit_weight not in (None, '') else 0.0
    return {
        'iteration': float(iteration),
        'out_node': float(out_node or 0),
        'beta': float(specs_obj.beta or 0),
        'max_error': float(specs_obj.max_error or 0),
        'best_seen_stagnation': float(best_seen_stagnation),
        'best_seen_iteration_age': float(best_seen_iteration_age),
        'same_subgraph_streak': float(same_subgraph_streak),
        'structural_stall_streak': float(structural_stall_streak),
        'negative_ratio': 0.0 if negative_ratio in (None, '') else float(negative_ratio),
        'timeout_count': float(timeout_count),
        'runtime_fraction': float(runtime_fraction),
        'best_seen_improvement_pct': 0.0 if best_seen_improvement_pct in (None, '') else float(best_seen_improvement_pct),
        'bit_weight_over_ceiling': (weight / max(ceiling, 1e-9)) if ceiling > 0 else 0.0,
    }


def _predictor_stop_probability(model: Dict[str, Any], feature_values: Dict[str, float]) -> float:
    feature_order = model['feature_names']
    means = model['feature_means']
    stds = model['feature_stds']
    weights = model['weights']
    bias = float(model['bias'])
    score = bias
    for idx, feature_name in enumerate(feature_order):
        raw_value = float(feature_values.get(feature_name, 0.0))
        normalized = (raw_value - float(means[idx])) / max(float(stds[idx]), 1e-9)
        score += float(weights[idx]) * normalized
    score = max(-60.0, min(60.0, score))
    return 1.0 / (1.0 + math.exp(-score))


def _predictor_should_stop(
    specs_obj: Specifications,
    *,
    iteration: int,
    out_node: int | None,
    bit_weight: float | None,
    termination_ceiling: float | None,
    best_seen_stagnation: int,
    best_seen_iteration_age: int,
    same_subgraph_streak: int,
    structural_stall_streak: int,
    negative_ratio: float | None,
    timeout_count: int,
    runtime_seconds: float,
    best_seen_improvement_pct: float | None,
    current_result: Dict[str, Any] | None,
    best_seen_result: Dict[str, Any] | None,
) -> Tuple[bool, float, float | None, float | None, float | None, Tuple[str, ...] | None]:
    if iteration < int(specs_obj.predictor_min_iteration):
        return (False, 0.0, None, None, None, None)

    model = _load_predictor_model(specs_obj.predictor_model_path)
    feature_values = _predictor_feature_vector(
        specs_obj,
        iteration=iteration,
        out_node=out_node,
        bit_weight=bit_weight,
        termination_ceiling=termination_ceiling,
        best_seen_stagnation=best_seen_stagnation,
        best_seen_iteration_age=best_seen_iteration_age,
        same_subgraph_streak=same_subgraph_streak,
        structural_stall_streak=structural_stall_streak,
        negative_ratio=negative_ratio,
        timeout_count=timeout_count,
        runtime_seconds=runtime_seconds,
        best_seen_improvement_pct=best_seen_improvement_pct,
    )
    stop_probability = _predictor_stop_probability(model, feature_values)
    if stop_probability < float(specs_obj.predictor_probability_threshold):
        return (False, stop_probability, None, None, None, None)

    guard_blocked, guard_gap_pct, current_area, best_area = _check_best_seen_guard(
        specs_obj,
        current_result=current_result,
        best_seen_result=best_seen_result,
    )
    if guard_blocked:
        return (
            False,
            stop_probability,
            guard_gap_pct,
            current_area,
            best_area,
            (
                'Best-seen guard blocked predictor termination: '
                f'current accepted area {current_area:.4f} is {guard_gap_pct:.2f}% '
                f'above run-best area {best_area:.4f}.',
            ),
        )

    reason_lines = (
        'Predictor termination fired:',
        f'predicted stop probability = {stop_probability:.3f}',
        f'best-seen stagnation = {best_seen_stagnation}',
        f'iterations since best-seen improved = {best_seen_iteration_age}',
        f'structural-stall streak = {structural_stall_streak}',
        f'same-subgraph streak = {same_subgraph_streak}',
        f'negative-cell ratio = {negative_ratio:.3f}' if negative_ratio is not None else 'negative-cell ratio = n/a',
        f'timeout count this iteration = {timeout_count}',
    )
    return (True, stop_probability, guard_gap_pct, current_area, best_area, reason_lines)


def _is_better_run_result(candidate: Dict[str, Any], incumbent: Dict[str, Any] | None) -> bool:
    if incumbent is None:
        return True

    candidate_area = candidate.get('area')
    incumbent_area = incumbent.get('area')
    if candidate_area != incumbent_area:
        return candidate_area < incumbent_area

    candidate_delay = candidate.get('delay')
    incumbent_delay = incumbent.get('delay')
    if candidate_delay != incumbent_delay:
        return candidate_delay < incumbent_delay

    candidate_power = candidate.get('power')
    incumbent_power = incumbent.get('power')
    if candidate_power != incumbent_power:
        return candidate_power < incumbent_power

    candidate_iteration = candidate.get('iteration')
    incumbent_iteration = incumbent.get('iteration')
    if candidate_iteration != incumbent_iteration:
        return candidate_iteration < incumbent_iteration

    return False


def _write_termination_trace(summary_stem: str, trace_rows: List[Dict[str, Any]]) -> str:
    # the csv trace stores one row per outer exploration iteration so sweeps can
    # be analyzed without reparsing the verbose console log.
    folder = f"{sxpatpaths.OUTPUT_PATH['report'][0]}/termination_study"
    FS.mkdir(folder)
    trace_path = f'{folder}/{summary_stem}_trace.csv'
    fieldnames = [
        'iteration',
        'runtime_elapsed_seconds',
        'iteration_runtime_seconds',
        'termination_mode',
        'termination_zone_rank_from_max',
        'termination_zone_rank_effective',
        'termination_zone_rank_applied',
        'termination_zone_level_count',
        'stop_reason',
        'out_node',
        'bit_weight',
        'termination_ceiling',
        'best_seen_guard_pct',
        'best_seen_guard_blocked',
        'best_seen_guard_gap_pct',
        'et',
        'benchmark',
        'selected_cell',
        'status',
        'best_area',
        'best_power',
        'best_delay',
        'selected_runtime_at_accept_seconds',
        'verified_error_exact',
        'verified_error_prev',
        'run_best_area',
        'run_best_iteration',
        'run_best_runtime_at_accept_seconds',
        'best_seen_iteration_age',
        'best_seen_improved',
        'best_seen_stagnation',
        'best_seen_improvement_pct',
        'subgraph_available',
        'subgraph_repeated',
        'labeling_time_seconds',
        'subgraph_extraction_time_seconds',
        'same_subgraph_streak',
        'structural_stall_streak',
        'grid_sat_count',
        'grid_unsat_count',
        'grid_unknown_count',
        'grid_dominated_count',
        'grid_timeout_count',
        'grid_negative_ratio',
        'pareto_efficient',
        'pareto_classification',
        'pareto_regret',
        'pareto_frontier_size',
        'pareto_stagnation',
        'pareto_stagnation_score',
        'pareto_temperature',
        'pareto_stop_probability',
        'pareto_random_draw',
        'predictor_stop_probability',
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
    pareto_stagnation_score = 0.0
    best_seen_stagnation = 0
    same_subgraph_streak = 0
    structural_stall_streak = 0
    pareto_rng = random.Random(specs_obj.pareto_rng_seed)

    run_started_at = time.time()
    trace_rows: List[Dict[str, Any]] = []
    last_selected_result: Dict[str, Any] | None = None
    best_seen_result: Dict[str, Any] | None = None
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
        iteration_started_at = time.time()
        status = None
        best_data = None
        best_name = None
        selected_result_this_iteration = False

        def commit_trace_row() -> None:
            trace_row['runtime_elapsed_seconds'] = round(time.time() - run_started_at, 6)
            trace_row['iteration_runtime_seconds'] = round(time.time() - iteration_started_at, 6)
            trace_row['selected_runtime_at_accept_seconds'] = (
                None
                if last_selected_result is None or int(last_selected_result['iteration']) != specs_obj.iteration
                else last_selected_result['runtime_at_accept_seconds']
            )
            trace_row['run_best_runtime_at_accept_seconds'] = (
                None if best_seen_result is None else best_seen_result['runtime_at_accept_seconds']
            )
            trace_row['labeling_time_seconds'] = None if labeling_time < 0 else labeling_time
            trace_row['subgraph_extraction_time_seconds'] = (
                None if subgraph_extraction_time < 0 else subgraph_extraction_time
            )
            _store_trace_row(trace_rows, **trace_row)

        # Record one trace row per outer iteration, even if we later discover
        # there was no usable subgraph or no SAT model in the selected cell.
        trace_row: Dict[str, Any] = {
            'iteration': specs_obj.iteration,
            'runtime_elapsed_seconds': None,
            'iteration_runtime_seconds': None,
            'termination_mode': specs_obj.termination_mode.value,
            'termination_zone_rank_from_max': (
                specs_obj.termination_zone_rank_from_max
                if specs_obj.cnn_constraint is CnnErrorConstraintTypes.ZONE_AET
                else None
            ),
            'termination_zone_rank_effective': None,
            'termination_zone_rank_applied': None,
            'termination_zone_level_count': None,
            'stop_reason': None,
            'out_node': specs_obj.out_node if specs_obj.extraction_mode == 0 else None,
            'bit_weight': None,
            'termination_ceiling': None,
            'best_seen_guard_pct': specs_obj.best_seen_guard_pct,
            'best_seen_guard_blocked': False,
            'best_seen_guard_gap_pct': None,
            'et': specs_obj.et,
            'verification_limit': None,
            'current_verified_error_exact': None,
            'current_verified_error_prev': None,
            'current_available_error': None,
            'benchmark': specs_obj.current_benchmark,
            'selected_cell': None,
            'status': None,
            'best_area': None,
            'best_power': None,
            'best_delay': None,
            'selected_runtime_at_accept_seconds': None,
            'verified_error_exact': None,
            'verified_error_prev': None,
            'run_best_area': None if best_seen_result is None else best_seen_result['area'],
            'run_best_iteration': None if best_seen_result is None else best_seen_result['iteration'],
            'run_best_runtime_at_accept_seconds': (
                None if best_seen_result is None else best_seen_result['runtime_at_accept_seconds']
            ),
            'best_seen_iteration_age': None if best_seen_result is None else specs_obj.iteration - int(best_seen_result['iteration']),
            'best_seen_improved': None,
            'best_seen_stagnation': best_seen_stagnation,
            'subgraph_available': None,
            'subgraph_repeated': False,
            'labeling_time_seconds': None,
            'subgraph_extraction_time_seconds': None,
            'same_subgraph_streak': same_subgraph_streak,
            'structural_stall_streak': structural_stall_streak,
            'grid_sat_count': 0,
            'grid_unsat_count': 0,
            'grid_unknown_count': 0,
            'grid_dominated_count': 0,
            'grid_timeout_count': 0,
            'grid_negative_ratio': None,
            'best_seen_improvement_pct': None,
            'pareto_efficient': None,
            'pareto_classification': None,
            'pareto_regret': None,
            'pareto_frontier_size': len(pareto_frontier),
            'pareto_stagnation': pareto_stagnation,
            'pareto_stagnation_score': pareto_stagnation_score,
            'pareto_temperature': None,
            'pareto_stop_probability': None,
            'pareto_random_draw': None,
            'predictor_stop_probability': None,
        }

        if not specs_obj.subxpat:
            if prev_actual_error == 0:
                stop_reason = 'no_progress'
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                commit_trace_row()
                break
            specs_obj.et = specs_obj.max_error
        elif specs_obj.extraction_mode == 0:
            print(f"Current out_node: {specs_obj.out_node}")
            # termination logic
            snapshot = _check_termination(
                specs_obj,
                max_out_node,
                current_result=last_selected_result,
                best_seen_result=best_seen_result,
                best_seen_stagnation=best_seen_stagnation,
            )
            trace_row['out_node'] = snapshot.out_node
            trace_row['bit_weight'] = snapshot.bit_weight
            trace_row['termination_ceiling'] = snapshot.ceiling
            trace_row['termination_zone_rank_effective'] = snapshot.zone_rank_effective
            trace_row['termination_zone_rank_applied'] = snapshot.zone_rank_applied
            trace_row['termination_zone_level_count'] = snapshot.zone_level_count
            trace_row['best_seen_guard_blocked'] = snapshot.best_seen_guard_blocked
            trace_row['best_seen_guard_gap_pct'] = snapshot.best_seen_guard_gap_pct
            trace_row['best_seen_stagnation'] = snapshot.best_seen_stagnation
            if snapshot.should_stop:
                stop_snapshot = snapshot
                stop_reason = snapshot.reason
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                if snapshot.reason == 'error_space_exhausted':
                    pprint.warning(snapshot.message_lines[0])
                else:
                    print('\n'.join(snapshot.message_lines))
                commit_trace_row()
                break
            if snapshot.best_seen_guard_blocked:
                print('\n'.join(snapshot.message_lines))
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
                    commit_trace_row()
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
        (
            current_verification_limit,
            current_verified_error_exact,
            current_verified_error_prev,
            current_available_error,
        ) = _current_error_budget_snapshot(specs_obj, last_selected_result)
        trace_row['verification_limit'] = current_verification_limit
        trace_row['current_verified_error_exact'] = current_verified_error_exact
        trace_row['current_verified_error_prev'] = current_verified_error_prev
        trace_row['current_available_error'] = current_available_error

        if (specs_obj.et > specs_obj.max_error and specs_obj.metric != MetricType.RELATIVE) or specs_obj.et <= 0:
            stop_reason = 'invalid_et'
            trace_row['stop_reason'] = stop_reason
            trace_row['status'] = 'STOPPED'
            commit_trace_row()
            break

        pprint.info1(
            f'iteration {specs_obj.iteration} with et {specs_obj.et}, '
            f'configured error bound {_format_optional_metric(current_verification_limit)}, '
            f'current exact error {_format_optional_metric(current_verified_error_exact)}, '
            f'actual available error {_format_optional_metric(current_available_error)}'
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
            structural_stall_streak += 1
            same_subgraph_streak = 0
            trace_row['status'] = 'NO_SUBGRAPH'
            trace_row['same_subgraph_streak'] = same_subgraph_streak
            trace_row['structural_stall_streak'] = structural_stall_streak
            pareto_reason_lines: Tuple[str, ...] | None = None
            pareto_stagnation, pareto_stagnation_score, pareto_stop_reason, pareto_reason_lines = _apply_pareto_candidate_termination(
                specs_obj,
                selected_result_this_iteration=False,
                iteration_status=trace_row['status'],
                pareto_stagnation=pareto_stagnation,
                pareto_stagnation_score=pareto_stagnation_score,
                persistance_limit=persistance_limit,
                iteration=specs_obj.iteration,
                runtime_seconds=time.time() - run_started_at,
                best_seen_stagnation=best_seen_stagnation,
                current_result=last_selected_result,
                best_seen_result=best_seen_result,
                trace_row=trace_row,
                pareto_rng=pareto_rng,
            )
            if trace_row['best_seen_guard_blocked'] and pareto_reason_lines is not None:
                pprint.warning('\n'.join(pareto_reason_lines))
            elif pareto_stop_reason is not None:
                stop_reason = pareto_stop_reason
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                pprint.warning('\n'.join(pareto_reason_lines or ('Pareto candidate termination fired.',)))
                commit_trace_row()
                break
            commit_trace_row()
            prev_actual_error = 0
            continue

        if (
            len(previous_subgraphs) >= 2
            and nx.is_isomorphic(previous_subgraphs[-2], previous_subgraphs[-1], node_match=node_matcher)
        ):
            pprint.warning('The subgraph is equal to the previous one. Skipping iteration ...')
            same_subgraph_streak += 1
            structural_stall_streak += 1
            trace_row['status'] = 'DUPLICATE_SUBGRAPH'
            trace_row['subgraph_repeated'] = True
            trace_row['same_subgraph_streak'] = same_subgraph_streak
            trace_row['structural_stall_streak'] = structural_stall_streak
            if specs_obj.termination_mode is TerminationMode.SENTINEL:
                should_stop, guard_gap_pct, current_area, best_area, reason_lines = _sentinel_should_stop(
                    specs_obj,
                    best_seen_stagnation=best_seen_stagnation,
                    best_seen_iteration_age=(
                        0 if best_seen_result is None else specs_obj.iteration - int(best_seen_result['iteration'])
                    ),
                    best_seen_improvement_pct=None,
                    same_subgraph_streak=same_subgraph_streak,
                    structural_stall_streak=structural_stall_streak,
                    negative_ratio=None,
                    timeout_count=0,
                    runtime_seconds=time.time() - run_started_at,
                    current_result=last_selected_result,
                    best_seen_result=best_seen_result,
                )
                trace_row['best_seen_guard_gap_pct'] = guard_gap_pct
                if should_stop:
                    stop_reason = 'sentinel_termination'
                    trace_row['stop_reason'] = stop_reason
                    trace_row['status'] = 'STOPPED'
                    pprint.warning('\n'.join(reason_lines or ('Sentinel termination fired.',)))
                    commit_trace_row()
                    break
            pareto_reason_lines: Tuple[str, ...] | None = None
            pareto_stagnation, pareto_stagnation_score, pareto_stop_reason, pareto_reason_lines = _apply_pareto_candidate_termination(
                specs_obj,
                selected_result_this_iteration=False,
                iteration_status=trace_row['status'],
                pareto_stagnation=pareto_stagnation,
                pareto_stagnation_score=pareto_stagnation_score,
                persistance_limit=persistance_limit,
                iteration=specs_obj.iteration,
                runtime_seconds=time.time() - run_started_at,
                best_seen_stagnation=best_seen_stagnation,
                current_result=last_selected_result,
                best_seen_result=best_seen_result,
                trace_row=trace_row,
                pareto_rng=pareto_rng,
            )
            if trace_row['best_seen_guard_blocked'] and pareto_reason_lines is not None:
                pprint.warning('\n'.join(pareto_reason_lines))
            elif pareto_stop_reason is not None:
                stop_reason = pareto_stop_reason
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                pprint.warning('\n'.join(pareto_reason_lines or ('Pareto candidate termination fired.',)))
                commit_trace_row()
                break
            commit_trace_row()
            prev_actual_error = 0
            continue
        same_subgraph_streak = 0

        # explore the grid
        pprint.info2(f'Grid ({specs_obj.grid_param_1} X {specs_obj.grid_param_2}) and et={specs_obj.et} exploration started...')
        dominant_cells = []
        exact_stats = MetricsEstimator.estimate_metrics(exact_file_path)
        grid_sat_count = 0
        grid_unsat_count = 0
        grid_unknown_count = 0
        grid_dominated_count = 0
        grid_timeout_count = 0

        for lpp, ppo in CellIterator.factory(specs_obj):
            if is_dominated((lpp, ppo), dominant_cells):
                pprint.info1(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> DOMINATED')
                grid_dominated_count += 1
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
                    if solve_timer.total >= max(0.0, float(specs_obj.timeout) - 1.0):
                        grid_timeout_count += 1
                    grid_unknown_count += 1
                    # store cell as dominant (to skip dominated subgrid)
                    dominant_cells.append((lpp, ppo))
                elif status == UNSAT:
                    grid_unsat_count += 1

            else:
                pprint.success(f'Cell({lpp},{ppo}) at iteration {specs_obj.iteration} -> {status.upper()} ({len(models)} models found)')
                grid_sat_count += 1

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
                    'iteration': specs_obj.iteration,
                    'runtime_at_accept_seconds': round(time.time() - run_started_at, 6),
                }
                previous_best_seen_result = None if best_seen_result is None else dict(best_seen_result)
                best_seen_improved = _is_better_run_result(last_selected_result, best_seen_result)
                if best_seen_improved:
                    best_seen_result = dict(last_selected_result)
                    best_seen_stagnation = 0
                else:
                    best_seen_stagnation += 1
                if best_seen_improved and previous_best_seen_result is not None and previous_best_seen_result.get('area'):
                    previous_best_area = float(previous_best_seen_result['area'])
                    best_seen_improvement_pct = (
                        ((previous_best_area - float(best_seen_result['area'])) / previous_best_area) * 100.0
                        if previous_best_area > 0 else None
                    )
                elif best_seen_improved:
                    best_seen_improvement_pct = None
                else:
                    best_seen_improvement_pct = 0.0
                trace_row['best_seen_improved'] = best_seen_improved
                trace_row['best_seen_stagnation'] = best_seen_stagnation
                trace_row['best_seen_improvement_pct'] = best_seen_improvement_pct
                trace_row['best_seen_iteration_age'] = specs_obj.iteration - int(best_seen_result['iteration'])
                selected_result_this_iteration = True

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

        trace_row['grid_sat_count'] = grid_sat_count
        trace_row['grid_unsat_count'] = grid_unsat_count
        trace_row['grid_unknown_count'] = grid_unknown_count
        trace_row['grid_dominated_count'] = grid_dominated_count
        trace_row['grid_timeout_count'] = grid_timeout_count
        negative_cell_count = grid_unsat_count + grid_unknown_count + grid_dominated_count
        considered_cell_count = grid_sat_count + negative_cell_count
        negative_ratio = (
            negative_cell_count / considered_cell_count
            if considered_cell_count > 0 else None
        )
        trace_row['grid_negative_ratio'] = negative_ratio

        if selected_result_this_iteration:
            iteration_structurally_stalled = (
                trace_row['best_seen_improved'] is False
                and (
                    (negative_ratio is not None and negative_ratio >= float(specs_obj.sentinel_negative_cell_ratio))
                    or grid_timeout_count > 0
                )
            )
            structural_stall_streak = structural_stall_streak + 1 if iteration_structurally_stalled else 0
        elif trace_row['status'] not in {'DUPLICATE_SUBGRAPH', 'NO_SUBGRAPH'}:
            structural_stall_streak = 0
        trace_row['same_subgraph_streak'] = same_subgraph_streak
        trace_row['structural_stall_streak'] = structural_stall_streak

        pareto_reason_lines: Tuple[str, ...] | None = None
        pareto_stagnation, pareto_stagnation_score, pareto_stop_reason, pareto_reason_lines = _apply_pareto_candidate_termination(
            specs_obj,
            selected_result_this_iteration=selected_result_this_iteration,
            iteration_status=trace_row['status'],
            pareto_stagnation=pareto_stagnation,
            pareto_stagnation_score=pareto_stagnation_score,
            persistance_limit=persistance_limit,
            iteration=specs_obj.iteration,
            runtime_seconds=time.time() - run_started_at,
            best_seen_stagnation=best_seen_stagnation,
            current_result=last_selected_result,
            best_seen_result=best_seen_result,
            trace_row=trace_row,
            pareto_rng=pareto_rng,
        )
        if trace_row['best_seen_guard_blocked'] and pareto_reason_lines is not None:
            pprint.warning('\n'.join(pareto_reason_lines))
        elif pareto_stop_reason is not None:
            stop_reason = pareto_stop_reason
            trace_row['stop_reason'] = stop_reason
            trace_row['status'] = 'STOPPED'
            pprint.warning('\n'.join(pareto_reason_lines or ('Pareto candidate termination fired.',)))
            commit_trace_row()
            break

        if (
            specs_obj.termination_mode is TerminationMode.SENTINEL
            and selected_result_this_iteration
        ):
            should_stop, guard_gap_pct, current_area, best_area, reason_lines = _sentinel_should_stop(
                specs_obj,
                best_seen_stagnation=best_seen_stagnation,
                best_seen_iteration_age=(
                    0 if best_seen_result is None else specs_obj.iteration - int(best_seen_result['iteration'])
                ),
                best_seen_improvement_pct=trace_row['best_seen_improvement_pct'],
                same_subgraph_streak=same_subgraph_streak,
                structural_stall_streak=structural_stall_streak,
                negative_ratio=negative_ratio,
                timeout_count=grid_timeout_count,
                runtime_seconds=time.time() - run_started_at,
                current_result=last_selected_result,
                best_seen_result=best_seen_result,
            )
            trace_row['best_seen_guard_gap_pct'] = guard_gap_pct
            if should_stop:
                stop_reason = 'sentinel_termination'
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                pprint.warning('\n'.join(reason_lines or ('Sentinel termination fired.',)))
                commit_trace_row()
                break

        if (
            specs_obj.termination_mode is TerminationMode.PREDICTOR
            and selected_result_this_iteration
        ):
            should_stop, stop_probability, guard_gap_pct, current_area, best_area, reason_lines = _predictor_should_stop(
                specs_obj,
                iteration=specs_obj.iteration,
                out_node=trace_row['out_node'],
                bit_weight=trace_row['bit_weight'],
                termination_ceiling=trace_row['termination_ceiling'],
                best_seen_stagnation=best_seen_stagnation,
                best_seen_iteration_age=(
                    0 if best_seen_result is None else specs_obj.iteration - int(best_seen_result['iteration'])
                ),
                same_subgraph_streak=same_subgraph_streak,
                structural_stall_streak=structural_stall_streak,
                negative_ratio=negative_ratio,
                timeout_count=grid_timeout_count,
                runtime_seconds=time.time() - run_started_at,
                best_seen_improvement_pct=trace_row['best_seen_improvement_pct'],
                current_result=last_selected_result,
                best_seen_result=best_seen_result,
            )
            trace_row['predictor_stop_probability'] = stop_probability
            trace_row['best_seen_guard_gap_pct'] = guard_gap_pct
            if should_stop:
                stop_reason = 'predictor_termination'
                trace_row['stop_reason'] = stop_reason
                trace_row['status'] = 'STOPPED'
                pprint.warning('\n'.join(reason_lines or ('Predictor termination fired.',)))
                commit_trace_row()
                break

        if trace_row['status'] is None and status is not None:
            trace_row['status'] = status.upper()
        if trace_row['pareto_frontier_size'] is None:
            trace_row['pareto_frontier_size'] = len(pareto_frontier)
        if trace_row['pareto_stagnation'] is None:
            trace_row['pareto_stagnation'] = pareto_stagnation
        if trace_row['pareto_stagnation_score'] is None:
            trace_row['pareto_stagnation_score'] = pareto_stagnation_score
        if trace_row['run_best_area'] is None and best_seen_result is not None:
            trace_row['run_best_area'] = best_seen_result['area']
            trace_row['run_best_iteration'] = best_seen_result['iteration']
        if trace_row['best_seen_stagnation'] is None:
            trace_row['best_seen_stagnation'] = best_seen_stagnation
        commit_trace_row()

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
        'termination_zone_rank_from_max': (
            specs_obj.termination_zone_rank_from_max
            if specs_obj.cnn_constraint is CnnErrorConstraintTypes.ZONE_AET
            else None
        ),
        'adaptive_termination_zone_rank': specs_obj.adaptive_termination_zone_rank,
        'adaptive_termination_zone_rank_step_interval': specs_obj.adaptive_termination_zone_rank_step_interval,
        'best_seen_guard_pct': specs_obj.best_seen_guard_pct,
        'pareto_forgiveness': specs_obj.pareto_forgiveness,
        'pareto_forgiveness_decay': specs_obj.pareto_forgiveness_decay,
        'pareto_min_forgiveness': specs_obj.pareto_min_forgiveness,
        'pareto_aggressive_after_stagnation': specs_obj.pareto_aggressive_after_stagnation,
        'pareto_area_weight': specs_obj.pareto_area_weight,
        'pareto_power_weight': specs_obj.pareto_power_weight,
        'pareto_delay_weight': specs_obj.pareto_delay_weight,
        'pareto_near_frontier_penalty': specs_obj.pareto_near_frontier_penalty,
        'pareto_dominated_penalty': specs_obj.pareto_dominated_penalty,
        'pareto_regret_scale': specs_obj.pareto_regret_scale,
        'pareto_temperature_init': specs_obj.pareto_temperature_init,
        'pareto_temperature_decay': specs_obj.pareto_temperature_decay,
        'pareto_runtime_pressure_scale': specs_obj.pareto_runtime_pressure_scale,
        'pareto_rng_seed': specs_obj.pareto_rng_seed,
        'pareto_candidate_patience': specs_obj.pareto_candidate_patience,
        'pareto_candidate_step_stop_probability': specs_obj.pareto_candidate_step_stop_probability,
        'sentinel_best_seen_patience': specs_obj.sentinel_best_seen_patience,
        'sentinel_structural_stall_streak': specs_obj.sentinel_structural_stall_streak,
        'sentinel_same_subgraph_streak': specs_obj.sentinel_same_subgraph_streak,
        'sentinel_negative_cell_ratio': specs_obj.sentinel_negative_cell_ratio,
        'sentinel_marginal_gain_pct': specs_obj.sentinel_marginal_gain_pct,
        'sentinel_min_runtime_fraction': specs_obj.sentinel_min_runtime_fraction,
        'sentinel_min_timeout_count': specs_obj.sentinel_min_timeout_count,
        'sentinel_best_seen_iteration_patience': specs_obj.sentinel_best_seen_iteration_patience,
        'sentinel_min_beta': specs_obj.sentinel_min_beta,
        'predictor_model_path': specs_obj.predictor_model_path,
        'predictor_probability_threshold': specs_obj.predictor_probability_threshold,
        'predictor_min_iteration': specs_obj.predictor_min_iteration,
        'termination_zone_rank_effective': None if stop_snapshot is None else stop_snapshot.zone_rank_effective,
        'termination_zone_rank_applied': None if stop_snapshot is None else stop_snapshot.zone_rank_applied,
        'termination_zone_level_count': None if stop_snapshot is None else stop_snapshot.zone_level_count,
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
        'final_iteration': None if last_selected_result is None else last_selected_result['iteration'],
        'final_runtime_at_accept_seconds': None if last_selected_result is None else last_selected_result['runtime_at_accept_seconds'],
        'best_seen_benchmark': None if best_seen_result is None else best_seen_result['benchmark'],
        'best_seen_area': None if best_seen_result is None else best_seen_result['area'],
        'best_seen_power': None if best_seen_result is None else best_seen_result['power'],
        'best_seen_delay': None if best_seen_result is None else best_seen_result['delay'],
        'best_seen_verified_error_exact': None if best_seen_result is None else best_seen_result['verified_error_exact'],
        'best_seen_verified_error_prev': None if best_seen_result is None else best_seen_result['verified_error_prev'],
        'best_seen_cell': None if best_seen_result is None else best_seen_result['cell'],
        'best_seen_iteration': None if best_seen_result is None else best_seen_result['iteration'],
        'best_seen_runtime_at_accept_seconds': None if best_seen_result is None else best_seen_result['runtime_at_accept_seconds'],
        'best_seen_stagnation': best_seen_stagnation,
        'pareto_frontier_size': 0,
        'pareto_stagnation': pareto_stagnation,
        'pareto_stagnation_score': pareto_stagnation_score,
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
