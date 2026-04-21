from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"
NONE_COLOR = "#6c7688"
TRIVIAL_COLOR = "#d24b40"
ACCENT = "#0f766e"
BETA_COLORS = {
    32: "#e76f51",
    64: "#2a9d8f",
    96: "#577590",
}
AET_MARKERS = {
    250: "o",
    300: "s",
    350: "D",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate richer visual comparisons for trivial vs none termination studies.",
    )
    parser.add_argument(
        "--pairwise-tsv",
        type=Path,
        default=Path(
            "output/figure/zone_aet_large_mul_i16_a2_multiAET_20260402/trivial_vs_none_best_seen.tsv"
        ),
        help="Path to the pairwise trivial-vs-none TSV summary.",
    )
    parser.add_argument(
        "--runs-csv",
        type=Path,
        default=Path(
            "output/figure/zone_aet_large_mul_i16_a2_multiAET_20260402/termination_study_runs.csv"
        ),
        help="Path to termination_study_runs.csv for the same batch.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/zone_aet_large_mul_i16_a2_multiAET_20260402"),
        help="Directory where the generated figures should be written.",
    )
    parser.add_argument(
        "--benchmark-label",
        default="mul_i16_o16",
        help="Label used in plot titles.",
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
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "legend.frameon": False,
            "grid.color": GRID,
            "grid.linestyle": "-",
            "grid.linewidth": 0.7,
        }
    )


def load_data(pairwise_tsv: Path, runs_csv: Path) -> pd.DataFrame:
    pairwise = pd.read_csv(pairwise_tsv, sep="\t")
    runs = pd.read_csv(runs_csv)
    runs = runs[runs["termination_mode"].isin(["none", "trivial"])].copy()
    runs["aet"] = runs["max_error"].astype(int)
    runs["beta"] = runs["beta"].astype(int)

    iteration_pivot = (
        runs.pivot_table(
            index=["aet", "beta"],
            columns="termination_mode",
            values="iteration_count",
            aggfunc="first",
        )
        .rename(columns={"none": "none_iterations", "trivial": "trivial_iterations"})
        .reset_index()
    )

    stop_pivot = (
        runs.pivot_table(
            index=["aet", "beta"],
            columns="termination_mode",
            values="stop_reason",
            aggfunc="first",
        )
        .rename(columns={"none": "none_stop_reason", "trivial": "trivial_stop_reason"})
        .reset_index()
    )

    df = pairwise.merge(iteration_pivot, on=["aet", "beta"], how="left").merge(
        stop_pivot, on=["aet", "beta"], how="left"
    )
    df["case_label"] = df.apply(lambda row: f"E{int(row.aet)} / B{int(row.beta)}", axis=1)
    df["runtime_gain_pct"] = (
        (df["none_runtime_seconds"] - df["trivial_runtime_seconds"])
        / df["none_runtime_seconds"]
        * 100.0
    )
    df["final_area_gain_pct"] = (
        (df["none_final_area"] - df["trivial_final_area"])
        / df["none_final_area"]
        * 100.0
    )
    df["best_area_gain_pct"] = (
        (df["none_best_seen_area"] - df["trivial_best_seen_area"])
        / df["none_best_seen_area"]
        * 100.0
    )
    df["drift_gap"] = df["trivial_drift"] - df["none_drift"]
    df["iterations_saved"] = df["none_iterations"] - df["trivial_iterations"]
    df["none_runtime_hours"] = df["none_runtime_seconds"] / 3600.0
    df["trivial_runtime_hours"] = df["trivial_runtime_seconds"] / 3600.0
    df["endpoint_illusion_pct"] = df["final_area_gain_pct"] - df["best_area_gain_pct"]
    return df.sort_values(["aet", "beta"]).reset_index(drop=True)


def _metric_matrix(
    df: pd.DataFrame, value_col: str
) -> tuple[np.ndarray, list[int], list[int]]:
    aets = sorted(df["aet"].unique())
    betas = sorted(df["beta"].unique())
    matrix = np.full((len(aets), len(betas)), np.nan)
    for _, row in df.iterrows():
        matrix[aets.index(int(row["aet"])), betas.index(int(row["beta"]))] = float(row[value_col])
    return matrix, aets, betas


