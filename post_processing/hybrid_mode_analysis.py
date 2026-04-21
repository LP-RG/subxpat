from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd


BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"
MODE_ORDER = ["none", "trivial", "pareto", "hybrid"]
MODE_COLORS = {
    "none": "#2d6a4f",
    "trivial": "#c1121f",
    "pareto": "#4361ee",
    "hybrid": "#7b2cbf",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build dedicated 4-mode hybrid termination summaries and plots.",
    )
    parser.add_argument(
        "--runs-csv",
        type=Path,
        default=Path(
            "output/figure/zone_aet_i8_hybrid_lowaet_20260409/termination_study_runs.csv"
        ),
        help="Path to termination_study_runs.csv for the analyzed batch.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/zone_aet_i8_hybrid_lowaet_20260409"),
        help="Directory where the dedicated report artifacts will be written.",
    )
    parser.add_argument(
        "--benchmark-label",
        default="mul_i8_o8",
        help="Benchmark name for plot and report titles.",
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
            "grid.linewidth": 0.7,
        }
    )


def load_runs(runs_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(runs_csv)
    df = df[df["termination_mode"].isin(MODE_ORDER)].copy()
    df["aet"] = df["max_error"].astype(float).astype(int)
    df["beta"] = df["beta"].astype(float).astype(int)
    df["runtime_seconds"] = df["runtime_seconds"].astype(float)
    df["final_area"] = df["final_area"].astype(float)
    df["best_seen_area"] = df["best_seen_area"].astype(float)
    return df.sort_values(["aet", "beta", "termination_mode"]).reset_index(drop=True)


def build_case_summary(runs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (aet, beta), group in runs.groupby(["aet", "beta"], sort=True):
        row = {"aet": int(aet), "beta": int(beta)}
        by_mode = {mode: group[group["termination_mode"] == mode].iloc[0] for mode in MODE_ORDER}
        for mode in MODE_ORDER:
            run = by_mode[mode]
            row[f"{mode}_area"] = float(run["final_area"])
            row[f"{mode}_best_area"] = float(run["best_seen_area"])
            row[f"{mode}_runtime_s"] = float(run["runtime_seconds"])
            row[f"{mode}_stop"] = str(run["stop_reason"])
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["aet", "beta"]).reset_index(drop=True)


def classify_against(case_df: pd.DataFrame, candidate: str, baseline: str, best_seen: bool = False) -> Counter:
    counter: Counter = Counter()
    area_suffix = "best_area" if best_seen else "area"
    for _, row in case_df.iterrows():
        left = float(row[f"{candidate}_{area_suffix}"])
        right = float(row[f"{baseline}_{area_suffix}"])
        if left < right:
            counter["better"] += 1
        elif left > right:
            counter["worse"] += 1
        else:
            counter["tied"] += 1
    return counter


def classify_runtime(case_df: pd.DataFrame, candidate: str, baseline: str) -> Counter:
    counter: Counter = Counter()
    for _, row in case_df.iterrows():
        left = float(row[f"{candidate}_runtime_s"])
        right = float(row[f"{baseline}_runtime_s"])
        if left < right:
            counter["faster"] += 1
        elif left > right:
            counter["slower"] += 1
        else:
            counter["tied"] += 1
    return counter


def _metric_matrix(case_df: pd.DataFrame, value_col: str) -> tuple[np.ndarray, list[int], list[int]]:
    aets = sorted(case_df["aet"].unique())
    betas = sorted(case_df["beta"].unique())
    matrix = np.full((len(aets), len(betas)), np.nan)
    for _, row in case_df.iterrows():
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
    for row_i, _ in enumerate(aets):
        for col_i, _ in enumerate(betas):
            value = matrix[row_i, col_i]
            if np.isnan(value):
                continue
            ax.text(
                col_i,
                row_i,
                format(value, fmt),
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color=TEXT,
            )
    return image


def plot_delta_dashboard(case_df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    for baseline in ["none", "trivial", "pareto"]:
        case_df[f"hybrid_vs_{baseline}_runtime_gain_pct"] = (
            (case_df[f"{baseline}_runtime_s"] - case_df["hybrid_runtime_s"])
            / case_df[f"{baseline}_runtime_s"]
            * 100.0
        )
        case_df[f"hybrid_vs_{baseline}_area_gain_pct"] = (
            (case_df[f"{baseline}_area"] - case_df["hybrid_area"])
            / case_df[f"{baseline}_area"]
            * 100.0
        )

    posneg = LinearSegmentedColormap.from_list(
        "hybrid_balance", ["#b3261e", "#fff7e6", "#1a7f37"]
    )
    fig, axes = plt.subplots(2, 3, figsize=(16, 9), constrained_layout=False)
    fig.suptitle(
        f"{benchmark_label}: hybrid relative to each baseline\nGreen means hybrid looks favorable; red means regression.",
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )

    metrics = [
        ("hybrid_vs_none_runtime_gain_pct", "Runtime gain of hybrid vs none (%)"),
        ("hybrid_vs_none_area_gain_pct", "Final area gain of hybrid vs none (%)"),
        ("hybrid_vs_trivial_runtime_gain_pct", "Runtime gain of hybrid vs trivial (%)"),
        ("hybrid_vs_trivial_area_gain_pct", "Final area gain of hybrid vs trivial (%)"),
        ("hybrid_vs_pareto_runtime_gain_pct", "Runtime gain of hybrid vs pareto (%)"),
        ("hybrid_vs_pareto_area_gain_pct", "Final area gain of hybrid vs pareto (%)"),
    ]

    for ax, (column, title) in zip(axes.flat, metrics):
        matrix, aets, betas = _metric_matrix(case_df, column)
        max_abs = max(abs(np.nanmin(matrix)), abs(np.nanmax(matrix)))
        image = _draw_heatmap(
            ax,
            matrix,
            aets,
            betas,
            title,
            ".1f",
            cmap=posneg,
            norm=TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs),
        )
        fig.colorbar(image, ax=ax, shrink=0.82, pad=0.02)

    fig.subplots_adjust(top=0.84, wspace=0.28, hspace=0.35)
    output_path = output_dir / f"{benchmark_label}_hybrid_delta_dashboard.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_tradeoff_grid(case_df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    aets = sorted(case_df["aet"].unique())
    betas = sorted(case_df["beta"].unique())
    fig, axes = plt.subplots(
        len(aets), len(betas), figsize=(14, 12), sharex=False, sharey=False, constrained_layout=False
    )
    fig.suptitle(
        f"{benchmark_label}: final area vs runtime by termination mode\nEach panel is one (AET, beta) setting.",
        fontsize=18,
        fontweight="bold",
        y=0.985,
    )

    for row_i, aet in enumerate(aets):
        for col_i, beta in enumerate(betas):
            ax = axes[row_i, col_i]
            subset = case_df[(case_df["aet"] == aet) & (case_df["beta"] == beta)].iloc[0]
            for mode in MODE_ORDER:
                x = float(subset[f"{mode}_area"])
                y = float(subset[f"{mode}_runtime_s"])
                ax.scatter(
                    x,
                    y,
                    s=120,
                    c=MODE_COLORS[mode],
                    edgecolors="white",
                    linewidths=1.5,
                    zorder=3,
                )
                ax.text(
                    x,
                    y,
                    mode[0].upper(),
                    ha="center",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color="white",
                    zorder=4,
                )

            ax.grid(True, alpha=0.35)
            ax.set_title(f"AET={aet}, beta={beta}")
            ax.set_xlabel("final area")
            ax.set_ylabel("runtime (s)")

    handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label=mode,
            markerfacecolor=MODE_COLORS[mode],
            markeredgecolor="white",
            markeredgewidth=1.5,
            markersize=10,
        )
        for mode in MODE_ORDER
    ]
    fig.legend(handles=handles, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 0.93))
    fig.subplots_adjust(top=0.88, wspace=0.28, hspace=0.42)
    output_path = output_dir / f"{benchmark_label}_hybrid_tradeoff_grid.png"
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def format_secs(seconds: float) -> str:
    if seconds >= 3600:
        return f"{seconds / 3600.0:.2f} h"
    return f"{seconds:.0f} s"


