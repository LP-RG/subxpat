from __future__ import annotations

import argparse
from datetime import datetime
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


def parse_log(log_path: Path) -> Dict[str, object] | None:
    text = _clean_text(log_path.read_text(errors='replace'))
    exit_code = _parse_exit_code(text)
    if exit_code not in (None, 0):
        return None

    specs = _parse_specs_block(text)
    exact = _parse_exact_candidate(text)
    candidate = _parse_last_candidate(text)
    if not specs or candidate is None:
        return None

    termination_mode = _infer_termination_mode(log_path, text, specs)
    benchmark = str(specs.get('exact_benchmark') or specs.get('current_benchmark') or log_path.stem)
    ceiling, bit_weight = _parse_stop_details(text)

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
        'iteration_count': _parse_last_iteration(text),
        'stop_reason': _parse_stop_reason(text),
        'stop_out_node': _parse_last_out_node(text),
        'termination_ceiling': ceiling,
        'bit_weight_at_stop': bit_weight,
        'runtime_seconds': _parse_runtime_seconds(text),
        'exit_code': exit_code,
        'final_verified_error_exact': _parse_final_verified_error(text),
        **(exact or {}),
        **candidate,
    }
    exact_area = row.get('exact_area')
    final_area = row.get('final_area')
    if isinstance(exact_area, (int, float)) and isinstance(final_area, (int, float)) and exact_area:
        row['area_reduction_pct'] = ((exact_area - final_area) / exact_area) * 100.0
    else:
        row['area_reduction_pct'] = None
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
        indices = list(group.index)
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
    return {'none': 'o', 'trivial': 's'}.get(_normalize_termination_mode(mode), 'D')


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


def build_mode_delta_table(df: pd.DataFrame) -> pd.DataFrame:
    case_keys = ['benchmark', 'cnn_constraint', 'max_error', 'alpha', 'beta', 'c_constant', 'threshold_array_idx']
    working = df.copy()
    working['case_label'] = working.apply(case_label, axis=1)

    keep_columns = case_keys + ['case_label', 'termination_mode', 'final_area', 'runtime_seconds', 'stop_reason']
    none_df = working[working['termination_mode'] == 'none'][keep_columns].rename(
        columns={
            'final_area': 'final_area_none',
            'runtime_seconds': 'runtime_seconds_none',
            'stop_reason': 'stop_reason_none',
        }
    )
    trivial_df = working[working['termination_mode'] == 'trivial'][keep_columns].rename(
        columns={
            'final_area': 'final_area_trivial',
            'runtime_seconds': 'runtime_seconds_trivial',
            'stop_reason': 'stop_reason_trivial',
        }
    )

    paired = none_df.drop(columns=['termination_mode']).merge(
        trivial_df.drop(columns=['termination_mode']),
        on=case_keys + ['case_label'],
        how='outer',
    )
    paired['delta_area_trivial_minus_none'] = paired['final_area_trivial'] - paired['final_area_none']
    paired['delta_runtime_trivial_minus_none'] = paired['runtime_seconds_trivial'] - paired['runtime_seconds_none']
    paired['area_better_mode'] = paired['delta_area_trivial_minus_none'].apply(_winner_mode)
    paired['runtime_better_mode'] = paired['delta_runtime_trivial_minus_none'].apply(_winner_mode)
    return paired.sort_values(['benchmark', 'cnn_constraint', 'max_error', 'alpha', 'beta', 'c_constant', 'threshold_array_idx']).reset_index(drop=True)


