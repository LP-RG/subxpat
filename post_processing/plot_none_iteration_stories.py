from __future__ import annotations

import argparse
import json
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

DEFAULT_LOG_PATHS = (
    Path("benchmarking/generated/zone_aet_i8_adaptive_guard_20260411_rerun/05_b4_a2_e12_none_r01.log"),
    Path("benchmarking/generated/zone_aet_i10_adaptive_guard_20260411_rerun/05_b4_a2_e12_none_r01.log"),
    Path("benchmarking/generated/zone_aet_i16_singlecase_350_b64_modes_20260419/01_b64_a2_e350_none_r01.log"),
)

GRID_PATH_RE = re.compile(r"^path = '(?P<grid_path>output/report/[^']+\.csv)'$", re.MULTILINE)

BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"
LINE = "#6c7688"
ACCEPTED = "#1f6d3a"

STATUS_COLORS = {
    "SAT": "#1f6d3a",
    "UNSAT": "#d24b40",
    "UNKNOWN": "#b7791f",
    "STOPPED": "#5b6472",
    "DUPLICATE_SUBGRAPH": "#7c3aed",
    "NO_SUBGRAPH": "#8b5cf6",
}
STATUS_BACKGROUNDS = {
    "SAT": "#e8f4ec",
    "UNSAT": "#faece9",
    "UNKNOWN": "#fbf3e3",
    "STOPPED": "#eceff3",
    "DUPLICATE_SUBGRAPH": "#f0eafd",
    "NO_SUBGRAPH": "#efe8fd",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate annotated iteration-story plots for selected none runs, showing "
            "time, out node, result status, representative cell, and S/U/?/D counts."
        )
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        action="append",
        default=None,
        help="Repeatable run log path. Defaults to representative none runs for mul_i8_o8, mul_i10_o10, and mul_i16_o16.",
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
    if hours < (1.0 / 60.0):
        return f"{hours * 3600.0:.0f}s"
    if hours < 1.0:
        return f"{hours * 60.0:.1f}m"
    return f"{hours:.2f}h"


def _discover_case_from_log(log_path: Path) -> dict[str, object]:
    resolved_log = _resolve(log_path)
    text = resolved_log.read_text(errors="replace")
    match = GRID_PATH_RE.search(text)
    if match is None:
        raise SystemExit(f"Could not find grid CSV path in {resolved_log}")

    grid_csv = _resolve(Path(match.group("grid_path")))
    summary_stem = grid_csv.stem
    summary_json = ROOT / "output/report/termination_study" / f"{summary_stem}_summary.json"
    trace_csv = ROOT / "output/report/termination_study" / f"{summary_stem}_trace.csv"

    if not grid_csv.exists():
        raise SystemExit(f"Grid CSV not found: {grid_csv}")
    if not summary_json.exists():
        raise SystemExit(f"Summary JSON not found: {summary_json}")
    if not trace_csv.exists():
        raise SystemExit(f"Trace CSV not found: {trace_csv}")

    summary = json.loads(summary_json.read_text())
    benchmark = str(summary["exact_benchmark"])
    mode = str(summary["termination_mode"])
    beta = int(summary["beta"])
    max_error = int(summary["max_error"])

    slug = f"{benchmark}_{mode}_iteration_story_b{beta}_e{max_error}"
    return {
        "log_path": resolved_log,
        "grid_csv": grid_csv,
        "trace_csv": trace_csv,
        "summary_json": summary_json,
        "summary": summary,
        "benchmark": benchmark,
        "mode": mode,
        "beta": beta,
        "max_error": max_error,
        "slug": slug,
    }


