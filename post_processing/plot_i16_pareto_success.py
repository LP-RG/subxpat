from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

CASE_SPECS = (
    {
        "key": "none",
        "label": "None",
        "trace_csv": Path(
            "output/report/termination_study/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608_trace.csv"
        ),
        "grid_csv": Path(
            "output/report/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608.csv"
        ),
        "summary_json": Path(
            "output/report/termination_study/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608_summary.json"
        ),
        "color": "#6c7688",
    },
    {
        "key": "predictor",
        "label": "Predictor",
        "trace_csv": Path(
            "output/report/termination_study/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpredictor_mode0_omax2_imax4_constnever_Sop1_time20260420:100130_trace.csv"
        ),
        "grid_csv": Path(
            "output/report/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpredictor_mode0_omax2_imax4_constnever_Sop1_time20260420:100130.csv"
        ),
        "summary_json": Path(
            "output/report/termination_study/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpredictor_mode0_omax2_imax4_constnever_Sop1_time20260420:100130_summary.json"
        ),
        "color": "#1d4ed8",
    },
    {
        "key": "pareto_annealed",
        "label": "Pareto Annealed",
        "trace_csv": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_annealed_isolated_20260424/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_annealed_mode0_omax2_imax4_constnever_Sop1_time20260424:083517_trace.csv"
        ),
        "grid_csv": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_annealed_isolated_20260424/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_annealed_mode0_omax2_imax4_constnever_Sop1_time20260424:083517.csv"
        ),
        "summary_json": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_annealed_isolated_20260424/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_annealed_mode0_omax2_imax4_constnever_Sop1_time20260424:083517_summary.json"
        ),
        "color": "#b7791f",
    },
    {
        "key": "pareto_p3",
        "label": "Pareto Patience 3",
        "trace_csv": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_patience3_20260426_081734/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_mode0_omax2_imax4_constnever_Sop1_time20260426:081744_trace.csv"
        ),
        "grid_csv": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_patience3_20260426_081734/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_mode0_omax2_imax4_constnever_Sop1_time20260426:081744.csv"
        ),
        "summary_json": Path(
            "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_patience3_20260426_081734/artifacts/"
            "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termpareto_mode0_omax2_imax4_constnever_Sop1_time20260426:081744_summary.json"
        ),
        "color": "#1f6d3a",
    },
)

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
}
STATUS_BACKGROUNDS = {
    "SAT": "#e8f4ec",
    "UNSAT": "#faece9",
    "UNKNOWN": "#fbf3e3",
    "STOPPED": "#eceff3",
    "DOMINATED": "#f0eafd",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate focused i16 pareto-success plots: a mode-comparison dashboard, "
            "a detailed patience-3 iteration story, and a row-by-row timeline for the "
            "pareto-annealed grid CSV."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/iteration_area_trajectories_20260424"),
        help="Directory for generated CSVs and plots.",
    )
    return parser.parse_args()


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


