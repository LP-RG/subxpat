#!/usr/bin/env python3
"""Build the May 2026 i16 dynamic-persistence weekly report."""

from __future__ import annotations

import os
import math
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
P1_DIR = ROOT / "benchmarking/generated/zone_aet_i16_dynpers_p1_grid_sweep_20260508"
FOLLOWUP_DIR = ROOT / "benchmarking/generated/zone_aet_i16_dynpers_patience_followup_20260512"
PREVIOUS_CMP = P1_DIR / "plots/comparison_to_previous/comparison_records.csv"
OUT_DIR = ROOT / "benchmarking/reports/2026-05-15_i16_dynpers_weekly_report"

BG = "#faf7f0"
GRID = "#ded5c7"
TEXT = "#292826"
MUTED = "#7b7469"
BLUE = "#2f6f9f"
GREEN = "#2f8a5b"
ORANGE = "#c97828"
RED = "#c84d3f"
GRAY = "#b8afa2"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "axes.edgecolor": "#c8bdae",
            "axes.labelcolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "text.color": TEXT,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.8,
        }
    )


def load_week_runs() -> pd.DataFrame:
    p1 = pd.read_csv(P1_DIR / "plots/run_summary_table.csv")
    p1["campaign"] = "2026-05-08 p1 sweep"
    followup = pd.read_csv(FOLLOWUP_DIR / "plots/run_summary_table.csv")
    followup["campaign"] = "2026-05-12 patience follow-up"
    week = pd.concat([p1, followup], ignore_index=True, sort=False)
    week["grid"] = week["grid_lpp"].astype(str) + "x" + week["grid_ppo"].astype(str)
    week["patience"] = "p" + week["pareto_candidate_patience"].astype(int).astype(str)
    week["case"] = (
        "b"
        + week["beta"].astype(int).astype(str)
        + " e"
        + week["aet"].astype(int).astype(str)
        + " "
        + week["grid"]
        + " "
        + week["patience"]
    )
    week["post_best_hours"] = week["runtime_hours"] - week["best_runtime_hours"]
    return week


def load_trivial_baseline() -> pd.DataFrame:
    previous = pd.read_csv(PREVIOUS_CMP)
    trivial = previous[previous["family"].eq("previous trivial")].copy()
    trivial["grid"] = trivial["grid"].astype(str)
    trivial["case"] = (
        "b"
        + trivial["beta"].astype(int).astype(str)
        + " e"
        + trivial["aet"].astype(int).astype(str)
        + " "
        + trivial["grid"]
        + " trivial"
    )
    return trivial


def best_by_beta_aet(week: pd.DataFrame) -> pd.DataFrame:
    ordered = week.sort_values(
        ["beta", "aet", "best_area", "runtime_hours", "iterations"],
        ascending=[True, True, True, True, True],
    )
    return ordered.groupby(["beta", "aet"], as_index=False).first()


def matched_beta32_vs_trivial(best_week: pd.DataFrame, trivial: pd.DataFrame) -> pd.DataFrame:
    base = trivial[trivial["beta"].eq(32)].copy()
    base = base.sort_values(["aet", "best_area", "runtime_hours"]).groupby("aet", as_index=False).first()
    week32 = best_week[best_week["beta"].eq(32)].copy()
    merged = week32.merge(
        base[
            [
                "aet",
                "best_area",
                "runtime_hours",
                "iterations",
                "best_iteration",
                "run",
            ]
        ],
        on="aet",
        suffixes=("_week", "_trivial"),
    )
    merged["area_delta"] = merged["best_area_week"] - merged["best_area_trivial"]
    merged["runtime_delta_h"] = merged["runtime_hours_week"] - merged["runtime_hours_trivial"]
    merged["area_improvement_pct"] = -100 * merged["area_delta"] / merged["best_area_trivial"]
    merged["runtime_speedup_pct"] = -100 * merged["runtime_delta_h"] / merged["runtime_hours_trivial"]
    return merged.sort_values("aet")


