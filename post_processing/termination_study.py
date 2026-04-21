from __future__ import annotations

import argparse
from datetime import datetime
import json
import math
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List

os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib-cache')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd


NUMBER_RE = r'-?\d+(?:\.\d+)?(?:e[+-]?\d+)?'
NUMBER_LITERAL_RE = re.compile(rf'^{NUMBER_RE}$', re.IGNORECASE)
ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
TABLE_ROW_RE = re.compile(
    rf'^\s*(?P<design>\S+)\s+(?P<area>{NUMBER_RE})\s+(?P<power>{NUMBER_RE})\s+(?P<delay>{NUMBER_RE})(?:\s+(?P<error>{NUMBER_RE}|None))?\s*$',
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Parse termination-study logs, rank parameter settings, and generate result plots.',
    )
    parser.add_argument(
        '--logs-root',
        type=Path,
        default=Path('benchmarking'),
        help='Directory containing benchmark logs (default: benchmarking)',
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output/figure/termination_study'),
        help='Directory for generated plots and CSVs (default: output/figure/termination_study)',
    )
    parser.add_argument(
        '--area-weight',
        type=float,
        default=0.7,
        help='Weight for normalized final area in the composite score (default: 0.7)',
    )
    parser.add_argument(
        '--runtime-weight',
        type=float,
        default=0.3,
        help='Weight for normalized runtime in the composite score (default: 0.3)',
    )
    parser.add_argument(
        '--include-wout',
        action='store_true',
        help='Include logs from benchmarking/wout (excluded by default because they are legacy verification traces).',
    )
    return parser.parse_args()


def _normalize_value(raw_value: str) -> object:
    value = raw_value.strip().rstrip(',')
    if value == 'None':
        return None
    if NUMBER_LITERAL_RE.match(value):
        try:
            return float(value)
        except ValueError:
            return value
    try:
        return int(value)
    except ValueError:
        if '.' in value:
            return value.split('.')[-1]
        return value


def _clean_text(text: str) -> str:
    return ANSI_ESCAPE_RE.sub('', text).replace('\r', '')


def _parse_specs_block(text: str) -> Dict[str, object]:
    match = re.search(r'specs_obj = Specifications\(\n(?P<body>.*?)\n\)', text, re.DOTALL)
    if match is None:
        return {}

    specs: Dict[str, object] = {}
    for raw_line in match.group('body').splitlines():
        line = raw_line.strip()
        if ' = ' not in line:
            continue
        key, value = line.split(' = ', 1)
        specs[key] = _normalize_value(value)
    return specs


def _normalize_termination_mode(mode: object) -> str:
    normalized = str(mode).strip().lower()
    if normalized == 'smart':
        return 'trivial'
    return normalized


def _infer_termination_mode(log_path: Path, text: str, specs: Dict[str, object]) -> str:
    if (mode := specs.get('termination_mode')) is not None:
        return _normalize_termination_mode(str(mode).split('.')[-1])
    parts = set(log_path.parts)
    if 'base' in parts:
        return 'none'
    if 'wtrivial' in parts:
        return 'trivial'
    if 'smart_terminal' in parts or log_path.name.startswith('smart_'):
        return 'trivial'
    if 'SMART TERMINATION FIRED' in text:
        return 'trivial'
    if 'TRIVIAL TERMINATION FIRED' in text or 'Termination Condition Met' in text:
        return 'trivial'
    return 'unknown'


def _parse_runtime_seconds(text: str) -> float | None:
    if (match := re.search(r'real\s+(\d+)m([\d.]+)s', text)) is None:
        start_match = re.search(r'^timestamp_start=(.+)$', text, re.MULTILINE)
        end_match = re.search(r'^timestamp_end=(.+)$', text, re.MULTILINE)
        if start_match is None or end_match is None:
            return None
        try:
            start = datetime.fromisoformat(start_match.group(1).strip())
            end = datetime.fromisoformat(end_match.group(1).strip())
        except ValueError:
            return None
        return max(0.0, (end - start).total_seconds())
    return int(match.group(1)) * 60 + float(match.group(2))


def _parse_exit_code(text: str) -> int | None:
    match = re.search(r'^exit_code=(\d+)$', text, re.MULTILINE)
    if match is None:
        return None
    return int(match.group(1))


def _parse_last_iteration(text: str) -> int | None:
    matches = re.findall(r'iteration\s+(\d+)\s+with', text)
    if not matches:
        return None
    return int(matches[-1])


def _parse_last_out_node(text: str) -> int | None:
    matches = re.findall(r'Current out_node:\s+(\d+)', text)
    if not matches:
        return None
    return int(matches[-1])


def _parse_stop_reason(text: str) -> str:
    if 'SMART TERMINATION FIRED' in text:
        return 'trivial_termination'
    if 'TRIVIAL TERMINATION FIRED' in text or 'Termination Condition Met' in text:
        return 'trivial_termination'
    if 'Pareto termination fired' in text:
        return 'pareto_termination'
    if 'Pareto-annealed termination fired' in text:
        return 'pareto_annealed_termination'
    if 'Sentinel termination fired' in text:
        return 'sentinel_termination'
    if 'The error space is exhausted (reached max bit)!' in text:
        return 'error_space_exhausted'
    return 'unknown'


def _parse_stop_details(text: str) -> tuple[int | None, int | None]:
    ceiling_match = re.search(r'Max legal error ceiling.*?(\d+)', text)
    bit_match = re.search(r'Bit\s+(\d+)\s+weight\s+\((\d+)\)', text)
    ceiling = int(ceiling_match.group(1)) if ceiling_match else None
    bit_weight = int(bit_match.group(2)) if bit_match else None
    return ceiling, bit_weight


