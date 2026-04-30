from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

TRACE_CSV = Path(
    "output/report/termination_study/"
    "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608_trace.csv"
)
GRID_CSV = Path(
    "output/report/"
    "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608.csv"
)
SUMMARY_JSON = Path(
    "output/report/termination_study/"
    "grid_mul_i16_o16_4X4_et350_subxpat_asc_encz3bvec_termnone_mode0_omax2_imax4_constnever_Sop1_time20260419:151608_summary.json"
)

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
}
STATUS_BACKGROUNDS = {
    "SAT": "#e8f4ec",
    "UNSAT": "#faece9",
    "UNKNOWN": "#fbf3e3",
    "STOPPED": "#eceff3",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot the recent mul_i16_o16 none run over iterations with per-iteration "
            "notes for out node, result status, grid cell, and grid-status counts."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/iteration_area_trajectories_20260424"),
        help="Directory for the generated CSV and annotated plot.",
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


def _load_summary() -> dict[str, object]:
    return json.loads(_resolve(SUMMARY_JSON).read_text())


def build_iteration_table() -> pd.DataFrame:
    trace = pd.read_csv(_resolve(TRACE_CSV)).sort_values("iteration").reset_index(drop=True)
    grid = pd.read_csv(_resolve(GRID_CSV)).copy()
    summary = _load_summary()

    runtime_by_iteration = (
        grid.groupby("iteration", as_index=False)["runtime"]
        .sum()
        .rename(columns={"runtime": "iteration_runtime_seconds"})
    )
    runtime_by_iteration["elapsed_runtime_seconds"] = runtime_by_iteration["iteration_runtime_seconds"].cumsum()

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
    df["elapsed_label"] = df["elapsed_runtime_hours"].map(lambda value: f"{value:.2f}")
    df["out_label"] = df["out_node"].map(lambda value: f"o{value}")
    df["status_label"] = df["status"].fillna("UNKNOWN")
    df["cell_label"] = df["primary_cell"].fillna("-")

    return df[
        [
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


def plot_iteration_story(df: pd.DataFrame, output_path: Path) -> Path:
    configure_style()
    fig, (ax_plot, ax_notes) = plt.subplots(
        2,
        1,
        figsize=(18.5, 9.8),
        sharex=True,
        gridspec_kw={"height_ratios": [3.2, 1.8], "hspace": 0.05},
    )

    accepted = df[df["accepted"]].copy()
    stalled = df[~df["accepted"]].copy()
    x_values = df["iteration"]

    ax_plot.step(
        x_values,
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
        "mul_i16_o16 none: current area over iterations\n"
        "notes show elapsed time, rewritten out node, iteration result, representative cell, and S/U/?/D counts"
    )
    ax_plot.set_ylabel("Current area (area units)")
    ax_plot.set_xlim(1, int(df["iteration"].max()))
    ax_plot.set_xticks(range(1, int(df["iteration"].max()) + 1))
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

    df = build_iteration_table()
    csv_path = output_dir / "mul_i16_o16_none_iteration_story.csv"
    plot_path = output_dir / "mul_i16_o16_none_iteration_story.png"

    df.to_csv(csv_path, index=False)
    plot_iteration_story(df, plot_path)

    print(f"Wrote iteration summary CSV to {csv_path}")
    print(f"Wrote annotated iteration plot to {plot_path}")


if __name__ == "__main__":
    main()
