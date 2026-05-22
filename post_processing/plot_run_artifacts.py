from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"
MUTED = "#5a5047"

STATUS_COLORS = {
    "SAT": "#1f6d3a",
    "UNSAT": "#d24b40",
    "UNKNOWN": "#b7791f",
    "STOPPED": "#5b6472",
    "DOMINATED": "#7c3aed",
    "DUPLICATE_SUBGRAPH": "#6c7688",
    "NO_SUBGRAPH": "#475569",
}
STATUS_BACKGROUNDS = {
    "SAT": "#e8f4ec",
    "UNSAT": "#faece9",
    "UNKNOWN": "#fbf3e3",
    "STOPPED": "#eceff3",
    "DOMINATED": "#f0eafd",
    "DUPLICATE_SUBGRAPH": "#eceff3",
    "NO_SUBGRAPH": "#e9eef2",
}


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "savefig.facecolor": BG,
            "axes.facecolor": PANEL,
            "axes.edgecolor": "#8a7f73",
            "axes.labelcolor": TEXT,
            "axes.titlecolor": TEXT,
            "text.color": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "font.size": 10,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "legend.frameon": False,
            "grid.color": GRID,
            "grid.linestyle": "-",
            "grid.linewidth": 0.8,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create run-local plots and lightweight indexes for SubXPAT runs. "
            "Each completed run gets a plots/ folder; sweep/group folders get "
            "a group dashboard."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Run directories or sweep directories under benchmarking/generated.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Discover run directories below each provided path.",
    )
    parser.add_argument(
        "--plots-dir-name",
        default="plots",
        help="Name of the per-run/group plots directory (default: plots).",
    )
    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Create whatever plots are possible even if summary artifacts are missing.",
    )
    return parser.parse_args()


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def format_seconds(seconds: Any) -> str:
    if pd.isna(seconds):
        return "-"
    value = float(seconds)
    if value < 60.0:
        return f"{value:.0f}s"
    if value < 3600.0:
        return f"{value / 60.0:.1f}m"
    return f"{value / 3600.0:.2f}h"


def format_hours(hours: Any) -> str:
    if pd.isna(hours):
        return "-"
    value = float(hours)
    if value < (1.0 / 60.0):
        return f"{value * 3600.0:.0f}s"
    if value < 1.0:
        return f"{value * 60.0:.1f}m"
    return f"{value:.2f}h"


