from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CASES = (
    {
        "mode": "none",
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
        "text_offset": (0, 8),
    },
    {
        "mode": "predictor",
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
        "text_offset": (0, -12),
    },
)

BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plot current area against elapsed runtime for the latest i16 single-case "
            "none and predictor runs, labeling every point with its iteration."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/iteration_area_trajectories_20260424"),
        help="Directory for the generated CSV and plot.",
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
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "legend.frameon": False,
            "grid.color": GRID,
            "grid.linestyle": "-",
            "grid.linewidth": 0.8,
        }
    )


def _resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def _load_summary(path: Path) -> dict[str, object]:
    return json.loads(_resolve_path(path).read_text())


def build_case_table(case: dict[str, object]) -> pd.DataFrame:
    trace = pd.read_csv(_resolve_path(case["trace_csv"]))
    grid = pd.read_csv(_resolve_path(case["grid_csv"]))
    summary = _load_summary(Path(case["summary_json"]))

    trace = trace.sort_values("iteration").reset_index(drop=True)
    runtime_by_iteration = (
        grid.groupby("iteration", as_index=False)["runtime"].sum().rename(columns={"runtime": "iteration_runtime_seconds"})
    )
    runtime_by_iteration["elapsed_runtime_seconds"] = runtime_by_iteration["iteration_runtime_seconds"].cumsum()

    case_df = trace.merge(runtime_by_iteration, on="iteration", how="left")
    case_df["mode"] = str(case["mode"])
    case_df["label"] = str(case["label"])
    case_df["current_area"] = case_df["best_area"].ffill()

    final_iteration = int(summary["iterations"])
    final_runtime_seconds = float(summary["runtime_seconds"])
    final_accept_iteration = int(summary["final_iteration"])
    final_accept_runtime_seconds = float(summary["final_runtime_at_accept_seconds"])

    if case_df["iteration"].iloc[-1] != final_iteration:
        raise ValueError(
            f"{case['mode']} trace ends at iteration {case_df['iteration'].iloc[-1]}, expected {final_iteration}"
        )

    case_df.loc[case_df["iteration"] == final_iteration, "elapsed_runtime_seconds"] = final_runtime_seconds
    case_df["elapsed_runtime_seconds"] = case_df["elapsed_runtime_seconds"].ffill()
    case_df["elapsed_runtime_hours"] = case_df["elapsed_runtime_seconds"] / 3600.0
    case_df["accepted"] = case_df["best_area"].notna()

    accepted_runtime = case_df["elapsed_runtime_seconds"].where(case_df["accepted"])
    case_df["accepted_runtime_seconds"] = accepted_runtime
    case_df.loc[
        case_df["iteration"] == final_accept_iteration,
        "accepted_runtime_seconds",
    ] = final_accept_runtime_seconds
    case_df["accepted_runtime_hours"] = case_df["accepted_runtime_seconds"] / 3600.0

    return case_df[
        [
            "mode",
            "label",
            "iteration",
            "status",
            "benchmark",
            "accepted",
            "best_area",
            "current_area",
            "iteration_runtime_seconds",
            "elapsed_runtime_seconds",
            "elapsed_runtime_hours",
            "accepted_runtime_seconds",
            "accepted_runtime_hours",
        ]
    ].copy()