def save_week_tables(week: pd.DataFrame, best_week: pd.DataFrame, matched: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    week.to_csv(OUT_DIR / "week_runs.csv", index=False)
    best_week.to_csv(OUT_DIR / "best_week_by_beta_aet.csv", index=False)
    matched.to_csv(OUT_DIR / "matched_beta32_vs_old_trivial.csv", index=False)


def annotate_delta(ax: plt.Axes, x: float, y: float, text: str, color: str) -> None:
    ax.text(x, y, text, ha="center", va="bottom", fontsize=9, color=color, fontweight="bold")


def plot_matched_beta32(matched: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 7.2), sharex=True)
    fig.subplots_adjust(hspace=0.12)
    aet_labels = [str(int(v)) for v in matched["aet"]]
    x = list(range(len(matched)))
    width = 0.34

    ax = axes[0]
    old_area = matched["best_area_trivial"]
    new_area = matched["best_area_week"]
    ax.bar([i - width / 2 for i in x], old_area, width, label="old trivial", color=GRAY)
    ax.bar([i + width / 2 for i in x], new_area, width, label="best this week", color=GREEN)
    ax.set_title("Exact beta 32 comparison: area")
    ax.set_ylabel("Best area")
    ax.legend(frameon=False, ncol=2, loc="upper right")
    ax.set_ylim(max(0, min(old_area.min(), new_area.min()) - 45), max(old_area.max(), new_area.max()) + 55)
    for i, row in matched.iterrows():
        delta = row["area_delta"]
        color = GREEN if delta < 0 else RED
        label = f"{delta:+.1f}"
        annotate_delta(ax, x[i], max(row["best_area_trivial"], row["best_area_week"]) + 9, label, color)

    ax = axes[1]
    old_rt = matched["runtime_hours_trivial"]
    new_rt = matched["runtime_hours_week"]
    ax.bar([i - width / 2 for i in x], old_rt, width, label="old trivial", color=GRAY)
    ax.bar([i + width / 2 for i in x], new_rt, width, label="best this week", color=BLUE)
    ax.set_title("Exact beta 32 comparison: wall time")
    ax.set_ylabel("Runtime (h)")
    ax.set_xlabel("AET")
    ax.set_xticks(x, aet_labels)
    ax.set_ylim(0, max(old_rt.max(), new_rt.max()) + 8)
    for i, row in matched.iterrows():
        delta = row["runtime_delta_h"]
        color = GREEN if delta < 0 else RED
        label = f"{delta:+.1f}h"
        annotate_delta(ax, x[i], max(row["runtime_hours_trivial"], row["runtime_hours_week"]) + 1.2, label, color)

    fig.suptitle("Lower is better. Deltas are this week minus old trivial.", y=0.985, fontsize=10, color=MUTED)
    fig.savefig(OUT_DIR / "matched_beta32_vs_old_trivial.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_week_best_matrix(best_week: pd.DataFrame) -> None:
    betas = sorted(best_week["beta"].unique())
    aets = sorted(best_week["aet"].unique())
    fig, ax = plt.subplots(figsize=(9.2, 4.2))
    values = best_week.pivot(index="beta", columns="aet", values="best_area").reindex(index=betas, columns=aets)
    runtime = best_week.pivot(index="beta", columns="aet", values="runtime_hours").reindex(index=betas, columns=aets)
    labels = best_week.pivot(index="beta", columns="aet", values="case").reindex(index=betas, columns=aets)

    image = ax.imshow(values.values, cmap="YlGnBu_r", aspect="auto")
    finite_values = values.stack()
    color_midpoint = (finite_values.min() + finite_values.max()) / 2
    ax.set_title("Best result found this week")
    ax.set_xlabel("AET")
    ax.set_ylabel("Beta")
    ax.set_xticks(range(len(aets)), [str(int(a)) for a in aets])
    ax.set_yticks(range(len(betas)), [str(int(b)) for b in betas])
    ax.grid(False)

    for i, beta in enumerate(betas):
        for j, aet in enumerate(aets):
            area = values.loc[beta, aet]
            hours = runtime.loc[beta, aet]
            case = labels.loc[beta, aet]
            if pd.isna(area):
                continue
            small = str(case).split(" ", 2)[2]
            ax.text(
                j,
                i,
                f"{area:.1f}\n{hours:.1f}h\n{small}",
                ha="center",
                va="center",
                fontsize=9,
                color="#fffaf0" if area < color_midpoint else TEXT,
            )

    cbar = fig.colorbar(image, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label("Best area")
    fig.savefig(OUT_DIR / "best_week_matrix.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def pareto_frontier(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.sort_values(["runtime_hours", "best_area"]).copy()
    frontier_rows = []
    best_area = math.inf
    for _, row in ordered.iterrows():
        if row["best_area"] < best_area:
            frontier_rows.append(row)
            best_area = row["best_area"]
    return pd.DataFrame(frontier_rows)


def plot_tradeoff(week: pd.DataFrame, trivial: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 6.0))
    colors = {32: GREEN, 48: BLUE}
    markers = {"3x3": "o", "4x4": "s"}
    for (beta, grid), group in week.groupby(["beta", "grid"]):
        ax.scatter(
            group["runtime_hours"],
            group["best_area"],
            s=72,
            color=colors.get(int(beta), ORANGE),
            marker=markers.get(grid, "o"),
            edgecolor=BG,
            linewidth=0.8,
            alpha=0.92,
            label=f"week b{int(beta)} {grid}",
        )

    trivial32 = trivial[trivial["beta"].eq(32)]
    ax.scatter(
        trivial32["runtime_hours"],
        trivial32["best_area"],
        s=95,
        color=GRAY,
        marker="D",
        edgecolor=TEXT,
        linewidth=0.5,
        alpha=0.95,
        label="old trivial b32",
    )

    frontier = pareto_frontier(week)
    ax.plot(frontier["runtime_hours"], frontier["best_area"], color=TEXT, linewidth=1.4, alpha=0.65)
    for _, row in frontier.iterrows():
        ax.text(
            row["runtime_hours"] + 0.35,
            row["best_area"] - 2.5,
            f"b{int(row['beta'])} e{int(row['aet'])} {row['grid']} {row['patience']}",
            fontsize=8,
            color=TEXT,
        )

    ax.set_title("Area/runtime trade-off, May 8-13 runs")
    ax.set_xlabel("Runtime (h)")
    ax.set_ylabel("Best area")
    ax.legend(frameon=False, ncol=2, fontsize=8, loc="upper right")
    ax.invert_yaxis()
    ax.text(
        0.01,
        -0.16,
        "Lower-left is better. Gray diamonds are exact old trivial beta 32 baselines.",
        transform=ax.transAxes,
        fontsize=9,
        color=MUTED,
    )
    fig.savefig(OUT_DIR / "week_area_runtime_tradeoff.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def plot_patience_effect(week: pd.DataFrame) -> None:
    follow = week[week["campaign"].str.contains("follow-up") | week["patience"].eq("p1")].copy()
    follow = follow[
        follow["beta"].eq(32) & follow["aet"].isin([300, 350])
        | (follow["beta"].eq(48) & follow["aet"].eq(350))
    ]
    follow["family_case"] = (
        "b"
        + follow["beta"].astype(int).astype(str)
        + " e"
        + follow["aet"].astype(int).astype(str)
        + " "
        + follow["grid"]
    )
    keep_cases = sorted(
        set(
            week[week["campaign"].str.contains("follow-up")].assign(
                family_case=lambda df: (
                    "b"
                    + df["beta"].astype(int).astype(str)
                    + " e"
                    + df["aet"].astype(int).astype(str)
                    + " "
                    + df["grid"]
                )
            )["family_case"]
        )
    )
    follow = follow[follow["family_case"].isin(keep_cases)]

    fig, ax = plt.subplots(figsize=(9.8, 5.6))
    for idx, (case, group) in enumerate(follow.groupby("family_case")):
        group = group.sort_values("pareto_candidate_patience")
        ax.plot(
            group["pareto_candidate_patience"],
            group["best_area"],
            marker="o",
            linewidth=2.0,
            label=case,
            color=[GREEN, BLUE, ORANGE, RED][idx % 4],
        )
        for _, row in group.iterrows():
            ax.text(
                row["pareto_candidate_patience"],
                row["best_area"] - 1.8,
                f"{row['runtime_hours']:.1f}h",
                ha="center",
                va="top",
                fontsize=8,
                color=MUTED,
            )

    ax.set_title("What extra patience bought us")
    ax.set_xlabel("Pareto candidate patience")
    ax.set_ylabel("Best area")
    ax.set_xticks([1, 2, 3])
    ax.legend(frameon=False, fontsize=8, loc="best")
    ax.invert_yaxis()
    ax.text(
        0.01,
        -0.17,
        "Labels are total runtime. Lower area is better.",
        transform=ax.transAxes,
        fontsize=9,
        color=MUTED,
    )
    fig.savefig(OUT_DIR / "patience_effect.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def linked(path: Path) -> str:
    rel = path.relative_to(OUT_DIR)
    return str(rel)


def write_report(week: pd.DataFrame, best_week: pd.DataFrame, matched: pd.DataFrame, trivial: pd.DataFrame) -> None:
    p1 = week[week["pareto_candidate_patience"].eq(1)]
    follow = week[week["campaign"].str.contains("follow-up")]
    trivial_betas = sorted(int(beta) for beta in trivial["beta"].unique())
    exact_betas = sorted(set(best_week["beta"]).intersection(set(trivial["beta"])))
    missing_betas = sorted(set(best_week["beta"]) - set(trivial["beta"]))

    best_rows = []
    for _, row in best_week.sort_values(["beta", "aet"]).iterrows():
        best_rows.append(
            f"| b{int(row['beta'])} | {int(row['aet'])} | {row['best_area']:.1f} | "
            f"{row['runtime_hours']:.1f}h | {row['grid']} {row['patience']} |"
        )

    matched_rows = []
    for _, row in matched.iterrows():
        area_word = "better" if row["area_delta"] < 0 else "worse"
        rt_word = "faster" if row["runtime_delta_h"] < 0 else "slower"
        matched_rows.append(
            f"| {int(row['beta'])} | {int(row['aet'])} | {row['best_area_trivial']:.1f} | "
            f"{row['best_area_week']:.1f} | {row['area_delta']:+.1f} ({area_word}) | "
            f"{row['runtime_hours_trivial']:.1f}h | {row['runtime_hours_week']:.1f}h | "
            f"{row['runtime_delta_h']:+.1f}h ({rt_word}) |"
        )

    best_p1_area = p1["best_area"].min()
    best_follow_area = follow["best_area"].min()
    p1_status = p1["stop_reason"].value_counts().to_dict()
    all_dynpers = bool(week["dynamic_persistence"].all())

    report = [
        "# i16 Dynamic Persistence Weekly Report",
        "",
        "Period covered: 07.05.2026 to 15.05.2026.",
        "",
        "## What We Completed",
        "",
        f"- Completed the 12-run dynamic-persistence sweep from the tentative plan: 2 betas, 3 AETs, 2 grids, alpha 2.",
        f"- The sweep used `pareto` termination with `pareto_candidate_patience = 1`; stop reasons were `{p1_status}`.",
        f"- Dynamic persistence was enabled in every weekly run: `{all_dynpers}`.",
        "- The per-run plot folders now carry the extraction diagnostics we wanted: `trace_enriched.csv`, `row_timeline.csv`, and `persistence_coverage.png`.",
        f"- Added 8 follow-up runs with patience 2 and 3 on the cases where p1 either looked promising or ambiguous.",
        f"- Built per-run plots and group plots, and moved the date navigation layer to `benchmarking/by_date`.",
        "",
        "## Best Results This Week",
        "",
        "| Beta | AET | Best area | Runtime | Source |",
        "|---:|---:|---:|---:|---|",
        *best_rows,
        "",
        "## Exact Comparison To Old Trivial Baseline",
        "",
        "Exact old trivial matches exist on disk for beta 32 only. I did not force a beta 48 comparison because no old trivial beta 48 baseline is available locally.",
        "",
        f"Old trivial source: `{trivial.iloc[0]['run_dir'].split('/mul_i16_o16_')[0]}`.",
        "",
        "| Beta | AET | Old trivial area | Best this week area | Area delta | Old trivial runtime | This week runtime | Runtime delta |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
        *matched_rows,
        "",
        "## Interpretation",
        "",
        f"- Best p1-sweep area was `{best_p1_area:.1f}`; best follow-up area was `{best_follow_area:.1f}`.",
        "- The big win is beta 32 / AET 300: patience 2 on 4x4 found area 336.5, beating old trivial by 30.5 area units while also saving about 15.5h.",
        "- Beta 32 / AET 350 is also a clean win: area 318.2 versus old trivial 337.4, with roughly 17.3h less runtime.",
        "- Beta 32 / AET 250 went the wrong direction in area: this week was faster, but old trivial still had lower area.",
        "- Patience beyond 1 is only clearly useful in the beta 32 / AET 300 cases; elsewhere it often adds runtime without improving area.",
        "- Several runs still finish after the best area was already seen, so exporting/restoring the global-best circuit remains important.",
        "",
        "## Plots",
        "",
        f"- [matched_beta32_vs_old_trivial.png]({linked(OUT_DIR / 'matched_beta32_vs_old_trivial.png')})",
        f"- [best_week_matrix.png]({linked(OUT_DIR / 'best_week_matrix.png')})",
        f"- [week_area_runtime_tradeoff.png]({linked(OUT_DIR / 'week_area_runtime_tradeoff.png')})",
        f"- [patience_effect.png]({linked(OUT_DIR / 'patience_effect.png')})",
        "",
        "## Data",
        "",
        f"- [week_runs.csv]({linked(OUT_DIR / 'week_runs.csv')})",
        f"- [best_week_by_beta_aet.csv]({linked(OUT_DIR / 'best_week_by_beta_aet.csv')})",
        f"- [matched_beta32_vs_old_trivial.csv]({linked(OUT_DIR / 'matched_beta32_vs_old_trivial.csv')})",
        "",
        "## Baseline Coverage Note",
        "",
        f"- Old trivial betas on disk: `{trivial_betas}`.",
        f"- Exact old trivial betas overlapping this week's beta set: `{exact_betas}`.",
        f"- Weekly betas without exact old trivial baseline: `{missing_betas}`.",
    ]
    (OUT_DIR / "index.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    setup_style()
    week = load_week_runs()
    trivial = load_trivial_baseline()
    best_week = best_by_beta_aet(week)
    matched = matched_beta32_vs_trivial(best_week, trivial)
    save_week_tables(week, best_week, matched)
    plot_matched_beta32(matched)
    plot_week_best_matrix(best_week)
    plot_tradeoff(week, trivial)
    plot_patience_effect(week)
    write_report(week, best_week, matched, trivial)
    print(f"Wrote {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