def build_iteration_table(case: dict[str, object]) -> pd.DataFrame:
    trace = pd.read_csv(Path(case["trace_csv"])).sort_values("iteration").reset_index(drop=True)
    grid = pd.read_csv(Path(case["grid_csv"])).copy()
    summary = dict(case["summary"])

    runtime_by_iteration = (
        grid.groupby("iteration", as_index=False)["runtime"]
        .sum()
        .rename(columns={"runtime": "iteration_runtime_seconds"})
    )
    runtime_by_iteration["elapsed_runtime_seconds"] = runtime_by_iteration["iteration_runtime_seconds"].cumsum()
    timeout_limit = max(0.0, float(summary.get("timeout", 0.0)))
    count_rows: list[dict[str, object]] = []
    for iteration, group in grid.groupby("iteration", sort=True):
        counts = group["status"].value_counts()
        timeout_count = 0
        if timeout_limit > 0.0:
            timeout_count = int(
                ((group["status"] == "UNKNOWN") & (group["runtime"] >= max(0.0, timeout_limit - 1.0))).sum()
            )
        count_rows.append(
            {
                "iteration": int(iteration),
                "grid_sat_count_computed": int(counts.get("SAT", 0)),
                "grid_unsat_count_computed": int(counts.get("UNSAT", 0)),
                "grid_unknown_count_computed": int(counts.get("UNKNOWN", 0)),
                "grid_dominated_count_computed": int(counts.get("DOMINATED", 0)),
                "grid_timeout_count_computed": timeout_count,
            }
        )
    grid_counts_by_iteration = pd.DataFrame(count_rows)

    rows: list[dict[str, object]] = []
    for _, trace_row in trace.iterrows():
        iteration = int(trace_row["iteration"])
        grid_rows = grid[grid["iteration"] == iteration].copy()

        selected_cell = _clean_cell(trace_row.get("selected_cell"))
        if selected_cell is not None:
            primary_cell = selected_cell
            cell_source = "selected_sat"
        elif not grid_rows.empty:
            primary_cell = str(grid_rows.iloc[-1]["cell"])
            cell_source = "last_tested"
        else:
            primary_cell = None
            cell_source = "missing"

        row = trace_row.to_dict()
        row["selected_cell"] = selected_cell
        row["primary_cell"] = primary_cell
        row["cell_source"] = cell_source
        rows.append(row)

    df = pd.DataFrame(rows).merge(runtime_by_iteration, on="iteration", how="left")
    df = df.merge(grid_counts_by_iteration, on="iteration", how="left")
    df["current_area"] = df["best_area"].ffill()

    final_iteration = int(summary["iterations"])
    final_runtime_seconds = float(summary["runtime_seconds"])
    df.loc[df["iteration"] == final_iteration, "elapsed_runtime_seconds"] = final_runtime_seconds
    df["elapsed_runtime_seconds"] = df["elapsed_runtime_seconds"].ffill()
    df["elapsed_runtime_hours"] = df["elapsed_runtime_seconds"] / 3600.0

    count_columns = [
        "grid_sat_count",
        "grid_unsat_count",
        "grid_unknown_count",
        "grid_dominated_count",
        "grid_timeout_count",
    ]
    for column in count_columns:
        computed_column = f"{column}_computed"
        if column in df.columns:
            df[column] = df[column].fillna(df[computed_column])
        else:
            df[column] = df[computed_column]
        df[column] = df[column].fillna(0).astype(int)

    df["out_node"] = df["out_node"].fillna(0).astype(int)
    df["accepted"] = df["status"].eq("SAT")
    df["grid_summary"] = (
        df["grid_sat_count"].astype(str)
        + "/"
        + df["grid_unsat_count"].astype(str)
        + "/"
        + df["grid_unknown_count"].astype(str)
        + "/"
        + df["grid_dominated_count"].astype(str)
    )
    df["elapsed_label"] = df["elapsed_runtime_hours"].map(_format_elapsed_label)
    df["out_label"] = df["out_node"].map(lambda value: f"o{value}")
    df["status_label"] = df["status"].fillna("UNKNOWN")
    df["cell_label"] = df["primary_cell"].fillna("-")
    df["benchmark"] = str(case["benchmark"])
    df["termination_mode"] = str(case["mode"])
    df["beta"] = int(case["beta"])
    df["max_error"] = int(case["max_error"])

    return df[
        [
            "benchmark",
            "termination_mode",
            "beta",
            "max_error",
            "iteration",
            "out_node",
            "out_label",
            "status",
            "status_label",
            "primary_cell",
            "cell_label",
            "cell_source",
            "selected_cell",
            "accepted",
            "best_area",
            "current_area",
            "iteration_runtime_seconds",
            "elapsed_runtime_seconds",
            "elapsed_runtime_hours",
            "elapsed_label",
            "grid_sat_count",
            "grid_unsat_count",
            "grid_unknown_count",
            "grid_dominated_count",
            "grid_timeout_count",
            "grid_summary",
        ]
    ].copy()