def plot_area_vs_time(df: pd.DataFrame, output_path: Path) -> Path:
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(16.5, 7.5), sharey=True)
    ax_zoom, ax_full = axes

    offsets = {case["mode"]: case["text_offset"] for case in DEFAULT_CASES}
    colors = {case["mode"]: case["color"] for case in DEFAULT_CASES}
    line_styles = {"none": "--", "predictor": "-"}
    markers = {"none": "o", "predictor": "s"}
    case_by_mode = {str(case["mode"]): case for case in DEFAULT_CASES}
    plot_order = (case_by_mode["predictor"], case_by_mode["none"])

    max_accept_hours = float(df["accepted_runtime_hours"].max(skipna=True))
    max_elapsed_hours = float(df["elapsed_runtime_hours"].max(skipna=True))

    for case in plot_order:
        mode = str(case["mode"])
        subset = df[df["mode"] == mode].sort_values("iteration").copy()
        color = colors[mode]
        linestyle = line_styles[mode]
        marker = markers[mode]
        accepted_facecolor = color if mode == "predictor" else PANEL
        accepted_edgecolor = "#ffffff" if mode == "predictor" else color
        accepted_size = 42 if mode == "predictor" else 52
        line_zorder = 3 if mode == "predictor" else 5
        marker_zorder = 4 if mode == "predictor" else 6

        accepted = subset[subset["accepted"]]
        stagnant = subset[~subset["accepted"]]

        for ax in axes:
            ax.step(
                subset["elapsed_runtime_hours"],
                subset["current_area"],
                where="post",
                color=color,
                linewidth=2.2,
                alpha=0.95,
                linestyle=linestyle,
                label=f"{case['label']} termination",
                zorder=line_zorder,
            )
            ax.scatter(
                accepted["elapsed_runtime_hours"],
                accepted["current_area"],
                s=accepted_size,
                facecolor=accepted_facecolor,
                edgecolor=accepted_edgecolor,
                linewidth=1.1 if mode == "none" else 0.8,
                marker=marker,
                zorder=marker_zorder,
            )
            if not stagnant.empty:
                ax.scatter(
                    stagnant["elapsed_runtime_hours"],
                    stagnant["current_area"],
                    s=34,
                    facecolor=PANEL,
                    edgecolor=color,
                    linewidth=1.1,
                    marker=marker,
                    zorder=4,
                )

        zoom_labels = subset[subset["accepted"]].copy()
        full_labels = subset[subset["iteration"] >= 17].copy()
        for ax, label_rows in ((ax_zoom, zoom_labels), (ax_full, full_labels)):
            for _, row in label_rows.iterrows():
                offset = offsets[mode]
                ax.annotate(
                    str(int(row["iteration"])),
                    (row["elapsed_runtime_hours"], row["current_area"]),
                    xytext=offset,
                    textcoords="offset points",
                    ha="center",
                    va="center",
                    fontsize=8,
                    color=color,
                    bbox={
                        "boxstyle": "round,pad=0.15",
                        "facecolor": "#fffaf5",
                        "edgecolor": "none",
                        "alpha": 0.82,
                    },
                )

    ax_zoom.set_title("Acceptance window")
    ax_zoom.set_xlabel("Elapsed runtime (hours)")
    ax_zoom.set_ylabel("Current area (area units)")
    ax_zoom.set_xlim(-0.1, max_accept_hours + 0.35)
    ax_zoom.grid(True, axis="both", alpha=0.8)
    ax_zoom.set_axisbelow(True)

    ax_full.set_title("Full run")
    ax_full.set_xlabel("Elapsed runtime (hours)")
    ax_full.set_xlim(-0.5, max_elapsed_hours + 1.0)
    ax_full.grid(True, axis="both", alpha=0.8)
    ax_full.set_axisbelow(True)
    ax_full.legend(loc="upper right")

    fig.suptitle("mul_i16_o16: current area vs elapsed runtime\nlabels show iteration number", y=1.02)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    case_frames = [build_case_table(case) for case in DEFAULT_CASES]
    combined = pd.concat(case_frames, ignore_index=True)
    combined = combined.sort_values(["mode", "iteration"]).reset_index(drop=True)

    csv_path = output_dir / "mul_i16_o16_area_vs_time.csv"
    plot_path = output_dir / "mul_i16_o16_area_vs_time_none_vs_predictor.png"
    combined.to_csv(csv_path, index=False)
    plot_area_vs_time(combined, plot_path)

    print(f"Wrote time-series CSV to {csv_path}")
    print(f"Wrote area-vs-time plot to {plot_path}")


if __name__ == "__main__":
    main()