def plot_tradeoff(df: pd.DataFrame, output_dir: Path) -> Path:
    benchmarks = list(df['benchmark'].unique())
    ncols = 2 if len(benchmarks) > 1 else 1
    nrows = math.ceil(len(benchmarks) / ncols)
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(8 * ncols, 5 * nrows), squeeze=False)

    color_map = {'none': '#2d6a4f', 'trivial': '#c1121f', 'unknown': '#6b7280'}

    for ax, benchmark in zip(axes.flat, benchmarks):
        subset = df[df['benchmark'] == benchmark].sort_values('composite_score')
        plotted_any = False
        for _, row in subset.iterrows():
            if pd.isna(row['runtime_seconds']) or pd.isna(row['final_area']):
                continue
            color = color_map.get(_normalize_termination_mode(row['termination_mode']), '#6b7280')
            marker = 'X' if row['is_pareto'] else 'o'
            ax.scatter(row['runtime_seconds'], row['final_area'], color=color, marker=marker, s=100)
            plotted_any = True
            ax.annotate(
                f"{case_label(row)} [{row['termination_mode']}]",
                (row['runtime_seconds'], row['final_area']),
                fontsize=8,
                xytext=(5, 5),
                textcoords='offset points',
            )
        frontier = subset[subset['is_pareto']].dropna(subset=['runtime_seconds', 'final_area']).sort_values('runtime_seconds')
        if not frontier.empty:
            ax.plot(frontier['runtime_seconds'], frontier['final_area'], color='#f59e0b', linestyle='--', linewidth=1.6, alpha=0.9)
        ax.set_title(f'{benchmark}: runtime vs final area')
        ax.set_xlabel('Runtime (s)')
        ax.set_ylabel('Final area')
        ax.grid(alpha=0.3)
        if not plotted_any:
            ax.text(0.5, 0.5, 'No complete runtime data', ha='center', va='center', transform=ax.transAxes)

    for ax in axes.flat[len(benchmarks):]:
        ax.axis('off')

    handles = [
        plt.Line2D([0], [0], marker='o', color='w', label=mode, markerfacecolor=color, markersize=10)
        for mode, color in color_map.items()
        if mode in set(df['termination_mode'])
    ]
    fig.legend(handles=handles, loc='upper center', ncol=max(1, len(handles)))
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    output_path = output_dir / 'termination_tradeoff_by_benchmark.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_mode_comparison(df: pd.DataFrame, benchmark: str, output_dir: Path) -> Path | None:
    deltas = build_mode_delta_table(df)
    subset = deltas[deltas['benchmark'] == benchmark].copy()
    subset = subset.dropna(subset=['final_area_none', 'final_area_trivial', 'runtime_seconds_none', 'runtime_seconds_trivial'])
    if subset.empty:
        return None

    subset = subset.sort_values(['final_area_trivial', 'runtime_seconds_trivial', 'case_label']).reset_index(drop=True)
    y_positions = list(range(len(subset)))
    yticklabels = [
        f"{row.case_label}\narea:{row.area_better_mode} | time:{row.runtime_better_mode}"
        for row in subset.itertuples(index=False)
    ]

    fig, (ax_area, ax_runtime) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(16, max(5.0, len(subset) * 1.15)),
        sharey=True,
    )

    none_color = '#2d6a4f'
    trivial_color = '#c1121f'
    connector_color = '#94a3b8'
    tie_color = '#6b7280'

    for y_pos, row in zip(y_positions, subset.itertuples(index=False)):
        ax_area.plot(
            [row.final_area_none, row.final_area_trivial],
            [y_pos, y_pos],
            color=connector_color,
            linewidth=2,
            alpha=0.9,
        )
        ax_runtime.plot(
            [row.runtime_seconds_none, row.runtime_seconds_trivial],
            [y_pos, y_pos],
            color=connector_color,
            linewidth=2,
            alpha=0.9,
        )

        ax_area.scatter(row.final_area_none, y_pos, color=none_color, s=90, marker='o', zorder=3)
        ax_area.scatter(row.final_area_trivial, y_pos, color=trivial_color, s=90, marker='s', zorder=3)
        ax_runtime.scatter(row.runtime_seconds_none, y_pos, color=none_color, s=90, marker='o', zorder=3)
        ax_runtime.scatter(row.runtime_seconds_trivial, y_pos, color=trivial_color, s=90, marker='s', zorder=3)

        area_delta = row.delta_area_trivial_minus_none
        runtime_delta = row.delta_runtime_trivial_minus_none
        if pd.notna(area_delta):
            anchor = max(row.final_area_none, row.final_area_trivial)
            area_color = {'none': none_color, 'trivial': trivial_color, 'tie': tie_color}.get(row.area_better_mode, tie_color)
            ax_area.annotate(
                f'{area_delta:+.2f} ({row.area_better_mode})',
                (anchor, y_pos),
                fontsize=8,
                xytext=(6, 0),
                textcoords='offset points',
                va='center',
                color=area_color,
            )
        if pd.notna(runtime_delta):
            anchor = max(row.runtime_seconds_none, row.runtime_seconds_trivial)
            runtime_color = {'none': none_color, 'trivial': trivial_color, 'tie': tie_color}.get(row.runtime_better_mode, tie_color)
            ax_runtime.annotate(
                f'{runtime_delta:+.0f}s ({row.runtime_better_mode})',
                (anchor, y_pos),
                fontsize=8,
                xytext=(6, 0),
                textcoords='offset points',
                va='center',
                color=runtime_color,
            )

    ax_area.set_title(f'{benchmark}: final area by case')
    ax_area.set_xlabel('Final area')
    ax_area.set_ylabel('Parameter case')
    ax_area.set_yticks(y_positions)
    ax_area.set_yticklabels(yticklabels)
    ax_area.grid(axis='x', alpha=0.3)

    ax_runtime.set_title(f'{benchmark}: runtime by case')
    ax_runtime.set_xlabel('Runtime (s)')
    ax_runtime.grid(axis='x', alpha=0.3)

    legend_handles = [
        plt.Line2D([0], [0], marker='o', color='w', label='none', markerfacecolor=none_color, markersize=10),
        plt.Line2D([0], [0], marker='s', color='w', label='trivial', markerfacecolor=trivial_color, markersize=10),
        plt.Line2D([0], [0], color=tie_color, linewidth=2, label='delta label says winner per case'),
    ]
    fig.legend(handles=legend_handles, loc='upper center', ncol=3)
    fig.suptitle('Direct none vs trivial comparison with per-case winners', y=0.98, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    output_path = output_dir / f'{benchmark}_mode_comparison.png'
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path


def plot_case_scorecard(df: pd.DataFrame, benchmark: str, output_dir: Path) -> Path:
    subset = df[df['benchmark'] == benchmark].sort_values('composite_score').reset_index(drop=True)
    labels = [short_label(row) for _, row in subset.iterrows()]
    colors = subset['termination_mode'].map(lambda mode: {'none': '#2d6a4f', 'trivial': '#c1121f'}.get(_normalize_termination_mode(mode), '#6b7280'))

    fig, (ax_area, ax_runtime) = plt.subplots(
        nrows=2,
        ncols=1,
        figsize=(max(11, len(subset) * 1.25), 8),
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
    ax_runtime.set_xticklabels(labels, rotation=40, ha='right')

    legend_handles = [
        plt.Line2D([0], [0], marker='s', color='w', label='Pareto / non-dominated edge', markerfacecolor='#f59e0b', markersize=0, markeredgecolor='#f59e0b', linewidth=0),
        plt.Line2D([0], [0], marker='o', color='w', label='none', markerfacecolor='#2d6a4f', markersize=10),
        plt.Line2D([0], [0], marker='s', color='w', label='trivial', markerfacecolor='#c1121f', markersize=10),
    ]
    fig.legend(handles=legend_handles, loc='upper center', ncol=3)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

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
    parameters = ['termination_mode', 'cnn_constraint', 'max_error', 'alpha', 'beta', 'c_constant', 'threshold_array_idx']

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
    for benchmark, subset in df.groupby('benchmark'):
        ordered = subset.sort_values('composite_score')
        best = ordered.iloc[0]
        lines.append(f'## {benchmark}')
        lines.append('')
        lines.append(
            f'- Best composite score: `{short_label(best)}` '
            f'(area `{best.final_area:.4f}`, runtime `{_format_seconds(best.runtime_seconds)}`, '
            f'area reduction `{_format_percentage(best.area_reduction_pct)}`, stop `{best.stop_reason}`)'
        )
        area_best = subset.loc[subset['final_area'].idxmin()]
        runtime_best = subset.loc[subset['runtime_seconds'].idxmin()]
        lines.append(
            f'- Lowest area: `{short_label(area_best)}` '
            f'(area `{area_best.final_area:.4f}`, runtime `{_format_seconds(area_best.runtime_seconds)}`)'
        )
        lines.append(
            f'- Fastest run: `{short_label(runtime_best)}` '
            f'(runtime `{_format_seconds(runtime_best.runtime_seconds)}`, area `{runtime_best.final_area:.4f}`)'
        )
        for (constraint, max_error), group in subset.groupby(['cnn_constraint', 'max_error']):
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