def format_float(value: Any, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def short_status(status: Any) -> str:
    text = str(status).upper()
    return {
        "SAT": "S",
        "UNSAT": "U",
        "UNKNOWN": "?",
        "DOMINATED": "D",
        "STOPPED": "stop",
        "DUPLICATE_SUBGRAPH": "dup",
        "NO_SUBGRAPH": "no-sub",
    }.get(text, text[:1])


def parse_grid_from_text(text: str) -> Optional[Tuple[int, int]]:
    match = re.search(r"_(?P<lpp>\d+)X(?P<ppo>\d+)_", text)
    if match is None:
        return None
    return int(match.group("lpp")), int(match.group("ppo"))


def safe_read_json(path: Optional[Path]) -> Dict[str, Any]:
    if path is None or not path.exists():
        return {}
    with path.open() as handle:
        return json.load(handle)


def safe_read_csv(path: Optional[Path]) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def first_existing(paths: Iterable[Optional[Path]]) -> Optional[Path]:
    for path in paths:
        if path is not None and path.exists():
            return path
    return None


def latest_file(directory: Path, pattern: str) -> Optional[Path]:
    matches = sorted(directory.glob(pattern))
    return matches[-1] if matches else None


def path_from_run_summary(run_dir: Path, column: str) -> Optional[Path]:
    summary_tsv = run_dir / "run_summary.tsv"
    if not summary_tsv.exists():
        return None
    try:
        frame = pd.read_csv(summary_tsv, sep="\t")
    except Exception:
        return None
    if frame.empty or column not in frame.columns:
        return None
    value = frame.iloc[-1][column]
    if pd.isna(value) or not str(value).strip():
        return None
    path = Path(str(value))
    return path if path.is_absolute() else run_dir / path


def resolve_artifacts(run_dir: Path) -> Dict[str, Optional[Path]]:
    artifacts_dir = run_dir / "artifacts"
    summary_json = first_existing(
        [
            path_from_run_summary(run_dir, "summary_json"),
            latest_file(artifacts_dir, "*_summary.json"),
            latest_file(run_dir, "*_summary.json"),
        ]
    )
    trace_csv = first_existing(
        [
            path_from_run_summary(run_dir, "trace_csv"),
            latest_file(artifacts_dir, "*_trace.csv"),
            latest_file(run_dir, "*_trace.csv"),
        ]
    )

    summary = safe_read_json(summary_json)
    grid_csv_candidates: List[Optional[Path]] = []
    raw_grid = summary.get("grid_csv")
    if raw_grid:
        grid_csv_candidates.append(run_dir / "artifacts" / Path(str(raw_grid)).name)
        grid_csv_candidates.append(run_dir / "workdir" / str(raw_grid))
        grid_csv_candidates.append(ROOT / str(raw_grid))
    grid_csv_candidates.append(latest_file(artifacts_dir, "grid_*.csv"))
    grid_csv_candidates.append(latest_file(run_dir, "grid_*.csv"))
    grid_csv = first_existing(grid_csv_candidates)

    return {
        "summary_json": summary_json,
        "trace_csv": trace_csv,
        "grid_csv": grid_csv,
    }


def is_run_dir(path: Path, include_incomplete: bool = False) -> bool:
    if (path / "run_summary.tsv").exists():
        return True
    if (path / "artifacts").exists() and latest_file(path / "artifacts", "*_summary.json"):
        return True
    return include_incomplete and (path / "terminal.out.log").exists()


def discover_run_dirs(paths: Sequence[Path], recursive: bool, include_incomplete: bool) -> List[Path]:
    run_dirs: List[Path] = []
    for raw_path in paths:
        path = resolve_path(raw_path)
        if is_run_dir(path, include_incomplete=include_incomplete):
            run_dirs.append(path)
        if recursive and path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.is_dir() and is_run_dir(child, include_incomplete=include_incomplete):
                    run_dirs.append(child)
    deduped: List[Path] = []
    seen = set()
    for run_dir in run_dirs:
        resolved = run_dir.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(run_dir)
    return deduped


def make_trace_table(trace: pd.DataFrame, summary: Dict[str, Any]) -> pd.DataFrame:
    if trace.empty:
        return pd.DataFrame()
    frame = trace.copy()
    frame["iteration"] = pd.to_numeric(frame["iteration"], errors="coerce")
    frame = frame.dropna(subset=["iteration"]).sort_values("iteration").reset_index(drop=True)
    frame["iteration"] = frame["iteration"].astype(int)

    if "runtime_elapsed_seconds" in frame.columns:
        frame["elapsed_seconds"] = pd.to_numeric(frame["runtime_elapsed_seconds"], errors="coerce")
    else:
        runtimes = pd.to_numeric(frame.get("iteration_runtime_seconds", pd.Series(dtype=float)), errors="coerce")
        frame["elapsed_seconds"] = runtimes.fillna(0).cumsum()
    if summary.get("iterations") is not None and summary.get("runtime_seconds") is not None:
        final_iter = int(summary["iterations"])
        frame.loc[frame["iteration"].eq(final_iter), "elapsed_seconds"] = float(summary["runtime_seconds"])
    frame["elapsed_seconds"] = frame["elapsed_seconds"].ffill()
    frame["elapsed_hours"] = frame["elapsed_seconds"] / 3600.0
    frame["elapsed_label"] = frame["elapsed_hours"].map(format_hours)

    best_area = pd.to_numeric(frame.get("best_area", pd.Series(dtype=float)), errors="coerce")
    run_best = pd.to_numeric(frame.get("run_best_area", pd.Series(dtype=float)), errors="coerce")
    frame["current_area"] = best_area.ffill()
    frame["run_best_area_filled"] = run_best.fillna(frame["current_area"]).ffill()
    if summary.get("best_seen_area") is not None:
        frame["run_best_area_filled"] = frame["run_best_area_filled"].fillna(float(summary["best_seen_area"]))
    frame["status"] = frame.get("status", pd.Series(["UNKNOWN"] * len(frame))).fillna("UNKNOWN")
    return frame


def make_grid_rows(grid: pd.DataFrame, trace_table: pd.DataFrame) -> pd.DataFrame:
    cell_rows = pd.DataFrame()
    if not grid.empty:
        cell_rows = grid.copy().reset_index(drop=True)
        cell_rows["source_row_index"] = range(1, len(cell_rows) + 1)
        cell_rows["iteration"] = pd.to_numeric(cell_rows["iteration"], errors="coerce")
        cell_rows = cell_rows.dropna(subset=["iteration"])
        cell_rows["iteration"] = cell_rows["iteration"].astype(int)
        cell_rows["runtime"] = pd.to_numeric(cell_rows.get("runtime", pd.Series(dtype=float)), errors="coerce")
        cell_rows["area"] = pd.to_numeric(cell_rows.get("area", pd.Series(dtype=float)), errors="coerce")
        cell_rows["status"] = cell_rows.get("status", pd.Series(["UNKNOWN"] * len(cell_rows))).fillna("UNKNOWN")
        cell_rows["cell"] = cell_rows.get("cell", pd.Series(["-"] * len(cell_rows))).fillna("-").astype(str)
        cell_rows["timeline_row_kind"] = "cell"

    trace_only_rows = pd.DataFrame()
    if not trace_table.empty:
        existing_iterations = set(cell_rows["iteration"].unique()) if not cell_rows.empty else set()
        trace_missing = trace_table[~trace_table["iteration"].isin(existing_iterations)].copy()
        if not trace_missing.empty:
            trace_only_rows = pd.DataFrame(
                {
                    "iteration": trace_missing["iteration"].astype(int),
                    "source_row_index": 0,
                    "status": trace_missing.get("status", pd.Series(["UNKNOWN"] * len(trace_missing))).fillna("UNKNOWN"),
                    "runtime": pd.to_numeric(
                        trace_missing.get("iteration_runtime_seconds", pd.Series(dtype=float)),
                        errors="coerce",
                    ),
                    "area": pd.to_numeric(trace_missing.get("best_area", pd.Series(dtype=float)), errors="coerce"),
                    "cell": trace_missing.get("selected_cell", pd.Series(["-"] * len(trace_missing))).fillna("-"),
                    "out_node": trace_missing.get("out_node", pd.Series([math.nan] * len(trace_missing))),
                    "current_area_after_row": pd.to_numeric(
                        trace_missing.get("current_area", pd.Series(dtype=float)),
                        errors="coerce",
                    ),
                    "timeline_row_kind": "trace",
                }
            )
            trace_only_rows["cell"] = trace_only_rows["cell"].replace({"": "-", "nan": "-"}).fillna("-").astype(str)

    rows = pd.concat([cell_rows, trace_only_rows], ignore_index=True, sort=False)
    if rows.empty:
        return pd.DataFrame()

    rows["source_row_index"] = pd.to_numeric(rows.get("source_row_index", pd.Series(dtype=float)), errors="coerce").fillna(0)
    rows = rows.sort_values(["iteration", "source_row_index", "timeline_row_kind"]).reset_index(drop=True)
    rows["row_index"] = range(1, len(rows) + 1)
    rows["runtime"] = pd.to_numeric(rows.get("runtime", pd.Series(dtype=float)), errors="coerce")
    rows["area"] = pd.to_numeric(rows.get("area", pd.Series(dtype=float)), errors="coerce")
    rows["status"] = rows.get("status", pd.Series(["UNKNOWN"] * len(rows))).fillna("UNKNOWN")
    rows["cell_label"] = rows.get("cell", pd.Series(["-"] * len(rows))).fillna("-").astype(str)
    rows["cell_runtime_label"] = rows["runtime"].map(format_seconds)
    rows["status_short"] = rows["status"].map(short_status)
    rows["row_area_label"] = rows["area"].map(lambda value: format_float(value, 1))
    if "current_area_after_row" not in rows.columns:
        rows["current_area_after_row"] = math.nan
    rows["current_area_after_row"] = pd.to_numeric(rows["current_area_after_row"], errors="coerce")
    rows["current_area_after_row"] = rows["current_area_after_row"].fillna(rows["area"].ffill()).ffill()
    rows["current_area_label"] = rows["current_area_after_row"].map(lambda value: format_float(value, 1))

    if not trace_table.empty:
        meta_columns = [
            column
            for column in (
                "iteration",
                "elapsed_label",
                "out_node",
                "ancestor_gate_count",
                "selected_subgraph_gate_count",
                "ancestor_coverage_ratio",
                "persistence_limit_used",
                "persistence_counter",
                "persistence_counter_after",
                "pareto_stagnation",
                "pareto_classification",
                "stop_reason",
            )
            if column in trace_table.columns
        ]
        trace_meta = trace_table[meta_columns].drop_duplicates("iteration")
        if "out_node" in rows.columns and "out_node" in trace_meta.columns:
            rows = rows.rename(columns={"out_node": "grid_out_node"})
            trace_meta = trace_meta.rename(columns={"out_node": "trace_out_node"})
        rows = rows.merge(trace_meta, on="iteration", how="left")
        if "trace_out_node" in rows.columns:
            rows["out_node"] = rows["trace_out_node"]
            if "grid_out_node" in rows.columns:
                rows["out_node"] = rows["out_node"].fillna(rows["grid_out_node"])

    rows["out_node_label"] = rows.get("out_node", pd.Series([math.nan] * len(rows))).map(
        lambda value: "-" if pd.isna(value) else f"o{int(value)}"
    )
    rows["subgraph_size_label"] = rows.apply(
        lambda row: "-"
        if pd.isna(row.get("selected_subgraph_gate_count")) or pd.isna(row.get("ancestor_gate_count"))
        else f"{int(row['selected_subgraph_gate_count'])}/{int(row['ancestor_gate_count'])}",
        axis=1,
    )
    rows["coverage_label"] = rows.get("ancestor_coverage_ratio", pd.Series([math.nan] * len(rows))).map(
        lambda value: "-" if pd.isna(value) else f"{float(value):.2f}"
    )
    rows["patience_label"] = rows.get("pareto_stagnation", pd.Series([math.nan] * len(rows))).map(
        lambda value: "-" if pd.isna(value) else str(int(value))
    )
    rows["persist_label"] = rows.apply(
        lambda row: "-"
        if pd.isna(row.get("persistence_limit_used"))
        else f"{int(row.get('persistence_counter', 0))}->{int(row.get('persistence_counter_after', 0))} L{int(row['persistence_limit_used'])}",
        axis=1,
    )
    if "elapsed_label" not in rows.columns:
        rows["elapsed_label"] = "-"
    return rows


def plot_area_story(trace_table: pd.DataFrame, summary: Dict[str, Any], output_path: Path) -> Optional[Path]:
    if trace_table.empty or trace_table["current_area"].dropna().empty:
        return None
    configure_style()
    fig, (ax_area, ax_counts) = plt.subplots(
        2,
        1,
        figsize=(14, 8.5),
        sharex=True,
        gridspec_kw={"height_ratios": [2.2, 1.0], "hspace": 0.08},
    )

    ax_area.plot(
        trace_table["iteration"],
        trace_table["current_area"],
        color="#b7791f",
        linewidth=2.2,
        marker="o",
        label="current accepted area",
    )
    if "run_best_area_filled" in trace_table.columns:
        ax_area.plot(
            trace_table["iteration"],
            trace_table["run_best_area_filled"],
            color="#1f6d3a",
            linewidth=1.8,
            linestyle="--",
            label="run-best area",
        )
    for status, subset in trace_table.groupby("status"):
        color = STATUS_COLORS.get(str(status), MUTED)
        ax_area.scatter(
            subset["iteration"],
            subset["current_area"],
            s=42,
            color=color,
            edgecolor="#fffaf5",
            linewidth=0.7,
            label=str(status),
            zorder=4,
        )

    best_iter = summary.get("best_seen_iteration")
    best_area = summary.get("best_seen_area")
    if best_iter is not None and best_area is not None:
        ax_area.scatter(
            [int(best_iter)],
            [float(best_area)],
            marker="*",
            s=220,
            color="#f59e0b",
            edgecolor="#7c2d12",
            linewidth=0.8,
            zorder=6,
            label="best",
        )
        ax_area.annotate(
            f"best i{int(best_iter)}\n{float(best_area):.1f}",
            (int(best_iter), float(best_area)),
            xytext=(10, 12),
            textcoords="offset points",
            fontsize=9,
            color="#7c2d12",
        )

    title_bits = [
        str(summary.get("exact_benchmark", "run")),
        f"beta={summary.get('beta', '-')}",
        f"aet={summary.get('max_error', '-')}",
        f"mode={summary.get('termination_mode', '-')}",
    ]
    grid = parse_grid_from_text(str(summary.get("grid_csv", "")))
    if grid is not None:
        title_bits.append(f"grid={grid[0]}x{grid[1]}")
    ax_area.set_title(" | ".join(title_bits))
    ax_area.set_ylabel("Area")
    ax_area.grid(True, axis="y", alpha=0.85)
    ax_area.legend(loc="upper right", ncol=3, fontsize=8)

    count_columns = [
        ("grid_sat_count", "#1f6d3a", "SAT"),
        ("grid_unsat_count", "#d24b40", "UNSAT"),
        ("grid_unknown_count", "#b7791f", "UNKNOWN"),
        ("grid_dominated_count", "#7c3aed", "DOMINATED"),
    ]
    bottom = pd.Series([0] * len(trace_table), index=trace_table.index, dtype=float)
    for column, color, label in count_columns:
        values = pd.to_numeric(trace_table.get(column, pd.Series([0] * len(trace_table))), errors="coerce").fillna(0)
        ax_counts.bar(trace_table["iteration"], values, bottom=bottom, color=color, alpha=0.82, label=label)
        bottom += values
    ax_counts.set_ylabel("Grid rows")
    ax_counts.set_xlabel("Iteration")
    ax_counts.grid(True, axis="y", alpha=0.65)
    ax_counts.legend(loc="upper right", ncol=4, fontsize=8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_persistence(trace_table: pd.DataFrame, output_path: Path) -> Optional[Path]:
    needed = {"ancestor_gate_count", "selected_subgraph_gate_count", "ancestor_coverage_ratio"}
    if trace_table.empty or not needed.issubset(trace_table.columns):
        return None
    if trace_table["ancestor_coverage_ratio"].dropna().empty:
        return None
    configure_style()
    fig, (ax_counts, ax_ratio) = plt.subplots(
        2,
        1,
        figsize=(14, 8),
        sharex=True,
        gridspec_kw={"height_ratios": [1.5, 1.0], "hspace": 0.08},
    )
    iterations = trace_table["iteration"]
    ancestors = pd.to_numeric(trace_table["ancestor_gate_count"], errors="coerce")
    selected = pd.to_numeric(trace_table["selected_subgraph_gate_count"], errors="coerce")
    ax_counts.bar(iterations, ancestors, color="#d8cab8", label="ancestor gates")
    ax_counts.bar(iterations, selected, color="#1f6d3a", label="selected subgraph gates")
    ax_counts.set_ylabel("Gate count")
    ax_counts.grid(True, axis="y", alpha=0.75)
    ax_counts.legend(loc="upper right")

    coverage = pd.to_numeric(trace_table["ancestor_coverage_ratio"], errors="coerce")
    limit = pd.to_numeric(trace_table.get("persistence_limit_used", pd.Series(dtype=float)), errors="coerce")
    counter_after = pd.to_numeric(trace_table.get("persistence_counter_after", pd.Series(dtype=float)), errors="coerce")
    ax_ratio.plot(iterations, coverage, marker="o", color="#b7791f", linewidth=2.0, label="coverage ratio")
    ax_limit = ax_ratio.twinx()
    ax_limit.step(iterations, limit, where="post", color="#475569", linewidth=1.7, label="persistence limit")
    ax_limit.scatter(iterations, counter_after, color="#7c3aed", s=30, label="counter after")
    ax_ratio.set_ylim(0, max(1.0, float(coverage.max(skipna=True)) * 1.1))
    ax_ratio.set_ylabel("Coverage")
    ax_limit.set_ylabel("Persistence")
    ax_ratio.set_xlabel("Iteration")
    ax_ratio.grid(True, axis="y", alpha=0.75)
    lines, labels = ax_ratio.get_legend_handles_labels()
    lines2, labels2 = ax_limit.get_legend_handles_labels()
    ax_ratio.legend(lines + lines2, labels + labels2, loc="upper right", ncol=3)
    ax_counts.set_title("Subgraph coverage and dynamic persistence")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_row_timeline(rows: pd.DataFrame, summary: Dict[str, Any], output_path: Path) -> Optional[Path]:
    if rows.empty or rows["current_area_after_row"].dropna().empty:
        return None
    configure_style()
    row_count = int(rows["row_index"].max())
    fig_width = max(16.0, min(42.0, 5.0 + (0.18 * row_count)))
    fig, (ax_plot, ax_notes) = plt.subplots(
        2,
        1,
        figsize=(fig_width, 12.8),
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 2.75], "hspace": 0.05},
    )

    spans = rows.groupby("iteration", as_index=False).agg(
        row_start=("row_index", "min"),
        row_end=("row_index", "max"),
    )
    for idx, span in spans.iterrows():
        fill = "#f6efe7" if idx % 2 == 0 else PANEL
        ax_plot.axvspan(span["row_start"] - 0.5, span["row_end"] + 0.5, facecolor=fill, alpha=0.32, zorder=0)
        ax_plot.axvline(span["row_end"] + 0.5, color="#b9ac9c", linewidth=0.8, alpha=0.65, zorder=1)

    ax_plot.step(
        rows["row_index"],
        rows["current_area_after_row"],
        where="post",
        color="#b7791f",
        linewidth=2.2,
        label="current accepted area after each row",
    )
    for status, subset in rows.groupby("status"):
        y_values = subset["area"].where(subset["status"].eq("SAT"), subset["current_area_after_row"])
        marker = {"SAT": "o", "UNSAT": "o", "UNKNOWN": "s", "DOMINATED": "D"}.get(str(status), "o")
        face = STATUS_COLORS.get(str(status), PANEL) if status == "SAT" else PANEL
        edge = "#ffffff" if status == "SAT" else STATUS_COLORS.get(str(status), TEXT)
        ax_plot.scatter(
            subset["row_index"],
            y_values,
            s=40,
            marker=marker,
            facecolor=face,
            edgecolor=edge,
            linewidth=0.9,
            label=str(status),
            zorder=4,
        )

    min_area = rows["current_area_after_row"].min(skipna=True)
    min_rows = rows[rows["current_area_after_row"].eq(min_area)]
    if not min_rows.empty:
        min_row = min_rows.iloc[0]
        ax_plot.scatter(
            [min_row["row_index"]],
            [min_row["current_area_after_row"]],
            s=190,
            marker="*",
            color="#f59e0b",
            edgecolor="#7c2d12",
            linewidth=0.8,
            zorder=6,
            label="minimum",
        )

    top_axis = ax_plot.twiny()
    top_axis.set_xlim(ax_plot.get_xlim())
    span_mids = (spans["row_start"] + spans["row_end"]) / 2.0
    top_axis.set_xticks(span_mids)
    top_axis.set_xticklabels([str(int(value)) for value in spans["iteration"]], fontsize=8)
    top_axis.set_xlabel("Iteration")

    title = f"{summary.get('exact_benchmark', 'run')}: row-by-row timeline"
    ax_plot.set_title(title)
    ax_plot.set_ylabel("Area")
    ax_plot.set_xlabel("Grid row index")
    ax_plot.grid(True, axis="y", alpha=0.85)
    ax_plot.legend(loc="upper right", ncol=3, fontsize=8)
    ax_plot.set_xlim(1, row_count)

    note_rows = [
        ("iter", "iteration"),
        ("elapsed", "elapsed_label"),
        ("cell", "cell_label"),
        ("result", "status_short"),
        ("patience", "patience_label"),
        ("cell time", "cell_runtime_label"),
        ("sub/anc", "subgraph_size_label"),
        ("out node", "out_node_label"),
        ("coverage", "coverage_label"),
        ("persist b->a L", "persist_label"),
        ("current area", "current_area_label"),
    ]
    ax_notes.set_xlim(0.5, row_count + 0.5)
    ax_notes.set_ylim(0, len(note_rows))
    ax_notes.axis("off")
    for note_index, (label, column) in enumerate(note_rows):
        y = len(note_rows) - note_index - 1
        ax_notes.text(-1.8, y + 0.5, label, ha="right", va="center", fontsize=9, fontweight="bold")
        for _, data in rows.iterrows():
            x = float(data["row_index"])
            base_fill = PANEL if int(x) % 2 else "#f4eee6"
            facecolor = STATUS_BACKGROUNDS.get(str(data["status"]), base_fill) if column == "status_short" else base_fill
            rect = Rectangle((x - 0.5, y), 1.0, 1.0, facecolor=facecolor, edgecolor=GRID, linewidth=0.75)
            ax_notes.add_patch(rect)
            rotation = 0 if column == "status_short" else 90
            fontsize = 6.1 if column in {"cell_label", "elapsed_label", "cell_runtime_label", "persist_label", "subgraph_size_label"} else 5.8
            color = STATUS_COLORS.get(str(data["status"]), TEXT) if column == "status_short" else TEXT
            ax_notes.text(x, y + 0.5, str(data.get(column, "-")), ha="center", va="center", fontsize=fontsize, rotation=rotation, color=color)

    fig.text(
        0.5,
        0.02,
        "Rows preserve grid exploration order within each iteration. sub/anc = selected subgraph gates / ancestor gates of the out node; coverage = sub/anc ratio.",
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    fig.text(
        0.5,
        0.005,
        "persist b->a L = persistence counter before->after, with dynamic limit L. Low coverage raises L, so the extractor may retry the same out node.",
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def run_record(run_dir: Path, summary: Dict[str, Any], trace_table: pd.DataFrame) -> Dict[str, Any]:
    grid = parse_grid_from_text(str(summary.get("grid_csv", "")))
    return {
        "run_dir": str(run_dir),
        "run": run_dir.name,
        "benchmark": summary.get("exact_benchmark"),
        "mode": summary.get("termination_mode"),
        "beta": summary.get("beta"),
        "aet": summary.get("max_error"),
        "alpha": summary.get("alpha"),
        "grid_lpp": None if grid is None else grid[0],
        "grid_ppo": None if grid is None else grid[1],
        "iterations": summary.get("iterations"),
        "best_iteration": summary.get("best_seen_iteration"),
        "final_iteration": summary.get("final_iteration"),
        "best_area": summary.get("best_seen_area"),
        "final_area": summary.get("final_area"),
        "runtime_hours": None if summary.get("runtime_seconds") is None else float(summary["runtime_seconds"]) / 3600.0,
        "best_runtime_hours": None if summary.get("best_seen_runtime_at_accept_seconds") is None else float(summary["best_seen_runtime_at_accept_seconds"]) / 3600.0,
        "stop_reason": summary.get("stop_reason"),
        "pareto_candidate_patience": summary.get("pareto_candidate_patience"),
        "dynamic_persistence": summary.get("dynamic_persistence"),
        "trace_rows": len(trace_table),
    }


def write_run_index(
    run_dir: Path,
    plots_dir: Path,
    record: Dict[str, Any],
    artifact_paths: Dict[str, Optional[Path]],
    generated: Sequence[Path],
) -> Path:
    index_path = plots_dir / "index.md"
    rel_generated = [path.name for path in generated]
    lines = [
        f"# {run_dir.name}",
        "",
        "## Summary",
        "",
        f"- Benchmark: `{record.get('benchmark')}`",
        f"- Mode: `{record.get('mode')}`",
        f"- beta/aet/alpha: `{record.get('beta')}` / `{record.get('aet')}` / `{record.get('alpha')}`",
        f"- grid: `{record.get('grid_lpp')}x{record.get('grid_ppo')}`",
        f"- best area: `{format_float(record.get('best_area'), 4)}` at iteration `{record.get('best_iteration')}`",
        f"- final area: `{format_float(record.get('final_area'), 4)}`",
        f"- runtime: `{format_hours(record.get('runtime_hours'))}`",
        f"- stop reason: `{record.get('stop_reason')}`",
        f"- dynamic persistence: `{record.get('dynamic_persistence')}`",
        "",
        "## Plots",
        "",
    ]
    lines.extend(f"- [{name}]({name})" for name in rel_generated)
    lines.extend(
        [
            "",
            "## Source Artifacts",
            "",
            f"- summary: `{artifact_paths.get('summary_json')}`",
            f"- trace: `{artifact_paths.get('trace_csv')}`",
            f"- grid: `{artifact_paths.get('grid_csv')}`",
            "",
        ]
    )
    index_path.write_text("\n".join(lines))
    return index_path


def plot_run(run_dir: Path, plots_dir_name: str, include_incomplete: bool) -> Optional[Dict[str, Any]]:
    artifacts = resolve_artifacts(run_dir)
    summary = safe_read_json(artifacts["summary_json"])
    trace = safe_read_csv(artifacts["trace_csv"])
    grid = safe_read_csv(artifacts["grid_csv"])
    if not summary and not include_incomplete:
        return None

    plots_dir = run_dir / plots_dir_name
    plots_dir.mkdir(parents=True, exist_ok=True)
    trace_table = make_trace_table(trace, summary)
    grid_rows = make_grid_rows(grid, trace_table)
    record = run_record(run_dir, summary, trace_table)
    pd.DataFrame([record]).to_csv(plots_dir / "run_metrics.csv", index=False)
    if not trace_table.empty:
        trace_table.to_csv(plots_dir / "trace_enriched.csv", index=False)
    if not grid_rows.empty:
        grid_rows.to_csv(plots_dir / "row_timeline.csv", index=False)

    generated: List[Path] = []
    for result in (
        plot_area_story(trace_table, summary, plots_dir / "area_story.png"),
        plot_persistence(trace_table, plots_dir / "persistence_coverage.png"),
        plot_row_timeline(grid_rows, summary, plots_dir / "row_timeline.png"),
    ):
        if result is not None:
            generated.append(result)
    write_run_index(run_dir, plots_dir, record, artifacts, generated)
    record["plots_dir"] = str(plots_dir)
    return record


def write_group_dashboard(group_dir: Path, records: Sequence[Dict[str, Any]], plots_dir_name: str) -> Optional[Path]:
    if not records:
        return None
    plots_dir = group_dir / plots_dir_name
    plots_dir.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(records).sort_values(["beta", "aet", "grid_lpp", "grid_ppo"], na_position="last")
    table.to_csv(plots_dir / "run_summary_table.csv", index=False)

    numeric = table.copy()
    numeric["runtime_hours"] = pd.to_numeric(numeric["runtime_hours"], errors="coerce")
    numeric["best_area"] = pd.to_numeric(numeric["best_area"], errors="coerce")
    if numeric["best_area"].dropna().empty:
        return plots_dir

    configure_style()
    fig, (ax_area, ax_runtime) = plt.subplots(2, 1, figsize=(15, 9), gridspec_kw={"height_ratios": [1.5, 1.0], "hspace": 0.28})
    labels = [
        f"b{row.beta}-e{row.aet}-{int(row.grid_lpp)}x{int(row.grid_ppo)}"
        if not pd.isna(row.grid_lpp) and not pd.isna(row.grid_ppo)
        else str(row.run)
        for row in numeric.itertuples()
    ]
    x_positions = range(len(numeric))
    colors = ["#1f6d3a" if int(row.grid_lpp or 0) == 3 else "#b7791f" for row in numeric.itertuples()]
    ax_area.bar(x_positions, numeric["best_area"], color=colors, alpha=0.85)
    ax_area.set_ylabel("Best area")
    ax_area.set_title(f"{group_dir.name}: best area and runtime by case")
    ax_area.grid(True, axis="y", alpha=0.75)
    ax_runtime.bar(x_positions, numeric["runtime_hours"], color="#6c7688", alpha=0.85)
    ax_runtime.set_ylabel("Runtime [h]")
    ax_runtime.set_xticks(list(x_positions))
    ax_runtime.set_xticklabels(labels, rotation=45, ha="right")
    ax_runtime.grid(True, axis="y", alpha=0.75)
    fig.savefig(plots_dir / "group_dashboard.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    matrix_plot = write_sweep_matrix_plot(numeric, plots_dir / "sweep_matrix.png")
    tradeoff_plot = write_tradeoff_plot(numeric, plots_dir / "area_runtime_tradeoff.png")

    index_lines = [
        f"# {group_dir.name}",
        "",
        "## Generated Files",
        "",
        "- [run_summary_table.csv](run_summary_table.csv)",
        "- [group_dashboard.png](group_dashboard.png)",
        *([] if matrix_plot is None else ["- [sweep_matrix.png](sweep_matrix.png)"]),
        *([] if tradeoff_plot is None else ["- [area_runtime_tradeoff.png](area_runtime_tradeoff.png)"]),
        "",
        "## Runs",
        "",
    ]
    for row in table.itertuples():
        run_path = Path(row.run_dir)
        rel = os.path.relpath(run_path / plots_dir_name / "index.md", plots_dir)
        index_lines.append(f"- [{row.run}]({rel})")
    (plots_dir / "index.md").write_text("\n".join(index_lines) + "\n")
    return plots_dir


def write_sweep_matrix_plot(table: pd.DataFrame, output_path: Path) -> Optional[Path]:
    required = {"beta", "aet", "grid_lpp", "grid_ppo", "best_area", "runtime_hours"}
    if not required.issubset(table.columns):
        return None
    frame = table.dropna(subset=list(required)).copy()
    if frame.empty:
        return None

    frame["beta"] = frame["beta"].astype(int)
    frame["aet"] = frame["aet"].astype(int)
    frame["grid_lpp"] = frame["grid_lpp"].astype(int)
    frame["grid_ppo"] = frame["grid_ppo"].astype(int)
    frame["grid_label"] = frame["grid_lpp"].astype(str) + "x" + frame["grid_ppo"].astype(str)
    frame["beta_grid"] = "b" + frame["beta"].astype(str) + " " + frame["grid_label"]

    ordered_columns = [
        f"b{beta} {grid}"
        for beta in sorted(frame["beta"].unique())
        for grid in sorted(frame.loc[frame["beta"] == beta, "grid_label"].unique())
    ]
    area_matrix = frame.pivot_table(index="aet", columns="beta_grid", values="best_area", aggfunc="first")
    runtime_matrix = frame.pivot_table(index="aet", columns="beta_grid", values="runtime_hours", aggfunc="first")
    area_matrix = area_matrix.reindex(columns=[col for col in ordered_columns if col in area_matrix.columns]).sort_index()
    runtime_matrix = runtime_matrix.reindex(columns=area_matrix.columns).sort_index()

    def grid_delta(metric: str) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        for (beta, aet), group in frame.groupby(["beta", "aet"]):
            values = {int(row.grid_lpp): float(getattr(row, metric)) for row in group.itertuples()}
            if 3 in values and 4 in values:
                rows.append({"beta": beta, "aet": aet, "delta": values[4] - values[3]})
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows).pivot_table(index="aet", columns="beta", values="delta", aggfunc="first").sort_index()

    delta_area = grid_delta("best_area")
    delta_runtime = grid_delta("runtime_hours")

    configure_style()
    fig, axes = plt.subplots(2, 2, figsize=(14, 8.5), gridspec_kw={"hspace": 0.38, "wspace": 0.24})

    def draw_heatmap(ax: plt.Axes, matrix: pd.DataFrame, title: str, cmap_name: str, fmt: str) -> None:
        if matrix.empty:
            ax.axis("off")
            ax.set_title(title)
            ax.text(0.5, 0.5, "no data", ha="center", va="center", transform=ax.transAxes)
            return
        cmap = plt.get_cmap(cmap_name).copy()
        cmap.set_bad("#eee8dd")
        image = ax.imshow(matrix.astype(float).values, aspect="auto", cmap=cmap)
        ax.set_title(title)
        ax.set_xticks(range(len(matrix.columns)))
        ax.set_xticklabels([str(col) for col in matrix.columns], rotation=35, ha="right")
        ax.set_yticks(range(len(matrix.index)))
        ax.set_yticklabels([f"e{int(idx)}" for idx in matrix.index])
        for y, (_, row) in enumerate(matrix.iterrows()):
            for x, value in enumerate(row):
                if pd.notna(value):
                    ax.text(x, y, fmt.format(float(value)), ha="center", va="center", fontsize=9, color=TEXT)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)

    draw_heatmap(axes[0, 0], area_matrix, "Best area (lower is better)", "YlGn_r", "{:.1f}")
    draw_heatmap(axes[0, 1], runtime_matrix, "Runtime [h] (lower is better)", "YlOrRd", "{:.1f}")
    draw_heatmap(axes[1, 0], delta_area, "Area delta: 4x4 - 3x3", "RdYlGn_r", "{:+.1f}")
    draw_heatmap(axes[1, 1], delta_runtime, "Runtime delta [h]: 4x4 - 3x3", "RdYlGn_r", "{:+.1f}")
    fig.suptitle(f"{output_path.parent.parent.name}: sweep comparison matrix", fontsize=17, fontweight="bold", y=0.98)
    fig.text(0.5, 0.02, "Negative area delta means 4x4 found a smaller circuit; positive runtime delta means 4x4 was slower.", ha="center", color=MUTED)
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_tradeoff_plot(table: pd.DataFrame, output_path: Path) -> Optional[Path]:
    required = {"beta", "aet", "grid_lpp", "grid_ppo", "best_area", "runtime_hours"}
    if not required.issubset(table.columns):
        return None
    frame = table.dropna(subset=list(required)).copy()
    if frame.empty:
        return None
    frame["beta"] = frame["beta"].astype(int)
    frame["aet"] = frame["aet"].astype(int)
    frame["grid_lpp"] = frame["grid_lpp"].astype(int)
    frame["grid_ppo"] = frame["grid_ppo"].astype(int)
    frame["best_area"] = pd.to_numeric(frame["best_area"], errors="coerce")
    frame["runtime_hours"] = pd.to_numeric(frame["runtime_hours"], errors="coerce")
    frame = frame.dropna(subset=["best_area", "runtime_hours"])
    if frame.empty:
        return None

    configure_style()
    fig, ax = plt.subplots(figsize=(10.5, 6.5))
    colors = {250: "#b7791f", 300: "#2f6f9f", 350: "#1f6d3a"}
    markers = {(3, 3): "o", (4, 4): "s"}
    for row in frame.sort_values(["aet", "beta", "grid_lpp"]).itertuples():
        marker = markers.get((row.grid_lpp, row.grid_ppo), "D")
        ax.scatter(
            row.runtime_hours,
            row.best_area,
            s=115,
            marker=marker,
            color=colors.get(row.aet, "#6c7688"),
            edgecolor="#2b2724",
            linewidth=0.8,
            alpha=0.92,
        )
        ax.annotate(
            f"b{row.beta} {row.grid_lpp}x{row.grid_ppo}",
            (row.runtime_hours, row.best_area),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8.5,
        )
    ax.set_title(f"{output_path.parent.parent.name}: area/runtime tradeoff")
    ax.set_xlabel("Runtime [h]")
    ax.set_ylabel("Best area")
    ax.grid(True, alpha=0.8)
    area_best = frame.loc[frame["best_area"].idxmin()]
    ax.scatter([area_best.runtime_hours], [area_best.best_area], s=260, facecolors="none", edgecolors="#d24b40", linewidths=2.0)
    ax.annotate("best area", (area_best.runtime_hours, area_best.best_area), xytext=(10, -18), textcoords="offset points", color="#d24b40", fontsize=9)

    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=colors[aet], markeredgecolor="#2b2724", markersize=8, label=f"AET {aet}")
        for aet in sorted(colors)
    ]
    handles.extend(
        [
            plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#8a8a8a", markeredgecolor="#2b2724", markersize=8, label="3x3"),
            plt.Line2D([0], [0], marker="s", color="none", markerfacecolor="#8a8a8a", markeredgecolor="#2b2724", markersize=8, label="4x4"),
        ]
    )
    ax.legend(handles=handles, loc="best")
    fig.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output_path


def common_parent(paths: Sequence[Path]) -> Path:
    if not paths:
        return ROOT
    resolved = [path.resolve() for path in paths]
    try:
        return Path(os.path.commonpath([str(path) for path in resolved]))
    except ValueError:
        return resolved[0].parent


def main() -> None:
    args = parse_args()
    run_dirs = discover_run_dirs(args.paths, recursive=args.recursive, include_incomplete=args.include_incomplete)
    if not run_dirs:
        raise SystemExit("No run directories found.")

    records: List[Dict[str, Any]] = []
    for run_dir in run_dirs:
        record = plot_run(run_dir, args.plots_dir_name, include_incomplete=args.include_incomplete)
        if record is not None:
            records.append(record)
            print(f"Wrote run plots to {record['plots_dir']}")

    roots = [resolve_path(path) for path in args.paths]
    group_dir = roots[0] if len(roots) == 1 and roots[0].is_dir() and not is_run_dir(roots[0]) else common_parent(run_dirs)
    group_plots = write_group_dashboard(group_dir, records, args.plots_dir_name)
    if group_plots is not None:
        print(f"Wrote group dashboard to {group_plots}")


if __name__ == "__main__":
    main()