def _parse_table_rows(text: str) -> List[Dict[str, float | str | None]]:
    rows: List[Dict[str, float | str | None]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('Design ID') or stripped.startswith('-----------'):
            continue
        match = TABLE_ROW_RE.match(stripped)
        if match is None:
            continue

        raw_error = match.group('error')
        error_value = None
        if raw_error not in (None, 'None'):
            try:
                error_value = float(raw_error)
            except ValueError:
                error_value = None

        rows.append(
            {
                'design_id': match.group('design'),
                'area': float(match.group('area')),
                'power': float(match.group('power')),
                'delay': float(match.group('delay')),
                'error': error_value,
            }
        )
    return rows


def _parse_exact_candidate(text: str) -> Dict[str, float] | None:
    exact = None
    for row in _parse_table_rows(text):
        if str(row['design_id']).lower() == 'exact':
            exact = {
                'exact_area': float(row['area']),
                'exact_power': float(row['power']),
                'exact_delay': float(row['delay']),
            }
    return exact


def _parse_last_candidate(text: str) -> Dict[str, float] | None:
    candidate = None
    for row in _parse_table_rows(text):
        design = str(row['design_id'])
        if design.lower() == 'exact':
            continue
        candidate = {
            'design_id': design,
            'final_area': float(row['area']),
            'final_power': float(row['power']),
            'final_delay': float(row['delay']),
            'final_reported_error': row['error'],
        }
    return candidate


def _parse_best_seen_candidate(text: str) -> Dict[str, float] | None:
    best_candidate = None
    for row in _parse_table_rows(text):
        design = str(row['design_id'])
        if design.lower() == 'exact':
            continue

        candidate = {
            'best_seen_design_id': design,
            'best_seen_area': float(row['area']),
            'best_seen_power': float(row['power']),
            'best_seen_delay': float(row['delay']),
            'best_seen_reported_error': row['error'],
        }
        if best_candidate is None:
            best_candidate = candidate
            continue

        if candidate['best_seen_area'] < best_candidate['best_seen_area']:
            best_candidate = candidate
            continue
        if (
            candidate['best_seen_area'] == best_candidate['best_seen_area']
            and candidate['best_seen_delay'] < best_candidate['best_seen_delay']
        ):
            best_candidate = candidate
            continue
        if (
            candidate['best_seen_area'] == best_candidate['best_seen_area']
            and candidate['best_seen_delay'] == best_candidate['best_seen_delay']
            and candidate['best_seen_power'] < best_candidate['best_seen_power']
        ):
            best_candidate = candidate

    return best_candidate


def _parse_final_verified_error(text: str) -> float | None:
    matches = re.findall(r'ErrorEval PASS! with total wce = ([^\n]+)', text)
    if not matches:
        return None
    value = matches[-1].strip()
    if value == 'None':
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _load_termination_summary(log_path: Path) -> Dict[str, object] | None:
    summary_dir = log_path.parent / 'output' / 'report' / 'termination_study'
    if not summary_dir.exists():
        return None
    summaries = sorted(summary_dir.glob('*_summary.json'))
    if not summaries:
        return None
    try:
        return json.loads(summaries[-1].read_text())
    except (OSError, json.JSONDecodeError):
        return None


def parse_log(log_path: Path) -> Dict[str, object] | None:
    text = _clean_text(log_path.read_text(errors='replace'))
    exit_code = _parse_exit_code(text)
    if exit_code not in (None, 0):
        return None

    specs = _parse_specs_block(text)
    exact = _parse_exact_candidate(text)
    candidate = _parse_last_candidate(text)
    best_seen_candidate = _parse_best_seen_candidate(text)
    if not specs or candidate is None:
        return None

    termination_mode = _infer_termination_mode(log_path, text, specs)
    benchmark = str(specs.get('exact_benchmark') or specs.get('current_benchmark') or log_path.stem)
    ceiling, bit_weight = _parse_stop_details(text)
    summary_data = _load_termination_summary(log_path)
    runtime_seconds = _parse_runtime_seconds(text)
    iteration_count = _parse_last_iteration(text)
    stop_reason = _parse_stop_reason(text)
    if summary_data is not None:
        runtime_seconds = runtime_seconds if runtime_seconds is not None else summary_data.get('runtime_seconds')
        iteration_count = iteration_count if iteration_count is not None else summary_data.get('iterations')
        stop_reason = stop_reason if stop_reason != 'unknown' else summary_data.get('stop_reason')

    termination_zone_rank_from_max = specs.get('termination_zone_rank_from_max')
    if termination_zone_rank_from_max is None and summary_data is not None:
        termination_zone_rank_from_max = summary_data.get('termination_zone_rank_from_max')
    adaptive_termination_zone_rank = specs.get('adaptive_termination_zone_rank')
    if adaptive_termination_zone_rank is None and summary_data is not None:
        adaptive_termination_zone_rank = summary_data.get('adaptive_termination_zone_rank')
    adaptive_termination_zone_rank_step_interval = specs.get('adaptive_termination_zone_rank_step_interval')
    if adaptive_termination_zone_rank_step_interval is None and summary_data is not None:
        adaptive_termination_zone_rank_step_interval = summary_data.get('adaptive_termination_zone_rank_step_interval')
    best_seen_guard_pct = specs.get('best_seen_guard_pct')
    if best_seen_guard_pct is None and summary_data is not None:
        best_seen_guard_pct = summary_data.get('best_seen_guard_pct')

    row = {
        'log_path': str(log_path),
        'log_mtime': log_path.stat().st_mtime,
        'benchmark': benchmark,
        'termination_mode': termination_mode,
        'metric': specs.get('metric'),
        'skip_verification': specs.get('skip_verification'),
        'cnn_constraint': specs.get('cnn_constraint'),
        'max_error': specs.get('max_error'),
        'alpha': specs.get('alpha'),
        'beta': specs.get('beta'),
        'c_constant': specs.get('c_constant'),
        'threshold_array_idx': specs.get('threshold_array_idx'),
        'termination_zone_rank_from_max': termination_zone_rank_from_max,
        'adaptive_termination_zone_rank': adaptive_termination_zone_rank,
        'adaptive_termination_zone_rank_step_interval': adaptive_termination_zone_rank_step_interval,
        'best_seen_guard_pct': best_seen_guard_pct,
        'termination_zone_rank_effective': None if summary_data is None else summary_data.get('termination_zone_rank_effective'),
        'termination_zone_rank_applied': None if summary_data is None else summary_data.get('termination_zone_rank_applied'),
        'termination_zone_level_count': None if summary_data is None else summary_data.get('termination_zone_level_count'),
        'iteration_count': iteration_count,
        'stop_reason': stop_reason,
        'stop_out_node': _parse_last_out_node(text),
        'termination_ceiling': ceiling,
        'bit_weight_at_stop': bit_weight,
        'runtime_seconds': runtime_seconds,
        'exit_code': exit_code,
        'final_verified_error_exact': _parse_final_verified_error(text),
        **(exact or {}),
        **candidate,
        **(best_seen_candidate or {}),
    }
    if summary_data is not None:
        row['best_seen_benchmark'] = summary_data.get('best_seen_benchmark')
        row['best_seen_area'] = summary_data.get('best_seen_area', row.get('best_seen_area'))
        row['best_seen_power'] = summary_data.get('best_seen_power', row.get('best_seen_power'))
        row['best_seen_delay'] = summary_data.get('best_seen_delay', row.get('best_seen_delay'))
        row['best_seen_verified_error_exact'] = summary_data.get('best_seen_verified_error_exact')
        row['best_seen_verified_error_prev'] = summary_data.get('best_seen_verified_error_prev')
        row['best_seen_cell'] = summary_data.get('best_seen_cell')
        row['best_seen_iteration'] = summary_data.get('best_seen_iteration')
        row['best_seen_runtime_at_accept_seconds'] = summary_data.get('best_seen_runtime_at_accept_seconds')
    else:
        row['best_seen_benchmark'] = None
        row['best_seen_verified_error_exact'] = None
        row['best_seen_verified_error_prev'] = None
        row['best_seen_cell'] = None
        row['best_seen_iteration'] = None
        row['best_seen_runtime_at_accept_seconds'] = None

    exact_area = row.get('exact_area')
    final_area = row.get('final_area')
    if isinstance(exact_area, (int, float)) and isinstance(final_area, (int, float)) and exact_area:
        row['area_reduction_pct'] = ((exact_area - final_area) / exact_area) * 100.0
    else:
        row['area_reduction_pct'] = None
    best_seen_area = row.get('best_seen_area')
    if isinstance(exact_area, (int, float)) and isinstance(best_seen_area, (int, float)) and exact_area:
        row['best_seen_area_reduction_pct'] = ((exact_area - best_seen_area) / exact_area) * 100.0
    else:
        row['best_seen_area_reduction_pct'] = None
    return row


def discover_logs(logs_root: Path, include_wout: bool = False) -> List[Path]:
    if logs_root.is_file():
        return [logs_root]
    return sorted(
        path
        for path in logs_root.rglob('*.log')
        if path.is_file() and (include_wout or 'wout' not in path.parts)
    )


def deduplicate_runs(rows: Iterable[Dict[str, object]]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    dedupe_keys = [
        'benchmark',
        'termination_mode',
        'cnn_constraint',
        'max_error',
        'alpha',
        'beta',
        'c_constant',
        'threshold_array_idx',
        'termination_zone_rank_from_max',
        'adaptive_termination_zone_rank',
        'adaptive_termination_zone_rank_step_interval',
        'best_seen_guard_pct',
    ]
    df = df.sort_values('log_mtime')
    df = df.drop_duplicates(subset=dedupe_keys, keep='last')
    return df.reset_index(drop=True)


def add_scores(df: pd.DataFrame, area_weight: float, runtime_weight: float) -> pd.DataFrame:
    scored = df.copy()

    def normalize(series: pd.Series) -> pd.Series:
        numeric = pd.to_numeric(series, errors='coerce')
        valid = numeric.dropna()
        if valid.nunique() <= 1:
            return pd.Series([0.0] * len(series), index=series.index)
        min_value = valid.min()
        max_value = valid.max()
        normalized = (numeric - min_value) / (max_value - min_value)
        return normalized.fillna(1.0)

    comparison_keys = ['benchmark', 'cnn_constraint', 'max_error']
    scored['comparison_group'] = (
        scored['benchmark'].astype(str)
        + '|'
        + scored['cnn_constraint'].fillna('None').astype(str)
        + '|'
        + scored['max_error'].fillna(-1).astype(str)
    )
    scored['area_norm'] = scored.groupby('benchmark')['final_area'].transform(normalize)
    scored['runtime_norm'] = scored.groupby('benchmark')['runtime_seconds'].transform(normalize)
    scored['composite_score'] = (scored['area_norm'] * area_weight) + (scored['runtime_norm'] * runtime_weight)
    scored['group_area_norm'] = scored.groupby(comparison_keys)['final_area'].transform(normalize)
    scored['group_runtime_norm'] = scored.groupby(comparison_keys)['runtime_seconds'].transform(normalize)
    scored['group_composite_score'] = (scored['group_area_norm'] * area_weight) + (scored['group_runtime_norm'] * runtime_weight)

    budget_status = []
    for verified_error, max_error, skip_verification in zip(
        pd.to_numeric(scored['final_verified_error_exact'], errors='coerce'),
        pd.to_numeric(scored['max_error'], errors='coerce'),
        scored.get('skip_verification', pd.Series([None] * len(scored), index=scored.index)),
    ):
        skip_value = str(skip_verification).strip().lower()
        if skip_value in {'true', '1'}:
            budget_status.append('unknown')
        elif pd.isna(verified_error) or pd.isna(max_error) or verified_error < 0:
            budget_status.append('unknown')
        elif verified_error <= max_error:
            budget_status.append('within_budget')
        else:
            budget_status.append('over_budget')
    scored['budget_status'] = budget_status
    return scored


def mark_pareto_optimal(df: pd.DataFrame) -> pd.DataFrame:
    marked = df.copy()
    marked['is_pareto'] = False

    for benchmark, group in marked.groupby('benchmark'):
        valid_group = group.dropna(subset=['final_area', 'runtime_seconds'])
        indices = list(valid_group.index)
        pareto_indices = []
        for idx in indices:
            candidate = marked.loc[idx]
            dominated = False
            for other_idx in indices:
                if other_idx == idx:
                    continue
                other = marked.loc[other_idx]
                better_or_equal = (
                    other['final_area'] <= candidate['final_area']
                    and other['runtime_seconds'] <= candidate['runtime_seconds']
                )
                strictly_better = (
                    other['final_area'] < candidate['final_area']
                    or other['runtime_seconds'] < candidate['runtime_seconds']
                )
                if better_or_equal and strictly_better:
                    dominated = True
                    break
            if not dominated:
                pareto_indices.append(idx)
        marked.loc[pareto_indices, 'is_pareto'] = True

    return marked


def short_label(row: pd.Series) -> str:
    parts = [row['termination_mode']]
    if pd.notna(row.get('cnn_constraint')):
        parts.append(str(row['cnn_constraint']))
    if pd.notna(row.get('max_error')):
        parts.append(f"e{int(row['max_error'])}")
    if pd.notna(row.get('alpha')):
        parts.append(f"a{int(row['alpha'])}")
    if pd.notna(row.get('beta')):
        parts.append(f"b{int(row['beta'])}")
    if pd.notna(row.get('c_constant')):
        parts.append(f"c{int(row['c_constant'])}")
    if pd.notna(row.get('threshold_array_idx')):
        parts.append(f"t{int(row['threshold_array_idx'])}")
    if pd.notna(row.get('termination_zone_rank_from_max')):
        parts.append(f"zr{int(row['termination_zone_rank_from_max'])}")
    return ' '.join(parts)


def case_label(row: pd.Series) -> str:
    parts = []
    if pd.notna(row.get('cnn_constraint')):
        parts.append(str(row['cnn_constraint']))
    if pd.notna(row.get('max_error')):
        parts.append(f"e{int(row['max_error'])}")
    if pd.notna(row.get('alpha')):
        parts.append(f"a{int(row['alpha'])}")
    if pd.notna(row.get('beta')):
        parts.append(f"b{int(row['beta'])}")
    if pd.notna(row.get('c_constant')):
        parts.append(f"c{int(row['c_constant'])}")
    if pd.notna(row.get('threshold_array_idx')):
        parts.append(f"t{int(row['threshold_array_idx'])}")
    if pd.notna(row.get('termination_zone_rank_from_max')):
        parts.append(f"zr{int(row['termination_zone_rank_from_max'])}")
    return ' '.join(parts)


def _numeric_or_none(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce')


def _format_float(value: object, digits: int = 3) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]
    if pd.isna(numeric):
        return 'unknown'
    return f'{float(numeric):.{digits}f}'


def _format_seconds(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]
    if pd.isna(numeric):
        return 'unknown'
    return f'{float(numeric):.3f}s'


def _format_percentage(value: object) -> str:
    numeric = pd.to_numeric(pd.Series([value]), errors='coerce').iloc[0]
    if pd.isna(numeric):
        return 'unknown'
    return f'{float(numeric):.2f}%'


def _marker_for_mode(mode: str) -> str:
    return {'none': 'o', 'trivial': 's', 'pareto': '^', 'pareto_annealed': 'v', 'sentinel': 'X', 'hybrid': 'P', 'predictor': 'D'}.get(_normalize_termination_mode(mode), 'D')


def _color_for_mode(mode: str) -> str:
    return {
        'none': '#2d6a4f',
        'trivial': '#c1121f',
        'pareto': '#4361ee',
        'pareto_annealed': '#0f766e',
        'sentinel': '#ea580c',
        'hybrid': '#7b2cbf',
        'predictor': '#1d4ed8',
        'unknown': '#6b7280',
    }.get(_normalize_termination_mode(mode), '#6b7280')


def _short_mode_label(mode: object) -> str:
    normalized = _normalize_termination_mode(str(mode))
    return {
        'none': 'none',
        'trivial': 'triv',
        'pareto': 'par',
        'pareto_annealed': 'par+',
        'sentinel': 'sent',
        'hybrid': 'hyb',
        'predictor': 'pred',
        'unknown': 'unk',
    }.get(normalized, normalized[:4])


def _compact_case_label(row: pd.Series) -> str:
    try:
        max_error = int(float(row.get('max_error', 0)))
    except (TypeError, ValueError):
        max_error = row.get('max_error', 'e?')
    try:
        beta = int(float(row.get('beta', 0)))
    except (TypeError, ValueError):
        beta = row.get('beta', 'b?')
    try:
        rank = int(float(row.get('termination_zone_rank_from_max', 0)))
    except (TypeError, ValueError):
        rank = row.get('termination_zone_rank_from_max', 'r?')
    return f"e{max_error} b{beta} zr{rank}"


def _size_from_budget(series: pd.Series) -> pd.Series:
    numeric = _numeric_or_none(series)
    valid = numeric.dropna()
    if valid.empty or valid.nunique() <= 1:
        return pd.Series([240.0] * len(series), index=series.index)
    scaled = 180.0 + 320.0 * ((numeric - valid.min()) / (valid.max() - valid.min()))
    return scaled.fillna(240.0)


def _winner_mode(delta: object, tolerance: float = 1e-9) -> str:
    numeric = pd.to_numeric(pd.Series([delta]), errors='coerce').iloc[0]
    if pd.isna(numeric):
        return 'unknown'
    if abs(float(numeric)) <= tolerance:
        return 'tie'
    return 'trivial' if float(numeric) < 0 else 'none'


def _winner_between_modes(delta: object, compare_mode: object, baseline_mode: str = 'none', tolerance: float = 1e-9) -> str:
    numeric = pd.to_numeric(pd.Series([delta]), errors='coerce').iloc[0]
    if pd.isna(numeric):
        return 'unknown'
    if abs(float(numeric)) <= tolerance:
        return 'tie'
    return str(compare_mode) if float(numeric) < 0 else baseline_mode


def _stop_reason_short(stop_reason: object) -> str:
    if stop_reason is None or pd.isna(stop_reason):
        return 'n/a'
    normalized = str(stop_reason).strip().lower()
    mapping = {
        'error_space_exhausted': 'exh',
        'trivial_termination': 'triv',
        'pareto_termination': 'par',
        'pareto_annealed_termination': 'par+',
        'sentinel_termination': 'sent',
        'hybrid_termination': 'hyb',
        'unknown': 'unk',
    }
    return mapping.get(normalized, normalized[:4])


def _default_baseline_modes(df: pd.DataFrame) -> List[str]:
    present_modes = [
        _normalize_termination_mode(mode)
        for mode in pd.Series(df['termination_mode']).dropna().astype(str).unique()
    ]
    preferred = [mode for mode in ['none', 'trivial'] if mode in present_modes]
    if preferred:
        return preferred
    return present_modes[:1]


def build_mode_delta_table(df: pd.DataFrame, baseline_modes: Iterable[str] | None = None) -> pd.DataFrame:
    case_keys = [
        'benchmark',
        'cnn_constraint',
        'max_error',
        'alpha',
        'beta',
        'c_constant',
        'threshold_array_idx',
        'termination_zone_rank_from_max',
    ]
    working = df.copy()
    working['case_label'] = working.apply(case_label, axis=1)
    working['termination_mode'] = working['termination_mode'].map(_normalize_termination_mode)

    present_modes = list(dict.fromkeys(working['termination_mode'].dropna().tolist()))
    requested_baselines = _default_baseline_modes(working) if baseline_modes is None else [
        _normalize_termination_mode(mode) for mode in baseline_modes
    ]
    baseline_modes_list = [mode for mode in requested_baselines if mode in present_modes]
    if not baseline_modes_list:
        baseline_modes_list = present_modes[:1]

    non_baseline_modes = [mode for mode in present_modes if mode not in baseline_modes_list]
    keep_columns = case_keys + ['case_label', 'termination_mode', 'final_area', 'runtime_seconds', 'stop_reason', 'best_seen_area']
    paired_tables: List[pd.DataFrame] = []

    for baseline_mode in baseline_modes_list:
        compare_modes = non_baseline_modes if non_baseline_modes else [mode for mode in present_modes if mode != baseline_mode]
        if not compare_modes:
            continue

        baseline_df = working[working['termination_mode'] == baseline_mode][keep_columns].rename(
            columns={
                'final_area': 'final_area_baseline',
                'best_seen_area': 'best_seen_area_baseline',
                'runtime_seconds': 'runtime_seconds_baseline',
                'stop_reason': 'stop_reason_baseline',
            }
        )
        compare_df = working[working['termination_mode'].isin(compare_modes)][keep_columns].rename(
            columns={
                'termination_mode': 'compare_mode',
                'final_area': 'final_area_compare',
                'best_seen_area': 'best_seen_area_compare',
                'runtime_seconds': 'runtime_seconds_compare',
                'stop_reason': 'stop_reason_compare',
            }
        )

        paired = baseline_df.drop(columns=['termination_mode']).merge(
            compare_df,
            on=case_keys + ['case_label'],
            how='inner',
        )
        paired['baseline_mode'] = baseline_mode
        paired['delta_area_compare_minus_baseline'] = paired['final_area_compare'] - paired['final_area_baseline']
        paired['delta_runtime_compare_minus_baseline'] = paired['runtime_seconds_compare'] - paired['runtime_seconds_baseline']
        paired['delta_best_seen_area_compare_minus_baseline'] = paired['best_seen_area_compare'] - paired['best_seen_area_baseline']
        paired['area_improvement_pct_compare_vs_baseline'] = (
            (paired['final_area_baseline'] - paired['final_area_compare']) / paired['final_area_baseline']
        ) * 100.0
        paired['runtime_improvement_pct_compare_vs_baseline'] = (
            (paired['runtime_seconds_baseline'] - paired['runtime_seconds_compare']) / paired['runtime_seconds_baseline']
        ) * 100.0
        paired['best_seen_area_improvement_pct_compare_vs_baseline'] = (
            (paired['best_seen_area_baseline'] - paired['best_seen_area_compare']) / paired['best_seen_area_baseline']
        ) * 100.0
        paired['area_better_mode'] = paired.apply(
            lambda row: _winner_between_modes(row['delta_area_compare_minus_baseline'], row.get('compare_mode'), baseline_mode),
            axis=1,
        )
        paired['runtime_better_mode'] = paired.apply(
            lambda row: _winner_between_modes(row['delta_runtime_compare_minus_baseline'], row.get('compare_mode'), baseline_mode),
            axis=1,
        )
        paired_tables.append(paired)

    if not paired_tables:
        return pd.DataFrame()

    return pd.concat(paired_tables, ignore_index=True).sort_values([
        'benchmark',
        'baseline_mode',
        'cnn_constraint',
        'max_error',
        'alpha',
        'beta',
        'c_constant',
        'threshold_array_idx',
        'termination_zone_rank_from_max',
        'compare_mode',
    ]).reset_index(drop=True)


def plot_tradeoff(df: pd.DataFrame, output_dir: Path) -> Path:
    benchmarks = list(df['benchmark'].unique())
    ncols = 2 if len(benchmarks) > 1 else 1
    nrows = math.ceil(len(benchmarks) / ncols)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(9 * ncols, 5.8 * nrows), squeeze=False)

    for ax, benchmark in zip(axes.flat, benchmarks):
        subset = df[df['benchmark'] == benchmark].sort_values('composite_score')
        plotted_any = False
        for _, row in subset.iterrows():
            if pd.isna(row['runtime_seconds']) or pd.isna(row['final_area']):
                continue
            color = _color_for_mode(str(row['termination_mode']))
            marker = 'X' if row['is_pareto'] else 'o'
            ax.scatter(row['runtime_seconds'], row['final_area'], color=color, marker=marker, s=90, alpha=0.85)
            plotted_any = True
            if len(subset) <= 14 or row['is_pareto']:
                ax.annotate(
                    f"{_compact_case_label(row)} [{_short_mode_label(row['termination_mode'])}]",
                    (row['runtime_seconds'], row['final_area']),
                    fontsize=8,
                    xytext=(5, 5),
                    textcoords='offset points',
                )
        frontier = subset[subset['is_pareto']].dropna(subset=['runtime_seconds', 'final_area']).sort_values('runtime_seconds')
        if not frontier.empty:
            ax.plot(frontier['runtime_seconds'], frontier['final_area'], color='#f59e0b', linestyle='--', linewidth=1.6, alpha=0.9)
        ax.set_title(f'{benchmark}: runtime vs final area', fontsize=12)
        ax.set_xlabel('Runtime (s)')
        ax.set_ylabel('Final area')
        ax.grid(alpha=0.3)
        if not plotted_any:
            ax.text(0.5, 0.5, 'No complete runtime data', ha='center', va='center', transform=ax.transAxes)

    for ax in axes.flat[len(benchmarks):]:
        ax.axis('off')

    handles = [
        plt.Line2D([0], [0], marker='o', color='w', label=mode, markerfacecolor=color, markersize=10)
        for mode, color in {m: _color_for_mode(m) for m in ['none', 'trivial', 'pareto', 'pareto_annealed', 'sentinel', 'hybrid', 'unknown']}.items()
        if mode in set(df['termination_mode'])
    ]
    fig.legend(handles=handles, loc='upper center', ncol=max(1, len(handles)))
    fig.subplots_adjust(top=0.86, left=0.08, right=0.98, bottom=0.1, hspace=0.3, wspace=0.22)

    output_path = output_dir / 'termination_tradeoff_by_benchmark.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_mode_comparison(df: pd.DataFrame, benchmark: str, output_dir: Path) -> Path | None:
    deltas = build_mode_delta_table(df)
    subset = deltas[deltas['benchmark'] == benchmark].copy()
    subset = subset.dropna(subset=['final_area_baseline', 'final_area_compare', 'runtime_seconds_baseline', 'runtime_seconds_compare'])
    if subset.empty:
        return None

    subset = subset.sort_values(['baseline_mode', 'max_error', 'beta', 'alpha', 'termination_zone_rank_from_max', 'compare_mode']).reset_index(drop=True)
    baseline_modes = [mode for mode in ['none', 'trivial'] if mode in set(subset['baseline_mode'])]
    if not baseline_modes:
        baseline_modes = sorted(subset['baseline_mode'].dropna().unique())
    mode_order = ['trivial', 'pareto', 'pareto_annealed', 'sentinel', 'hybrid', 'unknown']
    compare_modes = sorted(subset['compare_mode'].dropna().unique(), key=lambda mode: (mode_order.index(mode) if mode in mode_order else len(mode_order), mode))
    case_order = list(dict.fromkeys(subset['case_label'].tolist()))

    metric_specs = [
        ('area_improvement_pct_compare_vs_baseline', 'delta_area_compare_minus_baseline', 'final area improvement', 'positive means compared mode is smaller', lambda value: f'{value:+.2f}'),
        ('best_seen_area_improvement_pct_compare_vs_baseline', 'delta_best_seen_area_compare_minus_baseline', 'best-seen area improvement', 'positive means compared mode reached a smaller best checkpoint', lambda value: f'{value:+.2f}'),
        ('runtime_improvement_pct_compare_vs_baseline', 'delta_runtime_compare_minus_baseline', 'runtime improvement', 'positive means compared mode is faster', lambda value: f'{value:+.0f}s'),
    ]

    cmap = plt.get_cmap('RdYlGn').copy()
    cmap.set_bad('#f3f4f6')
    metric_maxima: Dict[str, float] = {}
    for metric_col, _, _, _, _ in metric_specs:
        metric_values = subset[metric_col].dropna().abs()
        metric_maxima[metric_col] = max(1.0, float(metric_values.max())) if not metric_values.empty else 1.0

    fig, axes = plt.subplots(
        nrows=len(baseline_modes),
        ncols=len(metric_specs),
        figsize=(
            max(12.5, len(compare_modes) * 3.1 * len(metric_specs)),
            max(5.0, len(case_order) * 0.7 * len(baseline_modes)),
        ),
        sharey='row',
        squeeze=False,
    )

    compact_labels = [
        _compact_case_label(
            subset[subset['case_label'] == label].iloc[0]
            if not subset[subset['case_label'] == label].empty
            else pd.Series({'case_label': label})
        )
        for label in case_order
    ]

    colorbars = []
    for row_idx, baseline_mode in enumerate(baseline_modes):
        baseline_subset = subset[subset['baseline_mode'] == baseline_mode].copy()
        stop_matrix = baseline_subset.pivot(index='case_label', columns='compare_mode', values='stop_reason_compare').reindex(index=case_order, columns=compare_modes)

        for col_idx, (metric_col, delta_col, metric_title, metric_subtitle, delta_formatter) in enumerate(metric_specs):
            metric_matrix = baseline_subset.pivot(index='case_label', columns='compare_mode', values=metric_col).reindex(index=case_order, columns=compare_modes)
            delta_matrix = baseline_subset.pivot(index='case_label', columns='compare_mode', values=delta_col).reindex(index=case_order, columns=compare_modes)
            ax = axes[row_idx, col_idx]
            image = ax.imshow(
                metric_matrix.to_numpy(dtype=float),
                aspect='auto',
                cmap=cmap,
                vmin=-metric_maxima[metric_col],
                vmax=metric_maxima[metric_col],
            )
            if row_idx == 0:
                ax.set_title(f'{metric_title}\n{metric_subtitle}', fontsize=10.5)
            ax.set_xticks(range(len(compare_modes)))
            ax.set_xticklabels([_short_mode_label(m) for m in compare_modes])
            ax.set_yticks(range(len(case_order)))
            ax.set_yticklabels(compact_labels)
            ax.set_xlabel(f'Compared mode vs {baseline_mode}')
            if col_idx == 0:
                ax.set_ylabel(f'Baseline: {baseline_mode}\nParameter case')
            ax.set_xticks([x - 0.5 for x in range(1, len(compare_modes))], minor=True)
            ax.set_yticks([y - 0.5 for y in range(1, len(case_order))], minor=True)
            ax.grid(which='minor', color='white', linewidth=1.2)
            ax.tick_params(which='minor', bottom=False, left=False)

            for i, case_label_value in enumerate(case_order):
                for j, compare_mode in enumerate(compare_modes):
                    metric_value = metric_matrix.loc[case_label_value, compare_mode]
                    delta_value = delta_matrix.loc[case_label_value, compare_mode]
                    stop_value = _stop_reason_short(stop_matrix.loc[case_label_value, compare_mode])
                    if pd.notna(metric_value):
                        delta_text = delta_formatter(float(delta_value)) if pd.notna(delta_value) else 'n/a'
                        ax.text(
                            j,
                            i,
                            f'{float(metric_value):+.1f}%\n{delta_text} {stop_value}',
                            ha='center',
                            va='center',
                            fontsize=7.1,
                            color='#111827',
                        )
                    else:
                        ax.text(j, i, 'n/a', ha='center', va='center', fontsize=7.5, color='#9ca3af')

            if row_idx == 0:
                colorbars.append((image, ax, metric_col))

    for image, ax, metric_col in colorbars:
        colorbar = fig.colorbar(image, ax=ax, shrink=0.84, pad=0.02)
        colorbar.set_label(f'{metric_specs[[spec[0] for spec in metric_specs].index(metric_col)][2]} (%)')

    baseline_label = ' and '.join(baseline_modes)
    fig.suptitle(f'General mode comparison relative to {baseline_label}', y=0.99, fontsize=13)
    fig.subplots_adjust(
        left=0.19 if len(case_order) > 4 else 0.14,
        right=0.96,
        top=0.89,
        bottom=0.08,
        wspace=0.22,
        hspace=0.26,
    )

    output_path = output_dir / f'{benchmark}_mode_comparison.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_case_scorecard(df: pd.DataFrame, benchmark: str, output_dir: Path) -> Path:
    subset = (
        df[df['benchmark'] == benchmark]
        .dropna(subset=['final_area', 'runtime_seconds'])
        .sort_values('composite_score')
        .reset_index(drop=True)
    )
    if subset.empty:
        return output_dir / f'{benchmark}_parameter_comparison.png'
    labels = [short_label(row) for _, row in subset.iterrows()]
    colors = subset['termination_mode'].map(_color_for_mode)

    fig, (ax_area, ax_runtime) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(max(12, len(subset) * 1.15), 8.2),
        sharex=True,
        gridspec_kw={'height_ratios': [1.1, 1.0]},
    )

    bars = ax_area.bar(range(len(subset)), subset['final_area'], color=colors, alpha=0.9)
    for idx, (_, row) in enumerate(subset.iterrows()):
        if row['is_pareto']:
            bars[idx].set_edgecolor('#f59e0b')
            bars[idx].set_linewidth(2.5)

    ax_runtime.bar(range(len(subset)), subset['runtime_seconds'], color=colors, alpha=0.6)

    ax_area.set_title(f'{benchmark}: ranked settings')
    ax_area.set_ylabel('Final area')
    ax_area.grid(axis='y', alpha=0.3)
    ax_runtime.set_ylabel('Runtime (s)')
    ax_runtime.set_xlabel('Setting')
    ax_runtime.grid(axis='y', alpha=0.3)
    ax_runtime.set_xticks(range(len(subset)))
    ax_runtime.set_xticklabels(labels, rotation=35, ha='right', fontsize=8)

    legend_handles = [
        plt.Line2D([0], [0], marker='s', color='w', label='Pareto / non-dominated edge', markerfacecolor='#f59e0b', markersize=0, markeredgecolor='#f59e0b', linewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label='none', markerfacecolor=_color_for_mode('none'), markersize=10),
        plt.Line2D([0], [0], marker='s', color='w', label='trivial', markerfacecolor=_color_for_mode('trivial'), markersize=10),
        plt.Line2D([0], [0], marker='^', color='w', label='pareto', markerfacecolor=_color_for_mode('pareto'), markersize=10),
        plt.Line2D([0], [0], marker='v', color='w', label='pareto_annealed', markerfacecolor=_color_for_mode('pareto_annealed'), markersize=10),
        plt.Line2D([0], [0], marker='X', color='w', label='sentinel', markerfacecolor=_color_for_mode('sentinel'), markersize=10),
        plt.Line2D([0], [0], marker='P', color='w', label='hybrid', markerfacecolor=_color_for_mode('hybrid'), markersize=10),
    ]
    fig.legend(handles=legend_handles, loc='upper center', ncol=7)
    fig.subplots_adjust(top=0.88, bottom=0.14)

    output_path = output_dir / f'{benchmark}_parameter_comparison.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_alpha_beta_sweep(df: pd.DataFrame, benchmark: str, output_dir: Path) -> Path | None:
    subset = df[df['benchmark'] == benchmark].copy()
    subset['alpha_num'] = _numeric_or_none(subset['alpha'])
    subset['beta_num'] = _numeric_or_none(subset['beta'])
    subset = subset.dropna(subset=['alpha_num', 'beta_num'])

    if subset.empty or (subset['alpha_num'].nunique() <= 1 and subset['beta_num'].nunique() <= 1):
        return None

    sizes = _size_from_budget(subset['max_error'])
    fig, ax = plt.subplots(figsize=(8, 6))

    for mode, mode_subset in subset.groupby('termination_mode'):
        indices = list(mode_subset.index)
        scatter = ax.scatter(
            mode_subset['beta_num'],
            mode_subset['alpha_num'],
            s=sizes.loc[indices],
            c=mode_subset['area_reduction_pct'],
            cmap='viridis',
            marker=_marker_for_mode(mode),
            edgecolors='#111827',
            linewidths=0.8,
            alpha=0.9,
            label=mode,
        )
        for _, row in mode_subset.iterrows():
            ax.annotate(
                f"e{int(row['max_error'])}" if pd.notna(row['max_error']) else row['termination_mode'],
                (row['beta_num'], row['alpha_num']),
                fontsize=8,
                xytext=(5, 4),
                textcoords='offset points',
            )

    colorbar = fig.colorbar(scatter, ax=ax)
    colorbar.set_label('Area reduction (%)')
    ax.set_title(f'{benchmark}: alpha/beta sweep')
    ax.set_xlabel('Beta')
    ax.set_ylabel('Alpha')
    ax.grid(alpha=0.3)
    ax.legend(title='Termination mode')
    fig.tight_layout()

    output_path = output_dir / f'{benchmark}_alpha_beta_sweep.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def summarize_parameter_effects(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    parameters = ['termination_mode', 'cnn_constraint', 'max_error', 'alpha', 'beta', 'c_constant', 'threshold_array_idx', 'termination_zone_rank_from_max']

    for benchmark, benchmark_df in df.groupby('benchmark'):
        for parameter in parameters:
            non_null = benchmark_df[benchmark_df[parameter].notna()]
            if non_null.empty:
                continue
            for value, subset in non_null.groupby(parameter):
                ordered = subset.sort_values('group_composite_score')
                best = ordered.iloc[0]
                rows.append(
                    {
                        'benchmark': benchmark,
                        'parameter': parameter,
                        'value': value,
                        'runs': len(subset),
                        'mean_final_area': subset['final_area'].mean(),
                        'best_final_area': subset['final_area'].min(),
                        'mean_runtime_seconds': subset['runtime_seconds'].mean(),
                        'fastest_runtime_seconds': subset['runtime_seconds'].min(),
                        'mean_area_reduction_pct': subset['area_reduction_pct'].mean(),
                        'best_label': best['label'],
                        'best_group_composite_score': best['group_composite_score'],
                        'best_budget_status': best['budget_status'],
                    }
                )

    return pd.DataFrame(rows)