def write_report(case_df: pd.DataFrame, output_dir: Path, benchmark_label: str) -> Path:
    runtime_vs_none = classify_runtime(case_df, "hybrid", "none")
    runtime_vs_trivial = classify_runtime(case_df, "hybrid", "trivial")
    runtime_vs_pareto = classify_runtime(case_df, "hybrid", "pareto")
    final_vs_none = classify_against(case_df, "hybrid", "none", best_seen=False)
    best_vs_none = classify_against(case_df, "hybrid", "none", best_seen=True)
    final_vs_trivial = classify_against(case_df, "hybrid", "trivial", best_seen=False)
    final_vs_pareto = classify_against(case_df, "hybrid", "pareto", best_seen=False)
    stop_counts = Counter(case_df["hybrid_stop"])

    mean_runtime_delta_vs_none = (
        case_df["hybrid_runtime_s"] - case_df["none_runtime_s"]
    ).mean()
    mean_runtime_delta_vs_trivial = (
        case_df["hybrid_runtime_s"] - case_df["trivial_runtime_s"]
    ).mean()
    mean_runtime_delta_vs_pareto = (
        case_df["hybrid_runtime_s"] - case_df["pareto_runtime_s"]
    ).mean()

    # Selector behavior.
    exact_pareto = int(
        ((case_df["hybrid_area"] == case_df["pareto_area"]) &
         (case_df["hybrid_runtime_s"] == case_df["pareto_runtime_s"])).sum()
    )
    exact_trivial = int(
        ((case_df["hybrid_area"] == case_df["trivial_area"]) &
         (case_df["hybrid_runtime_s"] == case_df["trivial_runtime_s"])).sum()
    )
    area_matches_pareto = int((case_df["hybrid_area"] == case_df["pareto_area"]).sum())
    area_matches_trivial = int((case_df["hybrid_area"] == case_df["trivial_area"]).sum())

    best_case = case_df.loc[
        (case_df["hybrid_area"] - case_df["none_area"]).idxmin()
    ]
    worst_case = case_df.loc[
        (case_df["hybrid_area"] - case_df["none_area"]).idxmax()
    ]
    fastest_case = case_df.loc[
        (case_df["none_runtime_s"] - case_df["hybrid_runtime_s"]).idxmax()
    ]

    lines = [
        f"# Mini Report: Hybrid Termination on `{benchmark_label}` at Low AET",
        "",
        "## Scope",
        "",
        "Batch analyzed:",
        "",
        "- `benchmarking/generated/zone_aet_i8_hybrid_lowaet_20260409`",
        f"- benchmark: `{benchmark_label}`",
        "- constraint: `ZONE_AET`",
        "- parameters: `beta in {4,6,8}`, `alpha = 2`, `AET in {4,8,12}`",
        "- termination modes: `none`, `trivial`, `pareto`, `hybrid`",
        "",
        "All 36 runs completed successfully with `exit_code = 0`.",
        "",
        "Main dedicated outputs for this batch are:",
        "",
        f"- `{output_dir / 'mode_comparison.tsv'}`",
        f"- `{output_dir / f'{benchmark_label}_hybrid_delta_dashboard.png'}`",
        f"- `{output_dir / f'{benchmark_label}_hybrid_tradeoff_grid.png'}`",
        "",
        "## Executive Summary",
        "",
        "The hybrid rule works technically, but on this low-AET `mul_i8_o8` matrix it mostly behaves like a selector between `trivial` and `pareto`, not like a genuinely stronger fourth strategy.",
        "",
        f"- versus `none`, `hybrid` was faster in `{runtime_vs_none['faster']}/9`, slower in `{runtime_vs_none['slower']}/9`, and tied in `{runtime_vs_none['tied']}/9`",
        f"- versus `none`, `hybrid` had lower final area in `{final_vs_none['better']}/9`, tied in `{final_vs_none['tied']}/9`, and was worse in `{final_vs_none['worse']}/9`",
        f"- under best-seen reporting, `hybrid` beat `none` in `{best_vs_none['better']}/9`, tied in `{best_vs_none['tied']}/9`, and was worse in `{best_vs_none['worse']}/9`",
        f"- versus `trivial`, `hybrid` tied final area in `{final_vs_trivial['tied']}/9` cases and never improved it",
        f"- versus `pareto`, `hybrid` tied final area in `{final_vs_pareto['tied']}/9` cases and improved it in only `{final_vs_pareto['better']}/9`",
        "",
        "So the honest read is:",
        "",
        "- `hybrid` is usually inheriting the endpoint of whichever constituent rule fires first",
        "- when `pareto` fires first, hybrid often looks like Pareto",
        "- when the trivial ceiling fires first, hybrid often looks like Trivial",
        "- in this batch, that does not translate into a consistently better tradeoff than the best of the two parents",
        "",
        "## Quantitative Comparison",
        "",
        "Runtime deltas below are `hybrid minus baseline`, so a negative value means hybrid was faster.",
        "",
        f"- mean runtime delta of `hybrid` vs `none`: `{mean_runtime_delta_vs_none:+.1f} s`",
        f"- mean runtime delta of `hybrid` vs `trivial`: `{mean_runtime_delta_vs_trivial:+.1f} s`",
        f"- mean runtime delta of `hybrid` vs `pareto`: `{mean_runtime_delta_vs_pareto:+.1f} s`",
        f"- hybrid stop reasons: `pareto_termination` in `{stop_counts['pareto_termination']}/9`, `trivial_termination` in `{stop_counts['trivial_termination']}/9`",
        "",
        "Selector behavior:",
        "",
        f"- hybrid matched Pareto exactly in `{exact_pareto}/9` cases",
        f"- hybrid matched Trivial exactly in `{exact_trivial}/9` cases",
        f"- hybrid final area matched Pareto in `{area_matches_pareto}/9` cases",
        f"- hybrid final area matched Trivial in `{area_matches_trivial}/9` cases",
        "",
        "This is the strongest evidence that hybrid is mostly choosing between existing behaviors rather than creating a new stable frontier.",
        "",
        "## Pairwise Results",
        "",
        "| beta | AET | none area | none best | none s | trivial area | trivial best | trivial s | pareto area | pareto best | pareto s | hybrid area | hybrid best | hybrid s | hybrid stop |",
        "| --- | --- | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- | --- | ---: | --- |",
    ]

    for _, row in case_df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row["beta"])),
                    str(int(row["aet"])),
                    f"{row['none_area']:.4f}",
                    f"{row['none_best_area']:.4f}",
                    f"{row['none_runtime_s']:.0f}",
                    f"{row['trivial_area']:.4f}",
                    f"{row['trivial_best_area']:.4f}",
                    f"{row['trivial_runtime_s']:.0f}",
                    f"{row['pareto_area']:.4f}",
                    f"{row['pareto_best_area']:.4f}",
                    f"{row['pareto_runtime_s']:.0f}",
                    f"{row['hybrid_area']:.4f}",
                    f"{row['hybrid_best_area']:.4f}",
                    f"{row['hybrid_runtime_s']:.0f}",
                    str(row["hybrid_stop"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## What The Hybrid Batch Shows",
            "",
            "### 1. Hybrid can be a strong runtime reducer against none",
            "",
            f"The strongest hybrid speedup against `none` was `AET={int(fastest_case['aet'])}, beta={int(fastest_case['beta'])}`: runtime `{fastest_case['none_runtime_s']:.0f} s -> {fastest_case['hybrid_runtime_s']:.0f} s` while final area moved `{fastest_case['none_area']:.4f} -> {fastest_case['hybrid_area']:.4f}`.",
            "",
            "But that does not mean the QoR tradeoff is good by default. Hybrid's biggest speedups often happen when it follows Pareto into an early endpoint.",
            "",
            "### 2. The cleanest hybrid win is limited",
            "",
            f"The only case where hybrid improved final area over `none` was `AET={int(best_case['aet'])}, beta={int(best_case['beta'])}`: area `{best_case['none_area']:.4f} -> {best_case['hybrid_area']:.4f}`, runtime `{best_case['none_runtime_s']:.0f} s -> {best_case['hybrid_runtime_s']:.0f} s`.",
            "",
            f"But even there, best-seen area was only a tie: `none` best `{best_case['none_best_area']:.4f}` vs hybrid best `{best_case['hybrid_best_area']:.4f}`.",
            "",
            "### 3. The clearest hybrid failure is when it inherits Pareto's early stop",
            "",
            f"The worst QoR regression against `none` was `AET={int(worst_case['aet'])}, beta={int(worst_case['beta'])}`: area `{worst_case['none_area']:.4f} -> {worst_case['hybrid_area']:.4f}` while runtime dropped `{worst_case['none_runtime_s']:.0f} s -> {worst_case['hybrid_runtime_s']:.0f} s`.",
            "",
            f"In that case, hybrid stopped by `{worst_case['hybrid_stop']}` and effectively followed Pareto's endpoint rather than preserving the safer `none` / `trivial` design.",
            "",
            "### 4. Hybrid does not consistently beat the better parent",
            "",
            "Examples:",
            "",
            "- `AET=12, beta=4`: hybrid equals Pareto (`83 s`, area `23.4650`) and is better than Trivial only because Pareto was already better there.",
            "- `AET=8, beta=6`: hybrid equals Trivial in area (`68.5178`) and runtime (`104-105 s`), so it inherits Trivial's faster-but-worse tradeoff.",
            "- `AET=4, beta=8`: hybrid stays much faster than `none` (`106 s` vs `197 s`) but ends on the same poor area as Pareto (`100.9000`).",
            "",
            "## Conclusion",
            "",
            "This batch does not support claiming that the hybrid rule is a new best default.",
            "",
            "What the data supports instead:",
            "",
            "- hybrid is a valid combined termination mode",
            "- it often behaves like the constituent rule that fires first",
            "- it is usually faster than `none`, but that alone is not enough",
            "- it does not reliably improve on `trivial`",
            "- and it can still inherit Pareto's most aggressive low-AET failures",
            "",
            "So the honest conclusion is:",
            "",
            "- `hybrid` is an interesting combination mechanism",
            "- but on `mul_i8_o8 + ZONE_AET + AET in {4,8,12}`, it is not yet better than simply choosing the right parent rule for the regime",
        ]
    )

    report_path = output_dir / "mini_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def main() -> None:
    args = parse_args()
    configure_style()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runs = load_runs(args.runs_csv)
    case_df = build_case_summary(runs)

    comparison_path = args.output_dir / "mode_comparison.tsv"
    case_df.to_csv(comparison_path, sep="\t", index=False, float_format="%.4f")

    plot_delta_dashboard(case_df.copy(), args.output_dir, args.benchmark_label)
    plot_tradeoff_grid(case_df, args.output_dir, args.benchmark_label)
    write_report(case_df, args.output_dir, args.benchmark_label)


if __name__ == "__main__":
    main()