def _resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _clean_cell(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _format_elapsed_label(hours: float) -> str:
    if pd.isna(hours):
        return "-"
    if hours < (1.0 / 60.0):
        return f"{hours * 3600.0:.0f}s"
    if hours < 1.0:
        return f"{hours * 60.0:.1f}m"
    return f"{hours:.2f}h"


def _format_seconds_label(seconds: object) -> str:
    if pd.isna(seconds):
        return "-"
    value = float(seconds)
    if value < 60.0:
        return f"{value:.0f}s"
    if value < 3600.0:
        return f"{value / 60.0:.1f}m"
    return f"{value / 3600.0:.2f}h"


def _format_float_label(value: object, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def _status_short_label(status: object) -> str:
    text = str(status).upper()
    return {
        "SAT": "S",
        "UNSAT": "U",
        "UNKNOWN": "?",
        "DOMINATED": "D",
        "STOPPED": "stop",
    }.get(text, text[:1])


def _lighten(hex_color: str, weight: float = 0.55) -> str:
    color = hex_color.lstrip("#")
    red = int(color[0:2], 16)
    green = int(color[2:4], 16)
    blue = int(color[4:6], 16)
    red = int(red + ((255 - red) * weight))
    green = int(green + ((255 - green) * weight))
    blue = int(blue + ((255 - blue) * weight))
    return f"#{red:02x}{green:02x}{blue:02x}"


def _operand_bits_from_benchmark(benchmark: str) -> int | None:
    match = re.search(r"_i(?P<bits>\d+)_o\d+$", benchmark)
    if match is None:
        return None
    input_bits = int(match.group("bits"))
    if input_bits <= 0 or input_bits % 2 != 0:
        return None
    return input_bits // 2


def _generate_zone_aet_thresholds(input_count: int, base_error: int, beta: int, alpha: int) -> list[int]:
    domain_size = 2 ** max(1, input_count // 2)
    half = (domain_size - 1) // 2
    zone_size = max(1, beta)
    num_steps = max(1, math.ceil(domain_size / zone_size))
    thresholds: list[int] = []

    for zone_i in range(num_steps):
        row_start = zone_i * zone_size
        row_end = min(domain_size - 1, ((zone_i + 1) * zone_size) - 1)
        for zone_j in range(num_steps):
            col_start = zone_j * zone_size
            col_end = min(domain_size - 1, ((zone_j + 1) * zone_size) - 1)

            zone_max = 0
            for input_one_value in range(row_start, row_end + 1):
                for input_two_value in range(col_start, col_end + 1):
                    numerator = (abs(input_two_value - half) * alpha) + input_one_value
                    score = max(1, math.ceil(numerator / zone_size))
                    zone_max = max(zone_max, score * base_error)
            thresholds.append(zone_max)

    return thresholds


def _zone_aet_ceiling(benchmark: str, base_error: int, beta: int, alpha: int) -> int | None:
    operand_bits = _operand_bits_from_benchmark(benchmark)
    if operand_bits is None:
        return None
    thresholds = _generate_zone_aet_thresholds(
        input_count=operand_bits * 2,
        base_error=base_error,
        beta=beta,
        alpha=alpha,
    )
    unique_levels = sorted(set(int(value) for value in thresholds))
    if not unique_levels:
        return None
    return unique_levels[-1]


def load_case(case_spec: dict[str, object]) -> dict[str, object]:
    trace = pd.read_csv(_resolve(Path(case_spec["trace_csv"]))).sort_values("iteration").reset_index(drop=True)
    grid = pd.read_csv(_resolve(Path(case_spec["grid_csv"]))).reset_index(drop=True)
    summary = json.loads(_resolve(Path(case_spec["summary_json"])).read_text())

    runtime_by_iteration = (
        grid.groupby("iteration", as_index=False)["runtime"]
        .sum()
        .rename(columns={"runtime": "iteration_runtime_seconds_grid"})
    )
    runtime_by_iteration["elapsed_runtime_seconds_grid"] = runtime_by_iteration[
        "iteration_runtime_seconds_grid"
    ].cumsum()

    count_rows: list[dict[str, object]] = []
    for iteration, group in grid.groupby("iteration", sort=True):
        counts = group["status"].value_counts()
        count_rows.append(
            {
                "iteration": int(iteration),
                "grid_sat_count_computed": int(counts.get("SAT", 0)),
                "grid_unsat_count_computed": int(counts.get("UNSAT", 0)),
                "grid_unknown_count_computed": int(counts.get("UNKNOWN", 0)),
                "grid_dominated_count_computed": int(counts.get("DOMINATED", 0)),
            }
        )
    grid_counts = pd.DataFrame(count_rows)

    row_data: list[dict[str, object]] = []
    for _, trace_row in trace.iterrows():
        iteration = int(trace_row["iteration"])
        grid_rows = grid[grid["iteration"] == iteration].copy()

        selected_cell = _clean_cell(trace_row.get("selected_cell"))
        if selected_cell is not None:
            primary_cell = selected_cell
        elif not grid_rows.empty:
            primary_cell = str(grid_rows.iloc[-1]["cell"])
        else:
            primary_cell = None

        row = trace_row.to_dict()
        row["selected_cell"] = selected_cell
        row["primary_cell"] = primary_cell
        row_data.append(row)

    iteration_df = pd.DataFrame(row_data)
    iteration_df = iteration_df.merge(runtime_by_iteration, on="iteration", how="left")
    iteration_df = iteration_df.merge(grid_counts, on="iteration", how="left")

    if "iteration_runtime_seconds" in iteration_df.columns:
        iteration_df["iteration_runtime_seconds"] = iteration_df["iteration_runtime_seconds"].fillna(
            iteration_df["iteration_runtime_seconds_grid"]
        )
    else:
        iteration_df["iteration_runtime_seconds"] = iteration_df["iteration_runtime_seconds_grid"]

    if "runtime_elapsed_seconds" in iteration_df.columns:
        iteration_df["elapsed_runtime_seconds"] = iteration_df["runtime_elapsed_seconds"].fillna(
            iteration_df["elapsed_runtime_seconds_grid"]
        )
    else:
        iteration_df["elapsed_runtime_seconds"] = iteration_df["elapsed_runtime_seconds_grid"]

    final_iteration = int(summary["iterations"])
    iteration_df.loc[
        iteration_df["iteration"] == final_iteration, "elapsed_runtime_seconds"
    ] = float(summary["runtime_seconds"])
    iteration_df["elapsed_runtime_seconds"] = iteration_df["elapsed_runtime_seconds"].ffill()
    iteration_df["elapsed_runtime_hours"] = iteration_df["elapsed_runtime_seconds"] / 3600.0

    count_columns = (
        "grid_sat_count",
        "grid_unsat_count",
        "grid_unknown_count",
        "grid_dominated_count",
    )
    for column in count_columns:
        computed = f"{column}_computed"
        if column in iteration_df.columns:
            iteration_df[column] = iteration_df[column].fillna(iteration_df[computed])
        else:
            iteration_df[column] = iteration_df[computed]
        iteration_df[column] = iteration_df[column].fillna(0).astype(int)

    if "grid_timeout_count" in iteration_df.columns:
        iteration_df["grid_timeout_count"] = iteration_df["grid_timeout_count"].fillna(0).astype(int)
    else:
        iteration_df["grid_timeout_count"] = 0

    iteration_df["accepted"] = iteration_df["status"].eq("SAT")
    iteration_df["out_node"] = iteration_df["out_node"].fillna(0).astype(int)
    iteration_df["current_area"] = iteration_df["best_area"].ffill()
    iteration_df["elapsed_label"] = iteration_df["elapsed_runtime_hours"].map(_format_elapsed_label)
    iteration_df["out_label"] = iteration_df["out_node"].map(lambda value: f"o{value}")
    iteration_df["status_label"] = iteration_df["status"].fillna("UNKNOWN")
    iteration_df["cell_label"] = iteration_df["primary_cell"].fillna("-")
    iteration_df["grid_summary"] = (
        iteration_df["grid_sat_count"].astype(str)
        + "/"
        + iteration_df["grid_unsat_count"].astype(str)
        + "/"
        + iteration_df["grid_unknown_count"].astype(str)
        + "/"
        + iteration_df["grid_dominated_count"].astype(str)
    )
    iteration_df["best_age_label"] = iteration_df["best_seen_iteration_age"].map(
        lambda value: "-" if pd.isna(value) else str(int(value))
    )
    iteration_df["pareto_stop_label"] = iteration_df["pareto_stop_probability"].map(
        lambda value: "-" if pd.isna(value) else f"{float(value):.2f}"
    )
    iteration_df["area_label"] = iteration_df["current_area"].map(lambda value: _format_float_label(value, digits=1))

    stop_iteration = int(iteration_df["iteration"].max())
    best_iteration = int(summary.get("best_seen_iteration", summary.get("final_iteration", stop_iteration)))
    best_runtime_seconds = float(
        summary.get(
            "best_seen_runtime_at_accept_seconds",
            summary.get("final_runtime_at_accept_seconds", summary["runtime_seconds"]),
        )
    )
    final_area = float(summary["final_area"])
    best_area = float(summary.get("best_seen_area", final_area))
    runtime_seconds = float(summary["runtime_seconds"])
    tail_seconds = max(0.0, runtime_seconds - best_runtime_seconds)

    metrics = {
        "key": str(case_spec["key"]),
        "label": str(case_spec["label"]),
        "termination_mode": str(summary["termination_mode"]),
        "benchmark": str(summary["exact_benchmark"]),
        "beta": int(summary["beta"]),
        "max_error": int(summary["max_error"]),
        "iterations": int(summary["iterations"]),
        "best_iteration": best_iteration,
        "final_iteration": int(summary.get("final_iteration", best_iteration)),
        "stop_iteration": stop_iteration,
        "final_area": final_area,
        "best_area": best_area,
        "runtime_seconds": runtime_seconds,
        "runtime_hours": runtime_seconds / 3600.0,
        "best_runtime_seconds": best_runtime_seconds,
        "best_runtime_hours": best_runtime_seconds / 3600.0,
        "tail_seconds": tail_seconds,
        "tail_hours": tail_seconds / 3600.0,
        "tail_share_pct": 100.0 * tail_seconds / runtime_seconds if runtime_seconds else 0.0,
        "stop_reason": str(summary["stop_reason"]),
        "stop_out_node": summary.get("stop_out_node"),
        "pareto_candidate_patience": summary.get("pareto_candidate_patience"),
        "pareto_stagnation": summary.get("pareto_stagnation"),
    }

    return {
        "spec": case_spec,
        "summary": summary,
        "trace": iteration_df,
        "grid": grid,
        "metrics": metrics,
    }


def build_derived_trivial_case(reference_case: dict[str, object]) -> dict[str, object]:
    summary = dict(reference_case["summary"])
    trace = reference_case["trace"].copy()

    ceiling = _zone_aet_ceiling(
        benchmark=str(summary["exact_benchmark"]),
        base_error=int(summary["max_error"]),
        beta=int(summary["beta"]),
        alpha=int(summary["alpha"]),
    )
    if ceiling is None:
        raise ValueError("Could not derive trivial ceiling for the i16 dashboard.")

    stop_candidates = trace[trace["bit_weight"] > ceiling].copy()
    if stop_candidates.empty:
        raise ValueError("No trivial stop point found in the reference none trace.")

    stop_iteration = int(stop_candidates.iloc[0]["iteration"])
    stop_out_node = int(stop_candidates.iloc[0]["out_node"])
    previous_rows = trace[trace["iteration"] < stop_iteration].copy()
    if previous_rows.empty:
        raise ValueError("Derived trivial stop occurs before any accepted iterations.")

    stop_runtime_seconds = float(previous_rows.iloc[-1]["elapsed_runtime_seconds"])
    current_area = float(previous_rows.iloc[-1]["current_area"])
    best_runtime_seconds = float(summary["best_seen_runtime_at_accept_seconds"])
    best_iteration = int(summary["best_seen_iteration"])

    stop_row = stop_candidates.iloc[0].copy()
    stop_row["status"] = "STOPPED"
    stop_row["status_label"] = "STOPPED"
    stop_row["accepted"] = False
    stop_row["best_area"] = pd.NA
    stop_row["current_area"] = current_area
    stop_row["elapsed_runtime_seconds"] = stop_runtime_seconds
    stop_row["elapsed_runtime_hours"] = stop_runtime_seconds / 3600.0
    stop_row["elapsed_label"] = _format_elapsed_label(stop_runtime_seconds / 3600.0)
    stop_row["iteration_runtime_seconds"] = 0.0
    stop_row["grid_sat_count"] = 0
    stop_row["grid_unsat_count"] = 0
    stop_row["grid_unknown_count"] = 0
    stop_row["grid_dominated_count"] = 0
    stop_row["grid_timeout_count"] = 0
    stop_row["grid_summary"] = "0/0/0/0"
    stop_row["cell_label"] = "-"
    stop_row["primary_cell"] = None
    stop_row["selected_cell"] = None
    stop_row["termination_mode"] = "trivial"
    stop_row["pareto_stop_probability"] = pd.NA
    stop_row["pareto_stop_label"] = "-"

    derived_trace = pd.concat([previous_rows, pd.DataFrame([stop_row])], ignore_index=True)
    derived_trace["termination_mode"] = "trivial"

    metrics = {
        "key": "trivial_derived",
        "label": "Trivial",
        "termination_mode": "trivial",
        "benchmark": str(summary["exact_benchmark"]),
        "beta": int(summary["beta"]),
        "max_error": int(summary["max_error"]),
        "iterations": stop_iteration,
        "best_iteration": best_iteration,
        "final_iteration": best_iteration,
        "stop_iteration": stop_iteration,
        "final_area": current_area,
        "best_area": current_area,
        "runtime_seconds": stop_runtime_seconds,
        "runtime_hours": stop_runtime_seconds / 3600.0,
        "best_runtime_seconds": best_runtime_seconds,
        "best_runtime_hours": best_runtime_seconds / 3600.0,
        "tail_seconds": max(0.0, stop_runtime_seconds - best_runtime_seconds),
        "tail_hours": max(0.0, stop_runtime_seconds - best_runtime_seconds) / 3600.0,
        "tail_share_pct": (
            100.0 * max(0.0, stop_runtime_seconds - best_runtime_seconds) / stop_runtime_seconds
            if stop_runtime_seconds
            else 0.0
        ),
        "stop_reason": "trivial_termination",
        "stop_out_node": stop_out_node,
        "pareto_candidate_patience": None,
        "pareto_stagnation": None,
        "termination_ceiling": ceiling,
    }

    return {
        "spec": {
            "key": "trivial_derived",
            "label": "Trivial",
            "color": "#9a3412",
        },
        "summary": summary,
        "trace": derived_trace,
        "grid": pd.DataFrame(),
        "metrics": metrics,
    }


def build_dashboard_table(case_data: list[dict[str, object]]) -> pd.DataFrame:
    rows = [dict(case["metrics"]) for case in case_data]
    df = pd.DataFrame(rows)
    none_runtime = float(df.loc[df["key"] == "none", "runtime_hours"].iloc[0])
    df["runtime_saved_vs_none_hours"] = none_runtime - df["runtime_hours"]
    df["runtime_saved_vs_none_pct"] = (
        100.0 * (none_runtime - df["runtime_hours"]) / none_runtime if none_runtime else 0.0
    )
    df["same_final_area_as_none"] = df["final_area"].eq(df.loc[df["key"] == "none", "final_area"].iloc[0])
    df["same_best_area_as_none"] = df["best_area"].eq(df.loc[df["key"] == "none", "best_area"].iloc[0])
    return df


def _draw_iteration_table(
    ax: plt.Axes,
    df: pd.DataFrame,
    row_specs: list[tuple[str, str]],
) -> None:
    iteration_count = int(df["iteration"].max())
    row_count = len(row_specs)

    ax.set_xlim(0.5, iteration_count + 0.5)
    ax.set_ylim(0, row_count)
    ax.axis("off")

    for row_index, (label, column) in enumerate(row_specs):
        y = row_count - row_index - 1
        ax.text(
            0.18,
            y + 0.5,
            label,
            ha="right",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=TEXT,
        )
        for _, data in df.iterrows():
            x = float(data["iteration"])
            base_fill = PANEL if int(x) % 2 else "#f4eee6"
            facecolor = base_fill
            if column == "status_label":
                facecolor = STATUS_BACKGROUNDS.get(str(data["status"]), base_fill)
            elif column in {"cell_label", "area_label"} and bool(data["accepted"]):
                facecolor = "#eef7f0"

            rect = Rectangle(
                (x - 0.5, y),
                1.0,
                1.0,
                facecolor=facecolor,
                edgecolor=GRID,
                linewidth=0.8,
            )
            ax.add_patch(rect)

            color = STATUS_COLORS.get(str(data["status"]), TEXT) if column == "status_label" else TEXT
            ax.text(
                x,
                y + 0.5,
                str(data[column]),
                ha="center",
                va="center",
                fontsize=7.4,
                color=color,
            )


def plot_pareto_iteration_story(case: dict[str, object], output_path: Path) -> Path:
    configure_style()
    df = case["trace"].copy()
    metrics = dict(case["metrics"])

    iteration_count = int(df["iteration"].max())
    fig_width = max(15.0, 3.0 + (0.72 * iteration_count))
    fig, (ax_plot, ax_notes) = plt.subplots(
        2,
        1,
        figsize=(fig_width, 10.8),
        sharex=True,
        gridspec_kw={"height_ratios": [3.2, 2.2], "hspace": 0.05},
    )

    accepted = df[df["accepted"]].copy()
    stalled = df[~df["accepted"]].copy()

    best_iteration = int(metrics["best_iteration"])
    stop_iteration = int(metrics["stop_iteration"])
    best_row = df[df["iteration"] == best_iteration].iloc[0]
    stop_row = df[df["iteration"] == stop_iteration].iloc[0]

    ax_plot.axvspan(
        best_iteration,
        stop_iteration,
        facecolor="#f8ddc7",
        alpha=0.35,
        zorder=0,
        label="tail after best area",
    )
    ax_plot.step(
        df["iteration"],
        df["current_area"],
        where="post",
        color=case["spec"]["color"],
        linewidth=2.5,
        alpha=0.98,
        label="current area",
        zorder=2,
    )
    ax_plot.scatter(
        accepted["iteration"],
        accepted["current_area"],
        s=62,
        color=STATUS_COLORS["SAT"],
        edgecolor="#ffffff",
        linewidth=0.9,
        label="accepted SAT iteration",
        zorder=4,
    )
    if not stalled.empty:
        stalled_colors = stalled["status"].map(lambda status: STATUS_COLORS.get(str(status), TEXT))
        ax_plot.scatter(
            stalled["iteration"],
            stalled["current_area"],
            s=58,
            facecolor=PANEL,
            edgecolor=stalled_colors,
            linewidth=1.3,
            label="non-accepted iteration",
            zorder=4,
        )

    ax_plot.scatter(
        [best_row["iteration"]],
        [best_row["current_area"]],
        s=190,
        marker="*",
        color="#f59e0b",
        edgecolor="#7c2d12",
        linewidth=0.9,
        zorder=6,
        label="global minimum",
    )
    ax_plot.scatter(
        [stop_row["iteration"]],
        [stop_row["current_area"]],
        s=120,
        marker="^",
        color="#7c2d12",
        edgecolor="#fff7ed",
        linewidth=0.8,
        zorder=6,
        label="stop iteration",
    )
    ax_plot.axvline(best_iteration, color="#9a3412", linewidth=1.2, linestyle=":", alpha=0.85, zorder=1)
    ax_plot.axvline(stop_iteration, color="#7c2d12", linewidth=1.2, linestyle="--", alpha=0.85, zorder=1)

    for _, row in df.iterrows():
        if pd.isna(row["current_area"]):
            continue
        status_color = STATUS_COLORS.get(str(row["status"]), TEXT)
        ax_plot.annotate(
            str(int(row["iteration"])),
            (row["iteration"], row["current_area"]),
            xytext=(0, 8 if row["accepted"] else -12),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=8,
            color=status_color,
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "#fffaf5",
                "edgecolor": "none",
                "alpha": 0.82,
            },
        )

    success_text = (
        "Success pattern:\n"
        f"same best/final area {metrics['best_area']:.4f}\n"
        f"stops at i{stop_iteration} after best-age 3\n"
        f"tail after best area: {metrics['tail_hours']:.2f}h"
    )
    ax_plot.text(
        0.985,
        0.04,
        success_text,
        transform=ax_plot.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=TEXT,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#fff7ed",
            "edgecolor": "#e8c7a6",
            "linewidth": 0.8,
        },
    )

    ax_plot.set_title(
        "mul_i16_o16 pareto patience=3: iteration story\n"
        "notes add elapsed time, rewritten out node, result, representative cell, S/U/?/D counts, best-age, and pareto stop probability"
    )
    ax_plot.set_ylabel("Current area (area units)")
    ax_plot.set_xlim(1, iteration_count)
    ax_plot.set_xticks(range(1, iteration_count + 1))
    ax_plot.grid(True, axis="both", alpha=0.8)
    ax_plot.set_axisbelow(True)

    status_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="None",
            markersize=7,
            markerfacecolor=STATUS_BACKGROUNDS.get(status, PANEL),
            markeredgecolor=color,
            markeredgewidth=1.2,
            label=status,
        )
        for status, color in STATUS_COLORS.items()
        if status in {"SAT", "UNSAT", "UNKNOWN", "STOPPED"}
    ]
    ax_plot.legend(
        handles=[
            Line2D([0], [0], color=case["spec"]["color"], linewidth=2.5, label="current area"),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="None",
                markersize=7,
                markerfacecolor=STATUS_COLORS["SAT"],
                markeredgecolor="#ffffff",
                markeredgewidth=0.9,
                label="accepted SAT iteration",
            ),
            Line2D([0], [0], marker="*", linestyle="None", markersize=12, color="#f59e0b", label="global minimum"),
            Line2D([0], [0], marker="^", linestyle="None", markersize=9, color="#7c2d12", label="stop iteration"),
            Line2D([0], [0], color="#9a3412", linewidth=1.2, linestyle=":", label="best-area iteration"),
            Line2D([0], [0], color="#7c2d12", linewidth=1.2, linestyle="--", label="pareto stop"),
            *status_handles,
        ],
        loc="upper right",
        ncol=2,
    )

    row_specs = [
        ("time", "elapsed_label"),
        ("out", "out_label"),
        ("result", "status_label"),
        ("cell", "cell_label"),
        ("S/U/?/D", "grid_summary"),
        ("best-age", "best_age_label"),
        ("p-stop", "pareto_stop_label"),
    ]
    _draw_iteration_table(ax_notes, df, row_specs)
    ax_notes.set_xlabel("Iteration")

    fig.text(
        0.5,
        0.02,
        "The shaded band shows the tail after the global minimum. Non-SAT iterations keep the last accepted area on the main line so the plateau shows time spent without improving the design.",
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )

    fig.subplots_adjust(left=0.055, right=0.995, top=0.92, bottom=0.12, hspace=0.06)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_success_dashboard(case_data: list[dict[str, object]], dashboard_df: pd.DataFrame, output_path: Path) -> Path:
    configure_style()
    fig = plt.figure(figsize=(15.5, 10.2))
    grid_spec = fig.add_gridspec(2, 1, height_ratios=[3.1, 2.0], hspace=0.28)
    ax_curve = fig.add_subplot(grid_spec[0, 0])
    ax_bar = fig.add_subplot(grid_spec[1, 0])

    for case in case_data:
        metrics = dict(case["metrics"])
        df = case["trace"].copy()
        color = str(case["spec"]["color"])
        accepted = df[df["accepted"]].copy()
        best_row = df[df["iteration"] == metrics["best_iteration"]].iloc[0]
        stop_row = df[df["iteration"] == metrics["stop_iteration"]].iloc[0]

        ax_curve.step(
            df["elapsed_runtime_hours"],
            df["current_area"],
            where="post",
            color=color,
            linewidth=2.4,
            label=str(case["spec"]["label"]),
            zorder=2,
        )
        ax_curve.scatter(
            accepted["elapsed_runtime_hours"],
            accepted["current_area"],
            s=42,
            facecolor=color,
            edgecolor="#ffffff",
            linewidth=0.8,
            zorder=4,
        )
        if pd.notna(best_row["elapsed_runtime_hours"]) and pd.notna(best_row["current_area"]):
            ax_curve.scatter(
                [best_row["elapsed_runtime_hours"]],
                [best_row["current_area"]],
                s=140,
                marker="*",
                color="#f59e0b",
                edgecolor="#7c2d12",
                linewidth=0.7,
                zorder=6,
            )
            ax_curve.annotate(
                f"best i{metrics['best_iteration']}",
                (best_row["elapsed_runtime_hours"], best_row["current_area"]),
                xytext=(0, -14),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=color,
                bbox={"boxstyle": "round,pad=0.15", "facecolor": "#fffaf5", "edgecolor": "none", "alpha": 0.85},
            )
        if pd.notna(stop_row["elapsed_runtime_hours"]) and pd.notna(stop_row["current_area"]):
            ax_curve.scatter(
                [stop_row["elapsed_runtime_hours"]],
                [stop_row["current_area"]],
                s=88,
                marker="^",
                color=color,
                edgecolor="#fff7ed",
                linewidth=0.8,
                zorder=6,
            )
            ax_curve.annotate(
                f"stop i{metrics['stop_iteration']}",
                (stop_row["elapsed_runtime_hours"], stop_row["current_area"]),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color=color,
                bbox={"boxstyle": "round,pad=0.15", "facecolor": "#fffaf5", "edgecolor": "none", "alpha": 0.85},
            )

    pareto_p3 = dashboard_df[dashboard_df["key"] == "pareto_p3"].iloc[0]
    ax_curve.text(
        0.985,
        0.04,
        (
            "Why patience=3 worked:\n"
            f"same final area {pareto_p3['final_area']:.4f}\n"
            f"{pareto_p3['runtime_saved_vs_none_hours']:.2f}h saved vs none\n"
            f"{pareto_p3['runtime_saved_vs_none_pct']:.1f}% runtime reduction"
        ),
        transform=ax_curve.transAxes,
        ha="right",
        va="bottom",
        fontsize=9,
        color=TEXT,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": "#eef7f0",
            "edgecolor": "#b7d9c2",
            "linewidth": 0.8,
        },
    )
    ax_curve.set_title(
        "mul_i16_o16: new pareto patience=3 preserves the same area but cuts the long tail"
    )
    ax_curve.set_xlabel("Elapsed runtime (hours)")
    ax_curve.set_ylabel("Current area (area units)")
    ax_curve.grid(True, axis="both", alpha=0.8)
    ax_curve.legend(loc="upper right", ncol=2)

    order = ["none", "trivial_derived", "pareto_p3"]
    ordered_df = dashboard_df.set_index("key").loc[order].reset_index()
    bar_labels = [label for label in ordered_df["label"]]
    y_positions = list(range(len(ordered_df)))
    colors = {str(case["spec"]["key"]): str(case["spec"]["color"]) for case in case_data}

    ax_bar.set_title("Runtime split: time to best area plus dead tail after the best area")
    for idx, row in ordered_df.iterrows():
        color = colors[str(row["key"])]
        tail_color = _lighten(color, 0.62)
        ax_bar.barh(idx, row["best_runtime_hours"], color=color, height=0.56)
        ax_bar.barh(idx, row["tail_hours"], left=row["best_runtime_hours"], color=tail_color, height=0.56)
        ax_bar.text(
            row["runtime_hours"] + 0.4,
            idx,
            f"{row['runtime_hours']:.2f}h total | {row['stop_reason']}",
            va="center",
            ha="left",
            fontsize=9,
            color=TEXT,
        )
        ax_bar.text(
            row["best_runtime_hours"] / 2.0,
            idx,
            f"{row['best_runtime_hours']:.2f}h",
            va="center",
            ha="center",
            fontsize=8,
            color="#ffffff",
        )
        if row["tail_hours"] > 0.35:
            ax_bar.text(
                row["best_runtime_hours"] + (row["tail_hours"] / 2.0),
                idx,
                f"{row['tail_hours']:.2f}h tail",
                va="center",
                ha="center",
                fontsize=8,
                color=TEXT,
            )

    ax_bar.set_yticks(y_positions)
    ax_bar.set_yticklabels(bar_labels)
    ax_bar.set_xlabel("Runtime (hours)")
    ax_bar.grid(True, axis="x", alpha=0.8)
    ax_bar.invert_yaxis()
    ax_bar.legend(
        handles=[
            Rectangle((0, 0), 1, 1, facecolor="#6c7688", edgecolor="none", label="time until best area"),
            Rectangle((0, 0), 1, 1, facecolor="#d8e3d2", edgecolor="none", label="tail after best area"),
        ],
        loc="lower right",
    )

    fig.subplots_adjust(left=0.10, right=0.98, top=0.94, bottom=0.08)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def build_row_timeline_tables(case: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    grid = case["grid"].copy().reset_index(drop=True)
    trace = case["trace"].copy()

    grid["source_row_index"] = range(1, len(grid) + 1)
    # The raw CSV interleaves iterations; sort by iteration while preserving the
    # original within-iteration order so the timeline reads in iteration order.
    grid = grid.sort_values(["iteration", "source_row_index"]).reset_index(drop=True)
    grid["row_index"] = range(1, len(grid) + 1)
    grid["current_area_after_row"] = grid["area"].ffill()

    iteration_spans = (
        grid.groupby("iteration", as_index=False)
        .agg(row_start=("row_index", "min"), row_end=("row_index", "max"))
        .copy()
    )
    covered_iterations = set(int(value) for value in iteration_spans["iteration"].tolist())
    next_row_index = int(iteration_spans["row_end"].max()) + 1 if not iteration_spans.empty else 1
    extra_spans: list[dict[str, object]] = []
    extra_rows: list[dict[str, object]] = []
    for _, trace_row in trace.sort_values("iteration").iterrows():
        iteration = int(trace_row["iteration"])
        if iteration in covered_iterations:
            continue
        extra_spans.append(
            {
                "iteration": iteration,
                "row_start": next_row_index,
                "row_end": next_row_index,
            }
        )
        extra_rows.append(
            {
                "row_index": next_row_index,
                "source_row_index": pd.NA,
                "iteration": iteration,
                "cell": trace_row.get("primary_cell"),
                "status": trace_row["status"],
                "runtime": 0.0,
                "area": pd.NA,
                "out_node": trace_row["out_node"],
                "current_area_after_row": trace_row["current_area"],
            }
        )
        next_row_index += 1
    if extra_spans:
        iteration_spans = pd.concat([iteration_spans, pd.DataFrame(extra_spans)], ignore_index=True)
    iteration_spans["row_mid"] = (iteration_spans["row_start"] + iteration_spans["row_end"]) / 2.0
    iteration_spans["row_span_label"] = iteration_spans.apply(
        lambda row: str(int(row["row_start"]))
        if int(row["row_start"]) == int(row["row_end"])
        else f"{int(row['row_start'])}-{int(row['row_end'])}",
        axis=1,
    )
    iteration_spans = iteration_spans.sort_values("row_start").reset_index(drop=True)

    iteration_meta = trace.merge(iteration_spans, on="iteration", how="left")
    iteration_meta["area_label"] = iteration_meta["current_area"].map(lambda value: _format_float_label(value, digits=1))

    export_rows = grid[
        [
            "row_index",
            "source_row_index",
            "iteration",
            "cell",
            "status",
            "runtime",
            "area",
            "out_node",
            "current_area_after_row",
        ]
    ].copy()
    if extra_rows:
        export_rows = pd.concat([export_rows, pd.DataFrame(extra_rows)], ignore_index=True)
    export_rows = export_rows.sort_values("row_index").reset_index(drop=True)
    export_rows = export_rows.merge(
        iteration_spans[["iteration", "row_start", "row_end", "row_mid", "row_span_label"]],
        on="iteration",
        how="left",
    )
    export_rows["cell_label"] = export_rows["cell"].fillna("-").astype(str)
    export_rows["cell_runtime_label"] = export_rows["runtime"].map(_format_seconds_label)
    export_rows["status_short"] = export_rows["status"].map(_status_short_label)
    export_rows["row_area_label"] = export_rows["area"].map(lambda value: _format_float_label(value, digits=1))
    export_rows["current_area_label"] = export_rows["current_area_after_row"].map(
        lambda value: _format_float_label(value, digits=1)
    )
    export_rows["cell_event_label"] = (
        export_rows["cell_label"]
        + " "
        + export_rows["status_short"]
        + " "
        + export_rows["cell_runtime_label"]
    )

    return export_rows, iteration_meta


def plot_annealed_row_timeline(
    row_df: pd.DataFrame,
    iteration_meta: pd.DataFrame,
    output_path: Path,
) -> Path:
    configure_style()
    row_df = row_df.copy()
    if "elapsed_label" not in row_df.columns:
        elapsed_by_iteration = (
            iteration_meta[["iteration", "elapsed_label"]]
            .drop_duplicates("iteration")
            .set_index("iteration")["elapsed_label"]
        )
        row_df["elapsed_label"] = row_df["iteration"].map(elapsed_by_iteration)

    row_count = int(row_df["row_index"].max())

    fig_width = max(18.0, 4.5 + (0.12 * row_count))
    fig, (ax_plot, ax_notes) = plt.subplots(
        2,
        1,
        figsize=(fig_width, 12.0),
        sharex=True,
        gridspec_kw={"height_ratios": [3.2, 2.25], "hspace": 0.05},
    )

    for idx, row in iteration_meta.iterrows():
        fill = "#f6efe7" if idx % 2 == 0 else PANEL
        ax_plot.axvspan(row["row_start"] - 0.5, row["row_end"] + 0.5, facecolor=fill, alpha=0.32, zorder=0)

    ax_plot.step(
        row_df["row_index"],
        row_df["current_area_after_row"],
        where="post",
        color="#b7791f",
        linewidth=2.3,
        label="current accepted area after each row",
        zorder=2,
    )

    sat_rows = row_df[row_df["status"] == "SAT"].copy()
    non_sat_rows = row_df[row_df["status"] != "SAT"].copy()

    ax_plot.scatter(
        sat_rows["row_index"],
        sat_rows["area"],
        s=44,
        color=STATUS_COLORS["SAT"],
        edgecolor="#ffffff",
        linewidth=0.7,
        label="SAT row",
        zorder=4,
    )
    for status, marker in (("UNSAT", "o"), ("UNKNOWN", "s"), ("DOMINATED", "D")):
        subset = non_sat_rows[non_sat_rows["status"] == status].copy()
        if subset.empty:
            continue
        ax_plot.scatter(
            subset["row_index"],
            subset["current_area_after_row"],
            s=34,
            marker=marker,
            facecolor=PANEL,
            edgecolor=STATUS_COLORS.get(status, TEXT),
            linewidth=1.0,
            label=f"{status} row",
            zorder=4,
        )

    min_area = float(row_df["current_area_after_row"].min())
    min_row = row_df[row_df["current_area_after_row"] == min_area].iloc[0]
    stop_row = row_df.iloc[-1]

    ax_plot.scatter(
        [min_row["row_index"]],
        [min_row["current_area_after_row"]],
        s=190,
        marker="*",
        color="#f59e0b",
        edgecolor="#7c2d12",
        linewidth=0.8,
        zorder=6,
        label="global minimum",
    )
    ax_plot.scatter(
        [stop_row["row_index"]],
        [stop_row["current_area_after_row"]],
        s=110,
        marker="^",
        color="#7c2d12",
        edgecolor="#fff7ed",
        linewidth=0.8,
        zorder=6,
        label="stop row",
    )

    for _, row in sat_rows.iterrows():
        if pd.isna(row["area"]):
            continue
        offset_y = 9 if int(row["iteration"]) % 2 else -14
        ax_plot.annotate(
            f"i{int(row['iteration'])}\n{row['area']:.1f}",
            (row["row_index"], row["area"]),
            xytext=(0, offset_y),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=7.2,
            color=STATUS_COLORS["SAT"],
            bbox={
                "boxstyle": "round,pad=0.15",
                "facecolor": "#fffaf5",
                "edgecolor": "none",
                "alpha": 0.85,
            },
        )

    timeout_rows = row_df[row_df["status"] == "UNKNOWN"].copy()
    for _, row in timeout_rows.iterrows():
        if pd.isna(row["current_area_after_row"]):
            continue
        ax_plot.annotate(
            f"{row['cell_label']}\n{row['cell_runtime_label']}",
            (row["row_index"], row["current_area_after_row"]),
            xytext=(0, 13),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=6.8,
            color=STATUS_COLORS["UNKNOWN"],
            bbox={
                "boxstyle": "round,pad=0.12",
                "facecolor": "#fffaf5",
                "edgecolor": "none",
                "alpha": 0.82,
            },
        )

    for _, row in iteration_meta.iterrows():
        ax_plot.axvline(row["row_end"] + 0.5, color="#b9ac9c", linewidth=0.8, alpha=0.65, zorder=1)

    top_axis = ax_plot.twiny()
    top_axis.set_xlim(ax_plot.get_xlim())
    top_axis.set_xticks(iteration_meta["row_mid"])
    top_axis.set_xticklabels([str(int(value)) for value in iteration_meta["iteration"]], fontsize=8)
    top_axis.set_xlabel("Iteration")
    top_axis.tick_params(axis="x", pad=2)

    ax_plot.set_title(
        "mul_i16_o16 pareto-annealed: row-by-row area timeline from the grid CSV\n"
        "bottom axis is iteration-sorted timeline row index, top axis is iteration, and vertical dividers show iteration boundaries"
    )
    ax_plot.set_ylabel("Area (area units)")
    ax_plot.set_xlabel("Grid row index")
    ax_plot.grid(True, axis="y", alpha=0.8)
    ax_plot.set_axisbelow(True)
    ax_plot.set_xlim(1, row_count)

    ax_plot.legend(loc="upper right", ncol=2)

    note_rows = [
        ("iter", "iteration"),
        ("elapsed", "elapsed_label"),
        ("cell", "cell_label"),
        ("result", "status_short"),
        ("cell time", "cell_runtime_label"),
        ("row area", "row_area_label"),
        ("current area", "current_area_label"),
    ]
    ax_notes.set_xlim(0.5, row_count + 0.5)
    ax_notes.set_ylim(0, len(note_rows))
    ax_notes.axis("off")

    for row_index, (label, column) in enumerate(note_rows):
        y = len(note_rows) - row_index - 1
        ax_notes.text(
            -2.2,
            y + 0.5,
            label,
            ha="right",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=TEXT,
        )
        for _, data in row_df.iterrows():
            x = float(data["row_index"])
            base_fill = PANEL if int(x) % 2 else "#f4eee6"
            facecolor = base_fill
            if column == "status_short":
                facecolor = STATUS_BACKGROUNDS.get(str(data["status"]), base_fill)
            elif column in {"row_area_label", "current_area_label"} and str(data["status"]) == "SAT":
                facecolor = "#eef7f0"

            rect = Rectangle(
                (x - 0.5, y),
                1.0,
                1.0,
                facecolor=facecolor,
                edgecolor=GRID,
                linewidth=0.8,
            )
            ax_notes.add_patch(rect)
            color = STATUS_COLORS.get(str(data["status"]), TEXT) if column == "status_short" else TEXT
            rotation = 0 if column == "status_short" else 90
            fontsize = 6.3 if column in {"cell_label", "cell_runtime_label", "elapsed_label"} else 5.9
            ax_notes.text(
                x,
                y + 0.5,
                str(data[column]),
                ha="center",
                va="center",
                fontsize=fontsize,
                color=color,
                rotation=rotation,
            )

    fig.text(
        0.5,
        0.02,
        "Rows are sorted by iteration while preserving their original order inside each iteration. The lower panel is cell-level: every grid row shows elapsed cumulative time, explored cell, result, per-cell runtime, row area, and current accepted area. UNKNOWN markers on the plot show the timeout cell and runtime.",
        ha="center",
        va="bottom",
        fontsize=9,
        color=MUTED,
    )

    fig.subplots_adjust(left=0.07, right=0.995, top=0.92, bottom=0.10, hspace=0.05)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    case_data = [load_case(case_spec) for case_spec in CASE_SPECS]
    none_case = next(case for case in case_data if case["spec"]["key"] == "none")
    pareto_case = next(case for case in case_data if case["spec"]["key"] == "pareto_p3")
    annealed_case = next(case for case in case_data if case["spec"]["key"] == "pareto_annealed")
    trivial_case = build_derived_trivial_case(none_case)

    dashboard_cases = [none_case, trivial_case, pareto_case]
    dashboard_df = build_dashboard_table(dashboard_cases)

    dashboard_csv = output_dir / "mul_i16_o16_pareto_success_dashboard.csv"
    dashboard_png = output_dir / "mul_i16_o16_pareto_success_dashboard.png"
    dashboard_df.to_csv(dashboard_csv, index=False)
    plot_success_dashboard(dashboard_cases, dashboard_df, dashboard_png)

    pareto_story_csv = output_dir / "mul_i16_o16_pareto_iteration_story_b64_e350.csv"
    pareto_story_png = output_dir / "mul_i16_o16_pareto_iteration_story_b64_e350.png"
    pareto_case["trace"].to_csv(pareto_story_csv, index=False)
    plot_pareto_iteration_story(pareto_case, pareto_story_png)

    row_df, iteration_meta = build_row_timeline_tables(annealed_case)
    annealed_timeline_csv = output_dir / "mul_i16_o16_pareto_annealed_row_timeline.csv"
    annealed_timeline_png = output_dir / "mul_i16_o16_pareto_annealed_row_timeline.png"
    main_annealed_timeline_png = output_dir / "mul_i16_o16_main_pareto_annealed_row_timeline.png"
    row_export = row_df.merge(
        iteration_meta[
            [
                "iteration",
                "out_label",
                "status_label",
                "grid_summary",
                "elapsed_label",
                "area_label",
            ]
        ],
        on="iteration",
        how="left",
    )
    row_export.to_csv(annealed_timeline_csv, index=False)
    plot_annealed_row_timeline(row_df, iteration_meta, annealed_timeline_png)
    plot_annealed_row_timeline(row_df, iteration_meta, main_annealed_timeline_png)

    print(f"Wrote dashboard CSV to {dashboard_csv}")
    print(f"Wrote dashboard plot to {dashboard_png}")
    print(f"Wrote pareto story CSV to {pareto_story_csv}")
    print(f"Wrote pareto story plot to {pareto_story_png}")
    print(f"Wrote annealed row timeline CSV to {annealed_timeline_csv}")
    print(f"Wrote annealed row timeline plot to {annealed_timeline_png}")
    print(f"Wrote main annealed row timeline plot to {main_annealed_timeline_png}")


if __name__ == "__main__":
    main()