def _draw_heatmap(
    ax: plt.Axes,
    matrix: np.ndarray,
    aets: list[int],
    betas: list[int],
    title: str,
    fmt: str,
    cmap,
    norm=None,
) -> None:
    image = ax.imshow(matrix, cmap=cmap, norm=norm, aspect="auto")
    ax.set_title(title)
    ax.set_xticks(range(len(betas)), [str(beta) for beta in betas])
    ax.set_yticks(range(len(aets)), [str(aet) for aet in aets])
    ax.set_xlabel("beta")
    ax.set_ylabel("AET")
    for row_i in range(len(aets) + 1):
        ax.axhline(row_i - 0.5, color="#e9dfd4", lw=1.0)
    for col_i in range(len(betas) + 1):
        ax.axvline(col_i - 0.5, color="#e9dfd4", lw=1.0)
    for row_i, aet in enumerate(aets):
        for col_i, beta in enumerate(betas):
            value = matrix[row_i, col_i]
            if np.isnan(value):
                continue
            text = format(value, fmt)
            ax.text(
                col_i,
                row_i,
                text,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color=TEXT,
            )
    return image


def plot_heatmap_dashboard(df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    posneg = LinearSegmentedColormap.from_list("warm_balance", ["#b3261e", "#fff7e6", "#1a7f37"])
    sequential = LinearSegmentedColormap.from_list("cool_depth", ["#fff7e6", "#78c6a3", "#005f73"])
    driftmap = LinearSegmentedColormap.from_list("drift_gap", ["#0f766e", "#fff7e6", "#8d0801"])

    metrics = [
        ("runtime_gain_pct", "Runtime gain of trivial vs none (%)", ".1f"),
        ("final_area_gain_pct", "Final area gain of trivial vs none (%)", ".1f"),
        ("best_area_gain_pct", "Best-seen area gain of trivial vs none (%)", ".1f"),
        ("iterations_saved", "Iterations saved by trivial", ".0f"),
        ("drift_gap", "Extra drift of trivial vs none (area units)", ".1f"),
        ("endpoint_illusion_pct", "Endpoint illusion: final minus best gain (%)", ".1f"),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(16, 10), constrained_layout=False)
    fig.suptitle(
        f"{benchmark_label}: dense termination dashboard\nGreen means trivial looks favorable; red means risk or regression.",
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )

    for ax, (column, title, fmt) in zip(axes.flat, metrics):
        matrix, aets, betas = _metric_matrix(df, column)
        if column == "iterations_saved":
            image = _draw_heatmap(
                ax,
                matrix,
                aets,
                betas,
                title,
                fmt,
                cmap=sequential,
            )
        elif column == "drift_gap":
            max_abs = max(abs(np.nanmin(matrix)), abs(np.nanmax(matrix)))
            image = _draw_heatmap(
                ax,
                matrix,
                aets,
                betas,
                title,
                fmt,
                cmap=driftmap,
                norm=TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs),
            )
        else:
            max_abs = max(abs(np.nanmin(matrix)), abs(np.nanmax(matrix)))
            image = _draw_heatmap(
                ax,
                matrix,
                aets,
                betas,
                title,
                fmt,
                cmap=posneg,
                norm=TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs),
            )
        fig.colorbar(image, ax=ax, shrink=0.82, pad=0.02)

    output_path = output_dir / "mul_i16_o16_trivial_heatmap_dashboard.png"
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_risk_reward(df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), constrained_layout=False)
    panels = [
        ("final_area_gain_pct", "Final endpoint"),
        ("best_area_gain_pct", "Best-seen checkpoint"),
    ]

    for ax, (y_col, subtitle) in zip(axes, panels):
        ax.set_title(f"{subtitle}: QoR gain vs runtime gain")
        ax.axvspan(0, 80, ymin=0.5, ymax=1.0, color="#d9f3df", alpha=0.6)
        ax.axvspan(0, 80, ymin=0.0, ymax=0.5, color="#fff3cd", alpha=0.65)
        ax.axvspan(-80, 0, ymin=0.5, ymax=1.0, color="#e8f1ff", alpha=0.7)
        ax.axvspan(-80, 0, ymin=0.0, ymax=0.5, color="#fde2e4", alpha=0.75)
        ax.axhline(0, color="#8a7f73", lw=1.2)
        ax.axvline(0, color="#8a7f73", lw=1.2)
        ax.grid(True, alpha=0.35)
        ax.set_xlabel("Runtime gain of trivial vs none (%)")
        ax.set_ylabel("Area gain of trivial vs none (%)")
        ax.text(2, max(df[y_col]) + 0.6, "Faster + better", color="#1a7f37", fontweight="bold")
        ax.text(2, min(df[y_col]) - 1.2, "Faster + worse QoR", color="#9a6700", fontweight="bold")

        for idx, row in df.iterrows():
            ax.scatter(
                row["runtime_gain_pct"],
                row[y_col],
                s=110 + row["iterations_saved"] * 12,
                color=BETA_COLORS[int(row["beta"])],
                marker=AET_MARKERS[int(row["aet"])],
                edgecolor="#2a211a",
                linewidth=1.1,
                alpha=0.95,
                zorder=3,
            )
            x_offset = 8 if idx % 2 == 0 else -30
            y_offset = 7 if idx % 3 == 0 else -12
            ax.annotate(
                f"E{int(row['aet'])}/B{int(row['beta'])}",
                (row["runtime_gain_pct"], row[y_col]),
                textcoords="offset points",
                xytext=(x_offset, y_offset),
                fontsize=9,
                fontweight="bold",
            )

        x_padding = 7
        y_padding = 3
        ax.set_xlim(df["runtime_gain_pct"].min() - x_padding, df["runtime_gain_pct"].max() + x_padding)
        ax.set_ylim(df[y_col].min() - y_padding, df[y_col].max() + y_padding)

    beta_handles = [
        Line2D([0], [0], marker="o", color="none", label=f"beta={beta}", markerfacecolor=color, markeredgecolor="#2a211a", markersize=10)
        for beta, color in BETA_COLORS.items()
    ]
    aet_handles = [
        Line2D([0], [0], marker=marker, color="#2a211a", label=f"AET={aet}", linestyle="none", markersize=9)
        for aet, marker in AET_MARKERS.items()
    ]
    fig.legend(
        handles=beta_handles + aet_handles,
        loc="upper center",
        ncol=6,
        bbox_to_anchor=(0.5, 0.97),
    )
    fig.suptitle(
        f"{benchmark_label}: risk–reward map for trivial termination",
        fontsize=18,
        fontweight="bold",
        y=0.995,
    )
    output_path = output_dir / "mul_i16_o16_trivial_risk_reward.png"
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def _plot_dumbbell_panel(
    ax: plt.Axes,
    cases: pd.DataFrame,
    none_col: str,
    trivial_col: str,
    title: str,
    x_label: str,
) -> None:
    y_positions = np.arange(len(cases))
    ax.set_title(title)
    for idx, row in cases.iterrows():
        y = y_positions[idx]
        if idx % 2 == 0:
            ax.axhspan(y - 0.5, y + 0.5, color="#f2ebe2", zorder=0)
        ax.hlines(y, row[none_col], row[trivial_col], color="#b8aa98", lw=3, zorder=1)
        ax.scatter(row[none_col], y, s=85, color=NONE_COLOR, edgecolor="#2a211a", linewidth=0.8, zorder=3)
        ax.scatter(row[trivial_col], y, s=85, color=TRIVIAL_COLOR, edgecolor="#2a211a", linewidth=0.8, zorder=3)
    ax.set_yticks(y_positions, cases["case_label"])
    ax.invert_yaxis()
    ax.grid(True, axis="x", alpha=0.35)
    ax.set_xlabel(x_label)
    ax.tick_params(axis="y", labelsize=10)


