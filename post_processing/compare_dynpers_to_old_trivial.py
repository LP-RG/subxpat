#!/usr/bin/env python3
"""Compare dynamic-persistence runs against old trivial termination baselines."""

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
DEFAULT_DYN_DIR = (
    ROOT
    / "benchmarking/generated/zone_aet_i16_dynpers_patience_followup_20260512"
)
DEFAULT_OLD_RECORDS = (
    ROOT
    / "benchmarking/generated/zone_aet_i16_dynpers_p1_grid_sweep_20260508"
    / "plots/comparison_to_previous/comparison_records.csv"
)

BG = "#faf7f0"
GRID = "#ddd3c5"
TEXT = "#282522"
MUTED = "#776f64"
OLD = "#b8afa2"
NEW = "#2f8a5b"
TIME = "#2f6f9f"
BAD = "#c84d3f"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create old-trivial vs dynamic-persistence comparison plots."
    )
    parser.add_argument(
        "--dyn-dir",
        type=Path,
        default=DEFAULT_DYN_DIR,
        help="Dynamic-persistence experiment folder containing plots/run_summary_table.csv.",
    )
    parser.add_argument(
        "--old-records",
        type=Path,
        default=DEFAULT_OLD_RECORDS,
        help="CSV containing normalized previous-run records.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output folder. Defaults to <dyn-dir>/plots/comparison_to_old_trivial.",
    )
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


def load_dynamic_runs(dyn_dir: Path) -> pd.DataFrame:
    path = dyn_dir / "plots/run_summary_table.csv"
    if not path.exists():
        raise SystemExit(f"Missing dynamic run summary table: {path}")
    df = pd.read_csv(path)
    df["grid"] = df["grid_lpp"].astype(int).astype(str) + "x" + df["grid_ppo"].astype(int).astype(str)
    df["patience"] = "p" + df["pareto_candidate_patience"].astype(int).astype(str)
    df["dyn_label"] = (
        "b"
        + df["beta"].astype(int).astype(str)
        + " e"
        + df["aet"].astype(int).astype(str)
        + " "
        + df["grid"]
        + " "
        + df["patience"]
    )
    return df


def load_old_trivial(old_records: Path) -> pd.DataFrame:
    if not old_records.exists():
        raise SystemExit(f"Missing old comparison records: {old_records}")
    df = pd.read_csv(old_records)
    trivial = df[df["family"].eq("previous trivial")].copy()
    trivial["old_grid"] = trivial["grid"].astype(str)
    trivial["old_label"] = (
        "old trivial b"
        + trivial["beta"].astype(int).astype(str)
        + " e"
        + trivial["aet"].astype(int).astype(str)
        + " "
        + trivial["old_grid"]
    )
    return trivial