def _draw_notes_table(ax: plt.Axes, df: pd.DataFrame) -> None:
    row_specs = [
        ("time [h]", "elapsed_label"),
        ("out", "out_label"),
        ("result", "status_label"),
        ("cell", "cell_label"),
        ("S/U/?/D", "grid_summary"),
    ]
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
            elif column == "cell_label" and bool(data["accepted"]):
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
                fontsize=7.6,
                color=color,
            )


def plot_iteration_story(df: pd.DataFrame, case: dict[str, object], output_path: Path) -> Path:
    configure_style()
    iteration_count = int(df["iteration"].max())
    fig_width = max(14.0, 2.8 + (0.6 * iteration_count))
    fig, (ax_plot, ax_notes) = plt.subplots(
        2,
        1,
        figsize=(fig_width, 9.8),
        sharex=True,
        gridspec_kw={"height_ratios": [3.2, 1.8], "hspace": 0.05},
    )

    accepted = df[df["accepted"]].copy()
    stalled = df[~df["accepted"]].copy()

    ax_plot.step(
        df["iteration"],
        df["current_area"],
        where="post",
        color=LINE,
        linewidth=2.4,
        alpha=0.95,
        label="current area",
        zorder=2,
    )
    if not accepted.empty:
        ax_plot.scatter(
            accepted["iteration"],
            accepted["current_area"],
            s=58,
            color=ACCEPTED,
            edgecolor="#ffffff",
            linewidth=0.9,
            label="accepted SAT iteration",
            zorder=4,
        )
    if not stalled.empty:
        stalled_colors = stalled["status"].map(lambda status: STATUS_COLORS.get(str(status), LINE))
        ax_plot.scatter(
            stalled["iteration"],
            stalled["current_area"],
            s=56,
            facecolor=PANEL,
            edgecolor=stalled_colors,
            linewidth=1.4,
            label="non-accepted iteration",
            zorder=4,
        )

    final_accept_iteration = int(df[df["accepted"]]["iteration"].max())
    ax_plot.axvline(
        final_accept_iteration,
        color="#9a3412",
        linewidth=1.2,
        linestyle=":",
        alpha=0.8,
        zorder=1,
    )

    for _, row in df.iterrows():
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

    ax_plot.set_title(
        f"{case['benchmark']} {case['mode']} (beta {case['beta']}, max_error {case['max_error']}): current area over iterations\n"
        "notes show elapsed time, rewritten out node, iteration result, representative cell, and S/U/?/D counts"
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
    ]
    ax_plot.legend(
        handles=[
            Line2D([0], [0], color=LINE, linewidth=2.4, label="current area"),
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="None",
                markersize=7,
                markerfacecolor=ACCEPTED,
                markeredgecolor="#ffffff",
                markeredgewidth=0.9,
                label="accepted SAT iteration",
            ),
            Line2D([0], [0], color="#9a3412", linewidth=1.2, linestyle=":", label="last area improvement"),
            *status_handles,
        ],
        loc="upper right",
        ncol=2,
    )

    _draw_notes_table(ax_notes, df)
    ax_notes.set_xlabel("Iteration")

    fig.text(
        0.5,
        0.02,
        "For non-SAT iterations, the cell row shows the last tested grid cell because the trace does not record a selected cell once no SAT candidate is accepted.",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#5a5047",
    )

    fig.subplots_adjust(left=0.055, right=0.995, top=0.92, bottom=0.12, hspace=0.06)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    log_paths = list(args.log_path or DEFAULT_LOG_PATHS)
    cases = [_discover_case_from_log(path) for path in log_paths]

    for case in cases:
        df = build_iteration_table(case)
        csv_path = output_dir / f"{case['slug']}.csv"
        plot_path = output_dir / f"{case['slug']}.png"
        df.to_csv(csv_path, index=False)
        plot_iteration_story(df, case, plot_path)
        print(f"Wrote iteration summary CSV to {csv_path}")
        print(f"Wrote annotated iteration plot to {plot_path}")


if __name__ == "__main__":
    main()