def plot_dumbbells(df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    cases = df.copy()
    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=False)

    _plot_dumbbell_panel(
        axes[0, 0],
        cases,
        "none_runtime_hours",
        "trivial_runtime_hours",
        "Runtime per case",
        "Hours",
    )
    _plot_dumbbell_panel(
        axes[0, 1],
        cases,
        "none_final_area",
        "trivial_final_area",
        "Final area per case",
        "Area",
    )
    _plot_dumbbell_panel(
        axes[1, 0],
        cases,
        "none_best_seen_area",
        "trivial_best_seen_area",
        "Best-seen area per case",
        "Area",
    )
    _plot_dumbbell_panel(
        axes[1, 1],
        cases,
        "none_drift",
        "trivial_drift",
        "Endpoint drift per case",
        "Area units of drift",
    )

    fig.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=NONE_COLOR, markeredgecolor="#2a211a", markersize=9, label="none"),
            Line2D([0], [0], marker="o", color="none", markerfacecolor=TRIVIAL_COLOR, markeredgecolor="#2a211a", markersize=9, label="trivial"),
        ],
        loc="upper center",
        ncol=2,
        bbox_to_anchor=(0.5, 0.98),
    )
    fig.suptitle(
        f"{benchmark_label}: direct pairwise comparison of none vs trivial",
        fontsize=18,
        fontweight="bold",
        y=0.995,
    )
    output_path = output_dir / "mul_i16_o16_trivial_dumbbells.png"
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_trends(df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), constrained_layout=False)
    trend_metrics = [
        ("runtime_gain_pct", "Runtime gain vs none (%)"),
        ("final_area_gain_pct", "Final area gain vs none (%)"),
        ("best_area_gain_pct", "Best-seen area gain vs none (%)"),
        ("drift_gap", "Extra drift of trivial vs none"),
    ]

    for ax, (metric, title) in zip(axes.flat, trend_metrics):
        ax.set_title(title)
        ax.axhline(0, color="#8a7f73", lw=1.1)
        ax.grid(True, alpha=0.35)
        for beta, color in BETA_COLORS.items():
            subset = df[df["beta"] == beta].sort_values("aet")
            ax.plot(
                subset["aet"],
                subset[metric],
                marker="o",
                color=color,
                lw=2.4,
                ms=7,
                label=f"beta={beta}",
            )
            for _, row in subset.iterrows():
                ax.text(
                    row["aet"],
                    row[metric],
                    f"{row[metric]:+.1f}",
                    fontsize=8,
                    ha="center",
                    va="bottom" if row[metric] >= 0 else "top",
                )
        ax.set_xlabel("AET")
        ax.set_xticks(sorted(df["aet"].unique()))

    axes[0, 0].legend(loc="best")
    fig.suptitle(
        f"{benchmark_label}: how AET and beta shape trivial termination",
        fontsize=18,
        fontweight="bold",
        y=0.995,
    )
    output_path = output_dir / "mul_i16_o16_trivial_trends.png"
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def write_plot_guide(output_dir: Path, benchmark_label: str, paths: Dict[str, Path]) -> Path:
    guide_path = output_dir / "plot_guide.md"
    guide_path.write_text(
        "\n".join(
            [
                f"# Plot Guide for `{benchmark_label}`",
                "",
                "## Suggested views",
                "",
                f"- [{paths['heatmaps'].name}]({paths['heatmaps'].name})",
                "  - Dense dashboard. Best for scanning runtime gain, QoR gain, drift, and iteration savings at once.",
                f"- [{paths['risk_reward'].name}]({paths['risk_reward'].name})",
                "  - Best for thesis discussion. Shows whether trivial is faster-and-better, faster-but-risky, or simply slower.",
                f"- [{paths['dumbbells'].name}]({paths['dumbbells'].name})",
                "  - Best for exact pairwise reading. Very easy to compare `none` and `trivial` for each case.",
                f"- [{paths['trends'].name}]({paths['trends'].name})",
                "  - Best for explaining the effect of `AET` and `beta` on termination behavior.",
                "",
                "## Reading hints",
                "",
                "- Positive gain means `trivial` is favorable.",
                "- In the risk–reward plot, the upper-right quadrant is the ideal region: faster and smaller.",
                "- The heatmap dashboard is the quickest way to find danger zones such as `AET=250, beta=32`.",
                "- The endpoint drift panels help distinguish true QoR gains from runs that only look better because they stop earlier on the same search path.",
                "",
            ]
        )
    )
    return guide_path


def main() -> None:
    args = parse_args()
    configure_style()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(args.pairwise_tsv, args.runs_csv)

    paths = {
        "heatmaps": plot_heatmap_dashboard(df, args.output_dir, args.benchmark_label),
        "risk_reward": plot_risk_reward(df, args.output_dir, args.benchmark_label),
        "dumbbells": plot_dumbbells(df, args.output_dir, args.benchmark_label),
        "trends": plot_trends(df, args.output_dir, args.benchmark_label),
    }
    guide_path = write_plot_guide(args.output_dir, args.benchmark_label, paths)

    for name, path in paths.items():
        print(f"Wrote {name} plot to {path}")
    print(f"Wrote guide to {guide_path}")


if __name__ == "__main__":
    main()