def write_report(df: pd.DataFrame, output_dir: Path) -> Path:
    lines = ['# Termination Study Parameter Report', '']
    pairwise_deltas = build_mode_delta_table(df)
    for benchmark, subset in df.groupby('benchmark'):
        completed = subset.dropna(subset=['final_area', 'runtime_seconds']).copy()
        if completed.empty:
            lines.append(f'## {benchmark}')
            lines.append('')
            lines.append('- No completed runs with both final area and runtime were available.')
            lines.append('')
            continue
        ordered = completed.sort_values('composite_score')
        best = ordered.iloc[0]
        lines.append(f'## {benchmark}')
        lines.append('')
        lines.append(
            f'- Best composite score: `{short_label(best)}` '
            f'(area `{best.final_area:.4f}`, runtime `{_format_seconds(best.runtime_seconds)}`, '
            f'area reduction `{_format_percentage(best.area_reduction_pct)}`, stop `{best.stop_reason}`)'
        )
        area_best = completed.loc[completed['final_area'].idxmin()]
        runtime_best = completed.loc[completed['runtime_seconds'].idxmin()]
        lines.append(
            f'- Lowest area: `{short_label(area_best)}` '
            f'(area `{area_best.final_area:.4f}`, runtime `{_format_seconds(area_best.runtime_seconds)}`)'
        )
        lines.append(
            f'- Fastest run: `{short_label(runtime_best)}` '
            f'(runtime `{_format_seconds(runtime_best.runtime_seconds)}`, area `{runtime_best.final_area:.4f}`)'
        )
        for (constraint, max_error), group in completed.groupby(['cnn_constraint', 'max_error']):
            group_best = group.sort_values('group_composite_score').iloc[0]
            lines.append(
                f'- Best for constraint `{constraint}` and max_error `{int(max_error)}`: '
                f'`{short_label(group_best)}` '
                f'(area `{group_best.final_area:.4f}`, runtime `{_format_seconds(group_best.runtime_seconds)}`, '
                f'budget `{group_best.budget_status}`)'
            )
        lines.append('- Non-dominated tradeoff settings in this tested set:')
        lines.append('  - These are the runs for which no other tested run is both faster and smaller-area at the same time.')
        pareto_subset = ordered[ordered['is_pareto']]
        for _, row in pareto_subset.iterrows():
            lines.append(
                f'  - `{short_label(row)}` '
                f'area `{row.final_area:.4f}`, runtime `{_format_seconds(row.runtime_seconds)}`, delay `{row.final_delay:.6f}`'
            )
        benchmark_deltas = pairwise_deltas[pairwise_deltas['benchmark'] == benchmark].copy()
        if not benchmark_deltas.empty:
            lines.append('- Pairwise baseline comparisons:')
            lines.append('  - Positive percentages mean the compared mode is better than the baseline.')
            for (baseline_mode, compare_mode), pair_subset in benchmark_deltas.groupby(['baseline_mode', 'compare_mode']):
                runtime_faster = int((pair_subset['runtime_improvement_pct_compare_vs_baseline'] > 1e-9).sum())
                runtime_slower = int((pair_subset['runtime_improvement_pct_compare_vs_baseline'] < -1e-9).sum())
                runtime_tied = int((pair_subset['runtime_improvement_pct_compare_vs_baseline'].abs() <= 1e-9).sum())
                area_better = int((pair_subset['area_improvement_pct_compare_vs_baseline'] > 1e-9).sum())
                area_worse = int((pair_subset['area_improvement_pct_compare_vs_baseline'] < -1e-9).sum())
                area_tied = int((pair_subset['area_improvement_pct_compare_vs_baseline'].abs() <= 1e-9).sum())
                best_seen_better = int((pair_subset['best_seen_area_improvement_pct_compare_vs_baseline'] > 1e-9).sum())
                best_seen_worse = int((pair_subset['best_seen_area_improvement_pct_compare_vs_baseline'] < -1e-9).sum())
                best_seen_tied = int((pair_subset['best_seen_area_improvement_pct_compare_vs_baseline'].abs() <= 1e-9).sum())
                lines.append(
                    f'  - `{compare_mode}` vs `{baseline_mode}`: '
                    f'mean runtime `{pair_subset["runtime_improvement_pct_compare_vs_baseline"].mean():+.2f}%` '
                    f'(`{pair_subset["delta_runtime_compare_minus_baseline"].mean():+.1f}s`), '
                    f'mean final area `{pair_subset["area_improvement_pct_compare_vs_baseline"].mean():+.2f}%`, '
                    f'mean best-seen area `{pair_subset["best_seen_area_improvement_pct_compare_vs_baseline"].mean():+.2f}%`; '
                    f'runtime better/tied/worse `{runtime_faster}/{runtime_tied}/{runtime_slower}`, '
                    f'final area better/tied/worse `{area_better}/{area_tied}/{area_worse}`, '
                    f'best-seen better/tied/worse `{best_seen_better}/{best_seen_tied}/{best_seen_worse}`'
                )
        lines.append('')

    report_path = output_dir / 'termination_study_report.md'
    report_path.write_text('\n'.join(lines))
    return report_path


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for stale_plot in args.output_dir.glob('*_alpha_beta_sweep.png'):
        stale_plot.unlink(missing_ok=True)

    parsed_rows = []
    for log_path in discover_logs(args.logs_root, include_wout=args.include_wout):
        row = parse_log(log_path)
        if row is not None:
            parsed_rows.append(row)

    if not parsed_rows:
        raise SystemExit('No parseable termination-study logs were found.')

    df = deduplicate_runs(parsed_rows)
    df = add_scores(df, area_weight=args.area_weight, runtime_weight=args.runtime_weight)
    df = mark_pareto_optimal(df)
    df['label'] = df.apply(short_label, axis=1)
    parameter_summary = summarize_parameter_effects(df)
    best_by_budget = (
        df.sort_values(['benchmark', 'cnn_constraint', 'max_error', 'group_composite_score'])
        .groupby(['benchmark', 'cnn_constraint', 'max_error'], as_index=False)
        .first()
    )
    best_by_benchmark = (
        df.sort_values(['benchmark', 'composite_score'])
        .groupby(['benchmark'], as_index=False)
        .first()
    )

    runs_csv = args.output_dir / 'termination_study_runs.csv'
    rankings_csv = args.output_dir / 'termination_study_rankings.csv'
    group_rankings_csv = args.output_dir / 'termination_study_group_rankings.csv'
    best_by_budget_csv = args.output_dir / 'termination_study_best_by_budget.csv'
    best_by_benchmark_csv = args.output_dir / 'termination_study_best_by_benchmark.csv'
    pareto_csv = args.output_dir / 'termination_study_pareto.csv'
    parameter_summary_csv = args.output_dir / 'termination_study_parameter_summary.csv'
    mode_delta_csv = args.output_dir / 'termination_mode_deltas.csv'

    df.sort_values(['benchmark', 'composite_score']).to_csv(runs_csv, index=False)
    df[['benchmark', 'label', 'composite_score', 'final_area', 'runtime_seconds', 'area_reduction_pct', 'termination_mode', 'stop_reason', 'budget_status']].sort_values(
        ['benchmark', 'composite_score']
    ).to_csv(rankings_csv, index=False)
    df[['benchmark', 'cnn_constraint', 'max_error', 'label', 'group_composite_score', 'final_area', 'runtime_seconds', 'termination_mode', 'budget_status']].sort_values(
        ['benchmark', 'cnn_constraint', 'max_error', 'group_composite_score']
    ).to_csv(group_rankings_csv, index=False)
    best_by_budget[['benchmark', 'cnn_constraint', 'max_error', 'label', 'group_composite_score', 'final_area', 'runtime_seconds', 'termination_mode', 'budget_status']].to_csv(
        best_by_budget_csv,
        index=False,
    )
    best_by_benchmark[['benchmark', 'label', 'composite_score', 'final_area', 'runtime_seconds', 'termination_mode', 'budget_status']].to_csv(
        best_by_benchmark_csv,
        index=False,
    )
    df[df['is_pareto']].sort_values(['benchmark', 'composite_score']).to_csv(pareto_csv, index=False)
    parameter_summary.sort_values(['benchmark', 'parameter', 'value']).to_csv(parameter_summary_csv, index=False)
    build_mode_delta_table(df).to_csv(mode_delta_csv, index=False)

    plot_tradeoff(df, args.output_dir)
    for benchmark in sorted(df['benchmark'].unique()):
        plot_case_scorecard(df, benchmark, args.output_dir)
        plot_mode_comparison(df, benchmark, args.output_dir)
    report_path = write_report(df, args.output_dir)

    print(f'Parsed {len(df)} unique runs.')
    print(f'Wrote ranked run data to {runs_csv}')
    print(f'Wrote per-budget rankings to {group_rankings_csv}')
    print(f'Wrote best-per-budget summary to {best_by_budget_csv}')
    print(f'Wrote Pareto frontier data to {pareto_csv}')
    print(f'Wrote parameter summary to {parameter_summary_csv}')
    print(f'Wrote direct mode deltas to {mode_delta_csv}')
    print(f'Wrote markdown summary to {report_path}')


if __name__ == '__main__':
    main()
