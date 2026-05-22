#!/usr/bin/env python3
"""Compare 3x3 vs 4x4 LPP/PPO settings for i16 dynamic-persistence runs."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
P1_DIR = ROOT / "benchmarking/generated/zone_aet_i16_dynpers_p1_grid_sweep_20260508"
FOLLOWUP_DIR = ROOT / "benchmarking/generated/zone_aet_i16_dynpers_patience_followup_20260512"
DEFAULT_OUTPUT_DIR = FOLLOWUP_DIR / "plots/lpp_ppo_comparison"

BG = "#faf7f0"
GRID = "#ded5c7"
TEXT = "#282522"
MUTED = "#776f64"
BLUE = "#2f6f9f"
GREEN = "#2f8a5b"
ORANGE = "#c97828"
RED = "#c84d3f"
GRAY = "#b8afa2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare LPP/PPO grids for dynamic-persistence i16 runs."
    )
    parser.add_argument("--p1-dir", type=Path, default=P1_DIR)
    parser.add_argument("--followup-dir", type=Path, default=FOLLOWUP_DIR)
    parser.add_argument(
        "--extra-dir",
        action="append",
        type=Path,
        default=[],
        help="Additional run group folder containing plots/run_summary_table.csv.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else ROOT / path


def configure_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "savefig.facecolor": BG,
            "axes.facecolor": BG,
            "axes.edgecolor": "#c8bdae",
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "text.color": TEXT,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.85,
        }
    )


def load_runs(p1_dir: Path, followup_dir: Path, extra_dirs: list[Path]) -> pd.DataFrame:
    frames = []
    groups = [
        ("2026-05-08 p1 full sweep", p1_dir),
        ("2026-05-12 p2/p3 follow-up", followup_dir),
    ]
    groups.extend((directory.name, directory) for directory in extra_dirs)
    for label, directory in groups:
        path = directory / "plots/run_summary_table.csv"
        if not path.exists():
            print(f"Skipping {directory}: missing {path.name}")
            continue
        frame = pd.read_csv(path)
        frame["source_group"] = label
        frames.append(frame)
    if not frames:
        raise SystemExit("No run_summary_table.csv files found.")
    runs = pd.concat(frames, ignore_index=True, sort=False)
    runs["grid"] = runs["grid_lpp"].astype(int).astype(str) + "x" + runs["grid_ppo"].astype(int).astype(str)
    runs["patience"] = "p" + runs["pareto_candidate_patience"].astype(int).astype(str)
    runs["case_key"] = (
        "b"
        + runs["beta"].astype(int).astype(str)
        + "_e"
        + runs["aet"].astype(int).astype(str)
        + "_a"
        + runs["alpha"].astype(int).astype(str)
        + "_"
        + runs["patience"]
    )
    runs["case_label"] = (
        "b"
        + runs["beta"].astype(int).astype(str)
        + " e"
        + runs["aet"].astype(int).astype(str)
        + " "
        + runs["patience"]
    )
    return runs.sort_values(["pareto_candidate_patience", "beta", "aet", "grid"]).reset_index(drop=True)


def build_pairs(runs: pd.DataFrame) -> pd.DataFrame:
    records = []
    for key, group in runs.groupby(["beta", "aet", "alpha", "pareto_candidate_patience"], dropna=False):
        by_grid = {row.grid: row for row in group.itertuples()}
        if "3x3" not in by_grid or "4x4" not in by_grid:
            continue
        row3 = by_grid["3x3"]
        row4 = by_grid["4x4"]
        area_delta = row4.best_area - row3.best_area
        runtime_delta = row4.runtime_hours - row3.runtime_hours
        records.append(
            {
                "beta": int(key[0]),
                "aet": int(key[1]),
                "alpha": int(key[2]),
                "patience": int(key[3]),
                "case_label": f"b{int(key[0])} e{int(key[1])} p{int(key[3])}",
                "area_3x3": row3.best_area,
                "area_4x4": row4.best_area,
                "area_delta_4x4_minus_3x3": area_delta,
                "runtime_3x3_h": row3.runtime_hours,
                "runtime_4x4_h": row4.runtime_hours,
                "runtime_delta_4x4_minus_3x3_h": runtime_delta,
                "iterations_3x3": row3.iterations,
                "iterations_4x4": row4.iterations,
                "best_grid_by_area": "4x4" if area_delta < 0 else "3x3" if area_delta > 0 else "tie",
                "faster_grid": "4x4" if runtime_delta < 0 else "3x3" if runtime_delta > 0 else "tie",
                "run_3x3": row3.run,
                "run_4x4": row4.run,
            }
        )
    columns = [
        "beta",
        "aet",
        "alpha",
        "patience",
        "case_label",
        "area_3x3",
        "area_4x4",
        "area_delta_4x4_minus_3x3",
        "runtime_3x3_h",
        "runtime_4x4_h",
        "runtime_delta_4x4_minus_3x3_h",
        "iterations_3x3",
        "iterations_4x4",
        "best_grid_by_area",
        "faster_grid",
        "run_3x3",
        "run_4x4",
    ]
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(records, columns=columns).sort_values(["patience", "beta", "aet"]).reset_index(drop=True)


def build_missing_pairs(runs: pd.DataFrame) -> pd.DataFrame:
    records = []
    for key, group in runs.groupby(["beta", "aet", "alpha", "pareto_candidate_patience"], dropna=False):
        present = sorted(group["grid"].unique())
        missing = [grid for grid in ("3x3", "4x4") if grid not in present]
        if missing:
            records.append(
                {
                    "beta": int(key[0]),
                    "aet": int(key[1]),
                    "alpha": int(key[2]),
                    "patience": int(key[3]),
                    "present_grids": ",".join(present),
                    "missing_grids": ",".join(missing),
                }
            )
    columns = ["beta", "aet", "alpha", "patience", "present_grids", "missing_grids"]
    if not records:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(records, columns=columns).sort_values(["patience", "beta", "aet"]).reset_index(drop=True)


def best_by_case(runs: pd.DataFrame) -> pd.DataFrame:
    return (
        runs.sort_values(["beta", "aet", "best_area", "runtime_hours", "pareto_candidate_patience"])
        .groupby(["beta", "aet", "alpha"], as_index=False)
        .first()
        .sort_values(["beta", "aet"])
    )


def plot_p1_delta_matrix(pairs: pd.DataFrame, output_path: Path) -> None:
    configure_style()
    p1 = pairs[pairs["patience"].eq(1)].copy()
    if p1.empty:
        return
    betas = sorted(p1["beta"].unique())
    aets = sorted(p1["aet"].unique())
    area = p1.pivot(index="beta", columns="aet", values="area_delta_4x4_minus_3x3").reindex(index=betas, columns=aets)
    runtime = p1.pivot(index="beta", columns="aet", values="runtime_delta_4x4_minus_3x3_h").reindex(index=betas, columns=aets)

    limit = max(abs(area.min().min()), abs(area.max().max()), 1.0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), gridspec_kw={"wspace": 0.26})
    image = axes[0].imshow(area.values, cmap="RdYlGn_r", vmin=-limit, vmax=limit, aspect="auto")
    axes[0].set_title("Area delta, p1 full sweep")
    axes[0].set_xlabel("AET")
    axes[0].set_ylabel("Beta")
    axes[0].set_xticks(range(len(aets)), [str(aet) for aet in aets])
    axes[0].set_yticks(range(len(betas)), [str(beta) for beta in betas])
    axes[0].grid(False)
    for i, beta in enumerate(betas):
        for j, aet in enumerate(aets):
            value = area.loc[beta, aet]
            rt_value = runtime.loc[beta, aet]
            if pd.isna(value):
                continue
            winner = "4x4" if value < 0 else "3x3" if value > 0 else "tie"
            axes[0].text(
                j,
                i,
                f"{value:+.1f}\n{winner}",
                ha="center",
                va="center",
                color=TEXT,
                fontsize=9,
                fontweight="bold",
            )
            axes[1].text(
                j,
                i,
                f"{rt_value:+.1f}h",
                ha="center",
                va="center",
                color=TEXT,
                fontsize=9,
                fontweight="bold",
            )

    rt_limit = max(abs(runtime.min().min()), abs(runtime.max().max()), 1.0)
    axes[1].imshow(runtime.values, cmap="RdYlGn_r", vmin=-rt_limit, vmax=rt_limit, aspect="auto")
    axes[1].set_title("Runtime delta, p1 full sweep")
    axes[1].set_xlabel("AET")
    axes[1].set_xticks(range(len(aets)), [str(aet) for aet in aets])
    axes[1].set_yticks(range(len(betas)), [str(beta) for beta in betas])
    axes[1].grid(False)

    cbar = fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.04)
    cbar.set_label("4x4 - 3x3 area")
    fig.text(
        0.5,
        -0.04,
        "Negative deltas mean 4x4 is better/faster. Positive deltas mean 3x3 is better/faster.",
        ha="center",
        fontsize=9,
        color=MUTED,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_all_pair_deltas(pairs: pd.DataFrame, output_path: Path) -> None:
    configure_style()
    if pairs.empty:
        return
    pairs = pairs.copy()
    pairs["label"] = pairs.apply(
        lambda row: f"b{int(row.beta)} e{int(row.aet)} p{int(row.patience)}", axis=1
    )
    colors = [GREEN if value < 0 else RED if value > 0 else GRAY for value in pairs["area_delta_4x4_minus_3x3"]]
    x = list(range(len(pairs)))

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.2), sharex=True, gridspec_kw={"hspace": 0.12})
    axes[0].bar(x, pairs["area_delta_4x4_minus_3x3"], color=colors, width=0.66)
    axes[0].axhline(0, color=TEXT, linewidth=1.0)
    axes[0].set_title("Paired grid comparison: area")
    axes[0].set_ylabel("4x4 - 3x3 area")
    axes[0].grid(True, axis="y")
    area_min = pairs["area_delta_4x4_minus_3x3"].min()
    area_max = pairs["area_delta_4x4_minus_3x3"].max()
    axes[0].set_ylim(area_min - max(4.0, abs(area_min) * 0.08), area_max + 7.0)
    for i, row in enumerate(pairs.itertuples()):
        va = "bottom" if row.area_delta_4x4_minus_3x3 >= 0 else "top"
        offset = 1.0 if row.area_delta_4x4_minus_3x3 >= 0 else -1.0
        axes[0].text(
            i,
            row.area_delta_4x4_minus_3x3 + offset,
            f"{row.area_delta_4x4_minus_3x3:+.1f}",
            ha="center",
            va=va,
            fontsize=8,
            color=TEXT,
        )

    rt_colors = [GREEN if value < 0 else RED if value > 0 else GRAY for value in pairs["runtime_delta_4x4_minus_3x3_h"]]
    axes[1].bar(x, pairs["runtime_delta_4x4_minus_3x3_h"], color=rt_colors, width=0.66)
    axes[1].axhline(0, color=TEXT, linewidth=1.0)
    axes[1].set_title("Paired grid comparison: runtime")
    axes[1].set_ylabel("4x4 - 3x3 runtime (h)")
    axes[1].set_xticks(x, pairs["label"], rotation=28, ha="right")
    axes[1].grid(True, axis="y")
    runtime_min = pairs["runtime_delta_4x4_minus_3x3_h"].min()
    runtime_max = pairs["runtime_delta_4x4_minus_3x3_h"].max()
    axes[1].set_ylim(runtime_min - 2.5, runtime_max + 3.0)
    for i, row in enumerate(pairs.itertuples()):
        va = "bottom" if row.runtime_delta_4x4_minus_3x3_h >= 0 else "top"
        offset = 0.7 if row.runtime_delta_4x4_minus_3x3_h >= 0 else -0.7
        axes[1].text(
            i,
            row.runtime_delta_4x4_minus_3x3_h + offset,
            f"{row.runtime_delta_4x4_minus_3x3_h:+.1f}h",
            ha="center",
            va=va,
            fontsize=8,
            color=TEXT,
        )
    fig.text(
        0.5,
        -0.03,
        "Negative deltas favor 4x4. Positive deltas favor 3x3.",
        ha="center",
        fontsize=9,
        color=MUTED,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_tradeoff(runs: pd.DataFrame, output_path: Path) -> None:
    configure_style()
    fig, ax = plt.subplots(figsize=(9.8, 6.0))
    markers = {"3x3": "o", "4x4": "s"}
    colors = {1: GREEN, 2: BLUE, 3: ORANGE}
    for (grid, patience), group in runs.groupby(["grid", "pareto_candidate_patience"]):
        ax.scatter(
            group["runtime_hours"],
            group["best_area"],
            s=80,
            marker=markers.get(grid, "o"),
            color=colors.get(int(patience), GRAY),
            edgecolor=BG,
            linewidth=0.8,
            label=f"{grid} p{int(patience)}",
            alpha=0.92,
        )
    for _, row in runs.iterrows():
        if row["pareto_candidate_patience"] > 1:
            ax.text(
                row["runtime_hours"] + 0.25,
                row["best_area"] + 1.5,
                f"b{int(row['beta'])} e{int(row['aet'])}",
                fontsize=8,
                color=MUTED,
            )
    ax.set_title("All dynamic-persistence grid runs")
    ax.set_xlabel("Runtime (h)")
    ax.set_ylabel("Best area")
    ax.invert_yaxis()
    ax.grid(True)
    ax.legend(frameon=False, ncol=3, fontsize=8)
    ax.text(
        0.01,
        -0.16,
        "Lower-left is better. Color = patience, marker = grid.",
        transform=ax.transAxes,
        fontsize=9,
        color=MUTED,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def write_index(output_dir: Path, runs: pd.DataFrame, pairs: pd.DataFrame, missing: pd.DataFrame, best: pd.DataFrame) -> None:
    p1_pairs = pairs[pairs["patience"].eq(1)]
    p2_pairs = pairs[pairs["patience"].eq(2)]
    p3_pairs = pairs[pairs["patience"].eq(3)]
    p23_pairs = pairs[pairs["patience"].isin([2, 3])]
    lines = [
        "# LPP/PPO Grid Comparison",
        "",
        "Dynamic-persistence comparison of `3x3` vs `4x4` on `mul_i16_o16`.",
        "",
        "## Files",
        "",
        "- [p1_grid_delta_matrix.png](p1_grid_delta_matrix.png)",
        "- [paired_grid_deltas.png](paired_grid_deltas.png)",
        "- [grid_tradeoff.png](grid_tradeoff.png)",
        "- [all_dynamic_grid_runs.csv](all_dynamic_grid_runs.csv)",
        "- [paired_grid_comparisons.csv](paired_grid_comparisons.csv)",
        "- [missing_grid_pairs.csv](missing_grid_pairs.csv)",
        "- [best_by_beta_aet.csv](best_by_beta_aet.csv)",
        "",
        "## Coverage",
        "",
        f"- Complete patience-1 pairs: `{len(p1_pairs)}` of `6` beta/AET cases.",
        f"- Complete patience-2 pairs: `{len(p2_pairs)}` of `6` beta/AET cases.",
        f"- Complete patience-3 pairs: `{len(p3_pairs)}` of `6` beta/AET cases.",
        f"- Patience-2/3 exact pairs currently available: `{len(p23_pairs)}` of `12` full beta/AET/patience cases.",
        "",
    ]
    if missing.empty:
        lines.append("- No missing pairs among observed beta/AET/patience cases.")
    else:
        lines.append("- Missing paired grids among observed beta/AET/patience cases:")
        for row in missing.itertuples():
            lines.append(
                f"- b{int(row.beta)} e{int(row.aet)} alpha{int(row.alpha)} p{int(row.patience)}: "
                f"present `{row.present_grids}`, missing `{row.missing_grids}`"
            )

    lines.extend(
        [
            "",
            "## Current Best Per Beta/AET",
            "",
            "| Beta | AET | Alpha | Best grid | Patience | Best area | Runtime | Iterations |",
            "|---:|---:|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in best.itertuples():
        lines.append(
            f"| {int(row.beta)} | {int(row.aet)} | {int(row.alpha)} | {row.grid} | "
            f"{int(row.pareto_candidate_patience)} | {row.best_area:.1f} | "
            f"{row.runtime_hours:.1f}h | {int(row.iterations)} |"
        )

    lines.extend(
        [
            "",
            "## Paired Grid Deltas",
            "",
            "`area delta` and `runtime delta` are `4x4 - 3x3`; negative means 4x4 is better/faster.",
            "",
            "| Beta | AET | Alpha | Patience | Area 3x3 | Area 4x4 | Area delta | Runtime 3x3 | Runtime 4x4 | Runtime delta | Area winner | Faster grid |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for row in pairs.itertuples():
        lines.append(
            f"| {int(row.beta)} | {int(row.aet)} | {int(row.alpha)} | {int(row.patience)} | "
            f"{row.area_3x3:.1f} | {row.area_4x4:.1f} | {row.area_delta_4x4_minus_3x3:+.1f} | "
            f"{row.runtime_3x3_h:.1f}h | {row.runtime_4x4_h:.1f}h | "
            f"{row.runtime_delta_4x4_minus_3x3_h:+.1f}h | {row.best_grid_by_area} | {row.faster_grid} |"
        )

    lines.extend(
        [
            "",
            "## Readout",
            "",
            "- For the complete p1 sweep, beta 32 does not benefit in area from 4x4; 3x3 is same area and faster.",
            "- For beta 48 at p1, 4x4 is clearly better for AET 250/300 and ties area while slightly faster at AET 350.",
            "- For observed p2/p3 pairs, b32 benefits from 4x4 at AET 300 and AET 350, but pays extra runtime.",
            "- For observed p2/p3 b48/e350 pairs, 3x3 and 4x4 tie on area; runtime differences are small/noisy.",
            "- The p2 grid is now complete; the only remaining dynamic-persistence grid gaps are p3 at AET 250 for both betas and p3 beta 48 at AET 300.",
        ]
    )

    (output_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    p1_dir = resolve(args.p1_dir)
    followup_dir = resolve(args.followup_dir)
    extra_dirs = [resolve(path) for path in args.extra_dir]
    output_dir = resolve(args.output_dir)
    runs = load_runs(p1_dir, followup_dir, extra_dirs)
    pairs = build_pairs(runs)
    missing = build_missing_pairs(runs)
    best = best_by_case(runs)

    output_dir.mkdir(parents=True, exist_ok=True)
    runs.to_csv(output_dir / "all_dynamic_grid_runs.csv", index=False)
    pairs.to_csv(output_dir / "paired_grid_comparisons.csv", index=False)
    missing.to_csv(output_dir / "missing_grid_pairs.csv", index=False)
    best.to_csv(output_dir / "best_by_beta_aet.csv", index=False)

    plot_p1_delta_matrix(pairs, output_dir / "p1_grid_delta_matrix.png")
    plot_all_pair_deltas(pairs, output_dir / "paired_grid_deltas.png")
    plot_tradeoff(runs, output_dir / "grid_tradeoff.png")
    write_index(output_dir, runs, pairs, missing, best)
    print(f"Wrote {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