def build_comparison(dynamic: pd.DataFrame, trivial: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    key = ["beta", "aet", "alpha"]
    old_best = (
        trivial.sort_values(key + ["best_area", "runtime_hours"])
        .groupby(key, as_index=False)
        .first()
    )
    exact = dynamic.merge(
        old_best[
            key
            + [
                "old_grid",
                "old_label",
                "best_area",
                "runtime_hours",
                "iterations",
                "best_iteration",
                "stop_reason",
                "run",
            ]
        ],
        on=key,
        how="inner",
        suffixes=("_dyn", "_old"),
    )
    exact = exact.rename(
        columns={
            "best_area_old": "old_best_area",
            "runtime_hours_old": "old_runtime_hours",
            "iterations_old": "old_iterations",
            "best_iteration_old": "old_best_iteration",
            "stop_reason_old": "old_stop_reason",
            "run_old": "old_run",
            "best_area_dyn": "dyn_best_area",
            "runtime_hours_dyn": "dyn_runtime_hours",
            "iterations_dyn": "dyn_iterations",
            "best_iteration_dyn": "dyn_best_iteration",
            "stop_reason_dyn": "dyn_stop_reason",
            "run_dyn": "dyn_run",
        }
    )
    exact["area_delta"] = exact["dyn_best_area"] - exact["old_best_area"]
    exact["runtime_delta_h"] = exact["dyn_runtime_hours"] - exact["old_runtime_hours"]
    exact["area_delta_pct"] = 100 * exact["area_delta"] / exact["old_best_area"]
    exact["runtime_delta_pct"] = 100 * exact["runtime_delta_h"] / exact["old_runtime_hours"]
    exact = exact.sort_values(["beta", "aet", "grid", "patience"])

    best_exact = (
        exact.sort_values(["beta", "aet", "dyn_best_area", "dyn_runtime_hours"])
        .groupby(["beta", "aet", "alpha"], as_index=False)
        .first()
    )

    matched_keys = old_best[key].drop_duplicates()
    unmatched = dynamic.merge(matched_keys, on=key, how="left", indicator=True)
    unmatched = unmatched[unmatched["_merge"].eq("left_only")].drop(columns=["_merge"])
    unmatched = unmatched.sort_values(["beta", "aet", "grid", "patience"])
    return exact, best_exact, unmatched


def plot_best(best_exact: pd.DataFrame, output_path: Path) -> None:
    configure_style()
    if best_exact.empty:
        return

    labels = [
        f"b{int(row.beta)} e{int(row.aet)}\n{row.grid} {row.patience}"
        for row in best_exact.itertuples()
    ]
    x = list(range(len(best_exact)))
    width = 0.34

    fig, axes = plt.subplots(2, 1, figsize=(8.8, 7.2), sharex=True)
    fig.subplots_adjust(hspace=0.12)

    ax = axes[0]
    ax.bar([i - width / 2 for i in x], best_exact["old_best_area"], width, color=OLD, label="old trivial")
    ax.bar([i + width / 2 for i in x], best_exact["dyn_best_area"], width, color=NEW, label="dynamic persistence")
    ax.set_title("Best exact matches: area")
    ax.set_ylabel("Best area")
    ax.grid(True, axis="y")
    ax.legend(frameon=False, ncol=2, loc="upper right")
    ypad = max(8, (max(best_exact["old_best_area"].max(), best_exact["dyn_best_area"].max()) * 0.03))
    ax.set_ylim(
        min(best_exact["old_best_area"].min(), best_exact["dyn_best_area"].min()) - 25,
        max(best_exact["old_best_area"].max(), best_exact["dyn_best_area"].max()) + 35,
    )
    for i, row in enumerate(best_exact.itertuples()):
        color = NEW if row.area_delta < 0 else BAD
        ax.text(
            i,
            max(row.old_best_area, row.dyn_best_area) + ypad,
            f"{row.area_delta:+.1f}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    ax = axes[1]
    ax.bar([i - width / 2 for i in x], best_exact["old_runtime_hours"], width, color=OLD, label="old trivial")
    ax.bar([i + width / 2 for i in x], best_exact["dyn_runtime_hours"], width, color=TIME, label="dynamic persistence")
    ax.set_title("Best exact matches: runtime")
    ax.set_ylabel("Runtime (h)")
    ax.set_xticks(x, labels)
    ax.grid(True, axis="y")
    ax.set_ylim(0, max(best_exact["old_runtime_hours"].max(), best_exact["dyn_runtime_hours"].max()) + 7)
    for i, row in enumerate(best_exact.itertuples()):
        color = NEW if row.runtime_delta_h < 0 else BAD
        ax.text(
            i,
            max(row.old_runtime_hours, row.dyn_runtime_hours) + 1.0,
            f"{row.runtime_delta_h:+.1f}h",
            ha="center",
            va="bottom",
            fontsize=9,
            color=color,
            fontweight="bold",
        )

    fig.suptitle("Exact key: beta, AET, alpha. Lower is better.", y=0.985, fontsize=10, color=MUTED)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_all_exact(exact: pd.DataFrame, output_path: Path) -> None:
    configure_style()
    if exact.empty:
        return
    exact = exact.copy()
    exact["label"] = (
        "b"
        + exact["beta"].astype(int).astype(str)
        + " e"
        + exact["aet"].astype(int).astype(str)
        + " "
        + exact["grid"]
        + " "
        + exact["patience"]
    )
    fig, ax = plt.subplots(figsize=(10.8, 5.8))
    x = list(range(len(exact)))
    colors = [NEW if value < 0 else BAD for value in exact["area_delta"]]
    ax.bar(x, exact["area_delta"], color=colors, width=0.62)
    ax.axhline(0, color=TEXT, linewidth=1.0)
    ax.set_title("All exact matched dynamic runs vs old trivial")
    ax.set_ylabel("Area delta: dynamic - old trivial")
    ax.set_xticks(x, exact["label"], rotation=28, ha="right")
    ax.grid(True, axis="y")
    for i, row in enumerate(exact.itertuples()):
        va = "bottom" if row.area_delta >= 0 else "top"
        offset = 1.0 if row.area_delta >= 0 else -1.0
        ax.text(
            i,
            row.area_delta + offset,
            f"{row.area_delta:+.1f}\n{row.runtime_delta_h:+.1f}h",
            ha="center",
            va=va,
            fontsize=8,
            color=TEXT,
        )
    ax.text(
        0.01,
        -0.28,
        "Text labels show area delta and runtime delta. Negative area/time is better.",
        transform=ax.transAxes,
        fontsize=9,
        color=MUTED,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def format_delta(value: float, suffix: str = "") -> str:
    return f"{value:+.1f}{suffix}"


def write_index(output_dir: Path, exact: pd.DataFrame, best_exact: pd.DataFrame, unmatched: pd.DataFrame, dyn_dir: Path, old_records: Path) -> None:
    lines = [
        "# Dynamic Persistence vs Old Trivial",
        "",
        "Comparison for the dynamic-persistence runs in this experiment folder.",
        "",
        f"- Dynamic source: `{dyn_dir}`",
        f"- Old-trivial source table: `{old_records}`",
        "- Exact matching key: `beta`, `aet`, `alpha`.",
        "",
        "## Files",
        "",
        "- [best_exact_old_trivial_vs_dynpers.png](best_exact_old_trivial_vs_dynpers.png)",
        "- [all_exact_area_delta.png](all_exact_area_delta.png)",
        "- [exact_old_trivial_vs_dynpers_runs.csv](exact_old_trivial_vs_dynpers_runs.csv)",
        "- [best_exact_old_trivial_vs_dynpers.csv](best_exact_old_trivial_vs_dynpers.csv)",
        "- [unmatched_dynpers_runs.csv](unmatched_dynpers_runs.csv)",
        "",
        "## Best Exact Matches",
        "",
        "| Beta | AET | Alpha | Dynamic grid | Patience | Old area | Dynamic area | Area delta | Old runtime | Dynamic runtime | Runtime delta |",
        "|---:|---:|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in best_exact.itertuples():
        lines.append(
            f"| {int(row.beta)} | {int(row.aet)} | {int(row.alpha)} | {row.grid} | {row.patience} | "
            f"{row.old_best_area:.1f} | {row.dyn_best_area:.1f} | {format_delta(row.area_delta)} | "
            f"{row.old_runtime_hours:.1f}h | {row.dyn_runtime_hours:.1f}h | {format_delta(row.runtime_delta_h, 'h')} |"
        )

    lines.extend(
        [
            "",
            "## Coverage Note",
            "",
        ]
    )
    if unmatched.empty:
        lines.append("All dynamic runs had exact old-trivial matches.")
    else:
        unmatched_cases = ", ".join(
            f"b{int(row.beta)} e{int(row.aet)} alpha{int(row.alpha)} {row.grid} {row.patience}"
            for row in unmatched.itertuples()
        )
        lines.append(
            "The following dynamic runs do not have exact old-trivial baselines on disk: "
            f"{unmatched_cases}."
        )
        lines.append("")
        lines.append(
            "In practice this means the beta 48 follow-up runs are summarized in CSV, "
            "but are not included in the exact old-trivial comparison plot."
        )

    lines.extend(
        [
            "",
            "## All Exact Dynamic Runs",
            "",
            "| Beta | AET | Alpha | Grid | Patience | Dynamic area | Area delta | Dynamic runtime | Runtime delta |",
            "|---:|---:|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in exact.itertuples():
        lines.append(
            f"| {int(row.beta)} | {int(row.aet)} | {int(row.alpha)} | {row.grid} | {row.patience} | "
            f"{row.dyn_best_area:.1f} | {format_delta(row.area_delta)} | "
            f"{row.dyn_runtime_hours:.1f}h | {format_delta(row.runtime_delta_h, 'h')} |"
        )

    (output_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    dyn_dir = resolve(args.dyn_dir)
    old_records = resolve(args.old_records)
    output_dir = resolve(args.output_dir) if args.output_dir else dyn_dir / "plots/comparison_to_old_trivial"

    dynamic = load_dynamic_runs(dyn_dir)
    trivial = load_old_trivial(old_records)
    exact, best_exact, unmatched = build_comparison(dynamic, trivial)

    output_dir.mkdir(parents=True, exist_ok=True)
    exact.to_csv(output_dir / "exact_old_trivial_vs_dynpers_runs.csv", index=False)
    best_exact.to_csv(output_dir / "best_exact_old_trivial_vs_dynpers.csv", index=False)
    unmatched.to_csv(output_dir / "unmatched_dynpers_runs.csv", index=False)

    plot_best(best_exact, output_dir / "best_exact_old_trivial_vs_dynpers.png")
    plot_all_exact(exact, output_dir / "all_exact_area_delta.png")
    write_index(output_dir, exact, best_exact, unmatched, dyn_dir, old_records)
    print(f"Wrote {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
