#!/usr/bin/env python3
"""Create the 2026-05-21 i16 dynamic-persistence parameter report."""

from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle

import compare_i16_dynamic_persistence as dyn_compare
import plot_run_artifacts as run_artifacts


ROOT = Path(__file__).resolve().parents[1]
COMPARISON_DIR = (
    ROOT
    / "benchmarking/generated/zone_aet_i16_dynpers_patience_followup_20260512/plots/lpp_ppo_comparison"
)
RUNS_CSV = COMPARISON_DIR / "all_dynamic_grid_runs.csv"
PAIRS_CSV = COMPARISON_DIR / "paired_grid_comparisons.csv"
OUT_DIR = ROOT / "benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report"

BG = "#faf7f0"
PANEL = "#fffaf3"
GRID = "#dfd3c2"
TEXT = "#292622"
MUTED = "#756b5e"
GREEN = "#2f8a5b"
BLUE = "#2f6f9f"
ORANGE = "#c97828"
RED = "#c84d3f"
GRAY = "#b8afa2"
PURPLE = "#7c5db3"


def setup_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": BG,
            "savefig.facecolor": BG,
            "axes.facecolor": PANEL,
            "axes.edgecolor": "#c8bdae",
            "axes.labelcolor": TEXT,
            "axes.titlecolor": TEXT,
            "axes.titlelocation": "left",
            "axes.titleweight": "bold",
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "text.color": TEXT,
            "font.family": "DejaVu Sans",
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.alpha": 0.82,
            "legend.frameon": False,
        }
    )


def parse_patience(value: object) -> int:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else int(float(value))


def load_runs() -> pd.DataFrame:
    runs = pd.read_csv(RUNS_CSV)
    runs["pnum"] = runs["patience"].map(parse_patience)
    runs["grid"] = runs["grid"].astype(str)
    runs["case"] = (
        "b"
        + runs["beta"].astype(int).astype(str)
        + " e"
        + runs["aet"].astype(int).astype(str)
        + " "
        + runs["grid"]
        + " p"
        + runs["pnum"].astype(str)
    )
    runs["row_timeline_png"] = runs["plots_dir"].map(lambda value: str(Path(value) / "row_timeline.png"))
    runs["row_timeline_exists"] = runs["row_timeline_png"].map(lambda value: Path(value).exists())
    return runs


def load_pairs() -> pd.DataFrame:
    pairs = pd.read_csv(PAIRS_CSV)
    return pairs


def best_by(runs: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    ordered = runs.sort_values(
        list(columns) + ["best_area", "runtime_hours", "iterations"],
        ascending=[True] * len(list(columns)) + [True, True, True],
    )
    return ordered.groupby(list(columns), as_index=False).first()


def format_hours(value: float) -> str:
    return f"{value:.1f}h"


def signed(value: float, unit: str = "") -> str:
    return f"{value:+.1f}{unit}"


def signed_pct(value: float) -> str:
    return f"{value:+.1f}%"


def relpath(path: Path) -> str:
    return os.path.relpath(path, OUT_DIR)


def safe_slug(value: object) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value)).strip("_")
    return slug or "artifact"


def markdown_link(label: str, path: Path) -> str:
    if not path.exists():
        return f"{label} missing"
    return f"[{label}]({relpath(path)})"


def pair_page_name(beta: int, aet: int, patience: int) -> str:
    return f"timeline_pair_b{beta}_e{aet}_p{patience}_3x3_vs_4x4.html"


def patience_history_page_name(grid: str, beta: int, aet: int) -> str:
    return f"timeline_history_{grid}_b{beta}_e{aet}.html"


def dynamic_fixed_page_name(grid: str, beta: int, aet: int) -> str:
    return f"dynamic_vs_fixed_{grid}_b{beta}_e{aet}.html"


def dynamic_fourway_page_name(beta: int, aet: int) -> str:
    return f"dynamic_vs_fixed_fourway_b{beta}_e{aet}.html"


def timeline_link(runs: pd.DataFrame, run: str, label: str = "timeline") -> str:
    matches = runs[runs["run"].eq(run)]
    if matches.empty:
        return "-"
    path = Path(matches.iloc[0]["row_timeline_png"])
    return markdown_link(label, path)


def timeline_url(runs: pd.DataFrame, run: str) -> str | None:
    matches = runs[runs["run"].eq(run)]
    if matches.empty:
        return None
    path = Path(matches.iloc[0]["row_timeline_png"])
    if not path.exists():
        return None
    return relpath(path)


def fixed_trace_path(summary_path: Path) -> Path:
    if summary_path.name.endswith("_summary.json"):
        return summary_path.with_name(summary_path.name.replace("_summary.json", "_trace.csv"))
    return summary_path.with_suffix(".csv")


def fixed_timeline_slug(summary_path: Path) -> str:
    for parent in summary_path.parents:
        if parent.name.startswith("mul_i16_o16_"):
            return safe_slug(parent.name)
    return safe_slug(summary_path.stem)


def ensure_fixed_row_timeline(summary_path_value: object) -> Path | None:
    if pd.isna(summary_path_value):
        return None
    summary_path = Path(str(summary_path_value))
    trace_path = fixed_trace_path(summary_path)
    if not summary_path.exists() or not trace_path.exists():
        return None

    output_dir = OUT_DIR / "fixed_timelines" / fixed_timeline_slug(summary_path)
    output_path = output_dir / "row_timeline.png"

    summary = run_artifacts.safe_read_json(summary_path)
    trace = run_artifacts.safe_read_csv(trace_path)
    if not summary or trace.empty:
        return None

    trace_table = run_artifacts.make_trace_table(trace, summary)
    rows = run_artifacts.make_grid_rows(pd.DataFrame(), trace_table)
    if trace_table.empty or rows.empty:
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    trace_table.to_csv(output_dir / "trace_enriched.csv", index=False)
    rows.to_csv(output_dir / "row_timeline.csv", index=False)
    return run_artifacts.plot_row_timeline(rows, summary, output_path)


def fixed_media_block(summary_path_value: object, heading: str) -> str:
    summary_path = Path(str(summary_path_value))
    timeline_path = ensure_fixed_row_timeline(summary_path_value)
    parts = []
    if timeline_path is not None and timeline_path.exists():
        image = relpath(timeline_path)
        parts.append(f"<a href='{image}'><img src='{image}' alt='{html.escape(heading)} row timeline'></a>")
    else:
        parts.append("<p>Fixed row timeline unavailable.</p>")
    parts.append(
        f"<p><a href='{relpath(summary_path)}'>summary JSON</a></p>"
        if summary_path.exists()
        else "<p>summary JSON missing</p>"
    )
    return "\n  ".join(parts)


def timeline_table(runs: pd.DataFrame, grid: str) -> pd.DataFrame:
    rows = []
    frame = runs[runs["grid"].eq(grid)].sort_values(["beta", "aet", "pnum"])
    for (beta, aet), group in frame.groupby(["beta", "aet"]):
        row = {"case": f"b{int(beta)} e{int(aet)}"}
        for patience in [1, 2, 3]:
            subset = group[group["pnum"].eq(patience)]
            if subset.empty:
                row[f"p{patience}"] = "-"
            else:
                run = str(subset.iloc[0]["run"])
                row[f"p{patience}"] = timeline_link(runs, run, f"p{patience}")
        rows.append(row)
    return pd.DataFrame(rows)


def symmetric_norm(values: np.ndarray) -> TwoSlopeNorm:
    finite = values[np.isfinite(values)]
    max_abs = float(np.max(np.abs(finite))) if finite.size else 1.0
    if max_abs < 1e-9:
        max_abs = 1.0
    return TwoSlopeNorm(vmin=-max_abs, vcenter=0.0, vmax=max_abs)


def pct_delta(new_value: float, old_value: float) -> float:
    if old_value == 0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100.0


def area_improvement_pct(new_area: float, old_area: float) -> float:
    if old_area == 0:
        return 0.0
    return ((old_area - new_area) / old_area) * 100.0


def runtime_improvement_pct(new_runtime: float, old_runtime: float) -> float:
    if old_runtime == 0:
        return 0.0
    return ((old_runtime - new_runtime) / old_runtime) * 100.0


def bar_colors(values: pd.Series, negative_good: bool = True) -> list[str]:
    colors = []
    for value in values:
        if abs(float(value)) < 1e-9:
            colors.append(GRAY)
        elif (value < 0 and negative_good) or (value > 0 and not negative_good):
            colors.append(GREEN)
        else:
            colors.append(RED)
    return colors


def plot_lpp_ppo_effect(pairs: pd.DataFrame) -> pd.DataFrame:
    p2 = pairs[pairs["patience"].eq(2)].copy()
    p2["label"] = "b" + p2["beta"].astype(int).astype(str) + " e" + p2["aet"].astype(int).astype(str)
    p2 = p2.sort_values(["beta", "aet"]).reset_index(drop=True)
    p2["area_improvement_4x4_vs_3x3_pct"] = p2.apply(
        lambda row: area_improvement_pct(float(row["area_4x4"]), float(row["area_3x3"])),
        axis=1,
    )
    p2["runtime_change_4x4_vs_3x3_pct"] = p2.apply(
        lambda row: pct_delta(float(row["runtime_4x4_h"]), float(row["runtime_3x3_h"])),
        axis=1,
    )
    p2["runtime_improvement_4x4_vs_3x3_pct"] = p2.apply(
        lambda row: runtime_improvement_pct(float(row["runtime_4x4_h"]), float(row["runtime_3x3_h"])),
        axis=1,
    )
    p2["area_reduction_4x4_vs_3x3"] = -p2["area_delta_4x4_minus_3x3"]
    p2["pair_page"] = p2.apply(
        lambda row: pair_page_name(int(row["beta"]), int(row["aet"]), int(row["patience"])),
        axis=1,
    )
    p2["area_delta_label"] = p2["area_delta_4x4_minus_3x3"].map(lambda value: signed(value))
    p2["area_reduction_label"] = p2["area_reduction_4x4_vs_3x3"].map(lambda value: signed(value))
    p2["runtime_delta_label"] = p2["runtime_delta_4x4_minus_3x3_h"].map(lambda value: signed(value, "h"))
    p2["area_improvement_pct_label"] = p2["area_improvement_4x4_vs_3x3_pct"].map(signed_pct)
    p2["runtime_change_pct_label"] = p2["runtime_change_4x4_vs_3x3_pct"].map(signed_pct)
    p2["runtime_improvement_pct_label"] = p2["runtime_improvement_4x4_vs_3x3_pct"].map(signed_pct)
    p2["recommendation"] = p2.apply(recommend_lpp_ppo, axis=1)
    p2.to_csv(OUT_DIR / "lpp_ppo_p2_effect.csv", index=False)
    p2[
        [
            "beta",
            "aet",
            "area_3x3",
            "area_4x4",
            "area_delta_4x4_minus_3x3",
            "area_reduction_4x4_vs_3x3",
            "area_improvement_4x4_vs_3x3_pct",
            "runtime_3x3_h",
            "runtime_4x4_h",
            "runtime_delta_4x4_minus_3x3_h",
            "runtime_change_4x4_vs_3x3_pct",
            "runtime_improvement_4x4_vs_3x3_pct",
            "recommendation",
        ]
    ].to_csv(OUT_DIR / "lpp_ppo_p2_decisions.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(11.2, 8.4), sharex=True)
    x = range(len(p2))

    ax = axes[0]
    values = p2["area_reduction_4x4_vs_3x3"]
    bars = ax.bar(x, values, color=bar_colors(values, negative_good=False), width=0.68)
    for bar, row in zip(bars, p2.itertuples()):
        bar.set_url(row.pair_page)
    ax.axhline(0, color=TEXT, linewidth=0.8)
    ax.set_title("LPP/PPO effect at patience p2: area reduction")
    ax.set_ylabel("Area reduction\n3x3 - 4x4")
    ax.grid(True, axis="y")
    for i, row in p2.iterrows():
        label = f"{signed(row.area_reduction_4x4_vs_3x3)}\n{signed_pct(row.area_improvement_4x4_vs_3x3_pct)}"
        ax.text(i, row.area_reduction_4x4_vs_3x3, label,
                ha="center", va="bottom" if row.area_reduction_4x4_vs_3x3 >= 0 else "top", fontsize=8.5)

    ax = axes[1]
    values = p2["runtime_delta_4x4_minus_3x3_h"]
    bars = ax.bar(x, values, color=bar_colors(values), width=0.68)
    for bar, row in zip(bars, p2.itertuples()):
        bar.set_url(row.pair_page)
    ax.axhline(0, color=TEXT, linewidth=0.8)
    ax.set_title("LPP/PPO effect at patience p2: runtime overhead")
    ax.set_ylabel("Runtime overhead\n4x4 - 3x3 [h]")
    ax.set_xticks(list(x), p2["label"], rotation=0)
    ax.grid(True, axis="y")
    for i, row in p2.iterrows():
        label = f"{signed(row.runtime_delta_4x4_minus_3x3_h, 'h')}\n{signed_pct(row.runtime_change_4x4_vs_3x3_pct)}"
        ax.text(i, row.runtime_delta_4x4_minus_3x3_h, label,
                ha="center", va="bottom" if row.runtime_delta_4x4_minus_3x3_h >= 0 else "top", fontsize=8.5)

    fig.suptitle(
        "Area uses 3x3 - 4x4, so positive means smaller area with 4x4. Runtime uses 4x4 - 3x3, so positive means runtime overhead.",
        color=MUTED,
        fontsize=10,
        y=0.985,
    )
    fig.savefig(OUT_DIR / "lpp_ppo_effect.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "lpp_ppo_effect.svg", bbox_inches="tight")
    plt.close(fig)
    return p2


def write_lpp_pair_pages(runs: pd.DataFrame, lpp: pd.DataFrame) -> None:
    for row in lpp.itertuples():
        run3 = runs[runs["run"].eq(row.run_3x3)]
        run4 = runs[runs["run"].eq(row.run_4x4)]
        if run3.empty or run4.empty:
            continue
        run3 = run3.iloc[0]
        run4 = run4.iloc[0]
        image3 = timeline_url(runs, str(row.run_3x3))
        image4 = timeline_url(runs, str(row.run_4x4))
        page = OUT_DIR / row.pair_page
        title = f"b{int(row.beta)} e{int(row.aet)} p{int(row.patience)}: 3x3 vs 4x4 timelines"
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
    }}
    a {{ color: {BLUE}; }}
    .summary {{
      display: grid;
      grid-template-columns: repeat(2, minmax(260px, 1fr));
      gap: 14px;
      margin: 18px 0;
    }}
    .card {{
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 12px;
      padding: 14px;
    }}
    .timelines {{
      display: grid;
      grid-template-columns: repeat(2, minmax(360px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    img {{
      max-width: 100%;
      border: 1px solid #d8cbbb;
      border-radius: 10px;
      background: white;
    }}
    .muted {{ color: {MUTED}; }}
  </style>
</head>
<body>
  <p><a href="index.md">Back to report</a></p>
  <h1>{html.escape(title)}</h1>
  <div class="summary">
    <div class="card">
      <h2>3x3</h2>
      <p>Run: <code>{html.escape(str(row.run_3x3))}</code></p>
      <p>Area: <strong>{float(row.area_3x3):.1f}</strong></p>
      <p>Runtime: <strong>{float(row.runtime_3x3_h):.1f}h</strong></p>
      <p>Iterations: <strong>{int(row.iterations_3x3)}</strong></p>
    </div>
    <div class="card">
      <h2>4x4</h2>
      <p>Run: <code>{html.escape(str(row.run_4x4))}</code></p>
      <p>Area: <strong>{float(row.area_4x4):.1f}</strong></p>
      <p>Runtime: <strong>{float(row.runtime_4x4_h):.1f}h</strong></p>
      <p>Iterations: <strong>{int(row.iterations_4x4)}</strong></p>
    </div>
  </div>
  <p>
    Area reduction: <strong>{float(row.area_reduction_4x4_vs_3x3):+.1f}</strong>
    ({float(row.area_improvement_4x4_vs_3x3_pct):+.1f}%).
    Runtime overhead: <strong>{float(row.runtime_delta_4x4_minus_3x3_h):+.1f}h</strong>
    ({float(row.runtime_change_4x4_vs_3x3_pct):+.1f}%).
  </p>
  <div class="timelines">
    <div>
      <h2>3x3 row timeline</h2>
      {"<a href='" + image3 + "'><img src='" + image3 + "' alt='3x3 row timeline'></a>" if image3 else "<p>Missing row timeline.</p>"}
    </div>
    <div>
      <h2>4x4 row timeline</h2>
      {"<a href='" + image4 + "'><img src='" + image4 + "' alt='4x4 row timeline'></a>" if image4 else "<p>Missing row timeline.</p>"}
    </div>
  </div>
</body>
</html>
"""
        page.write_text(body, encoding="utf-8")


def write_patience_history_pages(runs: pd.DataFrame, grid: str) -> None:
    frame = runs[runs["grid"].eq(grid)].sort_values(["beta", "aet", "pnum"])
    for (beta, aet), group in frame.groupby(["beta", "aet"]):
        title = f"{grid} patience history: b{int(beta)} e{int(aet)}"
        cards = []
        for patience in [1, 2, 3]:
            subset = group[group["pnum"].eq(patience)]
            if subset.empty:
                cards.append(
                    f"""<section class="card missing">
  <h2>p{patience}</h2>
  <p>No completed run in this comparison set.</p>
</section>"""
                )
                continue
            row = subset.iloc[0]
            image = timeline_url(runs, str(row.run))
            image_html = (
                f"<a href='{image}'><img src='{image}' alt='p{patience} row timeline'></a>"
                if image
                else "<p>Missing row timeline.</p>"
            )
            cards.append(
                f"""<section class="card">
  <h2>p{patience}</h2>
  <p>Run: <code>{html.escape(str(row.run))}</code></p>
  <p>Area: <strong>{float(row.best_area):.1f}</strong> · Runtime: <strong>{float(row.runtime_hours):.1f}h</strong> · Iterations: <strong>{int(row.iterations)}</strong></p>
  {image_html}
</section>"""
            )

        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
    }}
    a {{ color: {BLUE}; }}
    .muted {{ color: {MUTED}; }}
    .history {{
      display: grid;
      grid-template-columns: repeat(3, minmax(340px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .card {{
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 14px;
      padding: 14px;
      min-height: 180px;
    }}
    .missing {{
      opacity: 0.62;
    }}
    img {{
      width: 100%;
      border: 1px solid #d8cbbb;
      border-radius: 10px;
      background: white;
    }}
    @media (max-width: 1200px) {{
      .history {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <p><a href="index.md">Back to report</a> · <a href="patience_effect_{grid}_clickable.html">Back to clickable {grid} heatmap</a></p>
  <h1>{html.escape(title)}</h1>
  <div class="history">
    {"".join(cards)}
  </div>
</body>
</html>
"""
        (OUT_DIR / patience_history_page_name(grid, int(beta), int(aet))).write_text(body, encoding="utf-8")


def svg_body(svg_path: Path) -> str:
    text = svg_path.read_text(encoding="utf-8")
    start = text.find("<svg")
    return text[start:] if start >= 0 else text


def write_clickable_svg_page(svg_name: str, html_name: str, title: str) -> None:
    svg_path = OUT_DIR / svg_name
    if not svg_path.exists():
        return
    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
    }}
    a {{ color: {BLUE}; }}
    .plot {{
      max-width: 1280px;
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 14px;
      padding: 12px;
      overflow: auto;
    }}
    svg {{
      width: 100%;
      height: auto;
      display: block;
    }}
    .muted {{ color: {MUTED}; }}
  </style>
</head>
<body>
  <p><a href="index.md">Back to report</a></p>
  <h1>{html.escape(title)}</h1>
  <div class="plot">
{svg_body(svg_path)}
  </div>
</body>
</html>
"""
    (OUT_DIR / html_name).write_text(body, encoding="utf-8")


def write_clickable_plot_pages() -> None:
    write_clickable_svg_page(
        "lpp_ppo_effect.svg",
        "lpp_ppo_effect_clickable.html",
        "Clickable LPP/PPO Effect",
    )
    write_clickable_svg_page(
        "patience_effect_3x3.svg",
        "patience_effect_3x3_clickable.html",
        "Clickable Patience Effect: 3x3",
    )
    write_clickable_svg_page(
        "patience_effect_4x4.svg",
        "patience_effect_4x4_clickable.html",
        "Clickable Patience Effect: 4x4",
    )


def decision_plot_entries() -> list[tuple[str, str, str, str]]:
    return [
        (
            "01_lpp_ppo_effect_clickable.html",
            "lpp_ppo_effect_clickable.html",
            "1. LPP/PPO decision",
            "Compare 3x3 vs 4x4 at p2. Working default: use 3x3 for speed; escalate to 4x4 when the case is area-critical or known to benefit.",
        ),
        (
            "02_patience_effect_3x3_clickable.html",
            "patience_effect_3x3_clickable.html",
            "2a. Patience deltas for 3x3",
            "Compare p1/p2/p3 for fixed 3x3. The heatmap cells open p1/p2/p3 timeline histories.",
        ),
        (
            "03_patience_effect_4x4_clickable.html",
            "patience_effect_4x4_clickable.html",
            "2b. Patience deltas for 4x4",
            "Compare p1/p2/p3 for fixed 4x4. Use this next to the 3x3 patience plot before choosing patience globally.",
        ),
        (
            "04_dynamic_vs_fixed_persistence_fourway_clickable.html",
            "dynamic_vs_fixed_persistence_fourway_clickable.html",
            "3. Fixed none/trivial vs dynamic persistence",
            "Four-way view: fixed none, fixed trivial, dynamic 3x3, and dynamic 4x4. Click a case for side-by-side timelines.",
        ),
        (
            "05_dynamic_vs_fixed_persistence_3x3_clickable.html",
            "dynamic_vs_fixed_persistence_3x3_clickable.html",
            "3a. Dynamic 3x3 vs fixed baselines",
            "Grid-specific persistence comparison for dynamic 3x3.",
        ),
        (
            "06_dynamic_vs_fixed_persistence_4x4_clickable.html",
            "dynamic_vs_fixed_persistence_4x4_clickable.html",
            "3b. Dynamic 4x4 vs fixed baselines",
            "Grid-specific persistence comparison for dynamic 4x4.",
        ),
    ]


def decision_copy_html(source_name: str, output_name: str) -> bool:
    source = OUT_DIR / source_name
    if not source.exists():
        return False
    target_dir = OUT_DIR / "decision_plots"
    target_dir.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8")
    if "<base " not in text:
        text = text.replace("<head>", '<head>\n  <base href="../">', 1)
    text = text.replace(
        '<p><a href="index.md">Back to report</a></p>',
        '<p><a href="decision_plots/index.html">Back to decision hub</a> · <a href="index.md">Back to report</a></p>',
        1,
    )
    (target_dir / output_name).write_text(text, encoding="utf-8")
    return True


def write_decision_plot_hub() -> None:
    target_dir = OUT_DIR / "decision_plots"
    target_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    markdown_rows = [
        "# i16 Decision Plot Hub",
        "",
        "This folder groups the clickable plots for the three current decisions.",
        "",
    ]
    for output_name, source_name, title, description in decision_plot_entries():
        available = decision_copy_html(source_name, output_name)
        href = output_name if available else f"../{source_name}"
        rows.append(
            f"""<section class="card">
  <div class="kicker">{html.escape(title)}</div>
  <p>{html.escape(description)}</p>
  <a class="button" href="{html.escape(href)}">Open clickable plot</a>
</section>"""
        )
        markdown_rows.extend(
            [
                f"## {title}",
                "",
                description,
                "",
                f"- [Open clickable plot]({href})",
                f"- [Source page](../{source_name})",
                "",
            ]
        )

    body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>i16 Decision Plot Hub</title>
  <style>
    body {{
      margin: 28px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
      line-height: 1.45;
    }}
    a {{ color: {BLUE}; }}
    .lede {{ color: {MUTED}; max-width: 920px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(260px, 1fr));
      gap: 18px;
      margin-top: 22px;
    }}
    .card {{
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 16px;
      padding: 18px;
      min-height: 160px;
      box-shadow: 0 8px 22px rgba(41, 38, 34, 0.06);
    }}
    .kicker {{
      color: {ORANGE};
      font-weight: 800;
      letter-spacing: 0.01em;
    }}
    .button {{
      display: inline-block;
      margin-top: 10px;
      padding: 9px 12px;
      border-radius: 10px;
      background: {TEXT};
      color: {BG};
      text-decoration: none;
      font-weight: 700;
    }}
    .decision {{
      max-width: 920px;
      background: #fff4df;
      border: 1px solid #e5c99a;
      border-radius: 16px;
      padding: 14px 18px;
      margin-top: 18px;
    }}
    @media (max-width: 1080px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <p><a href="../index.md">Back to report</a></p>
  <h1>i16 Decision Plot Hub</h1>
  <p class="lede">One folder for the clickable plots connected to the current decisions: LPP/PPO, patience, and default-vs-dynamic persistence.</p>
  <section class="decision">
    <strong>Current read:</strong> use <code>3x3</code> as the default speed-first LPP/PPO setting, keep <code>4x4</code> as the area-seeking option for cases where it demonstrably helps; use <code>p2</code> as the practical patience default unless a new run shows p3 buying area.
  </section>
  <div class="grid">
    {"".join(rows)}
  </div>
</body>
</html>
"""
    (target_dir / "index.html").write_text(body, encoding="utf-8")
    (target_dir / "index.md").write_text("\n".join(markdown_rows), encoding="utf-8")


def recommend_lpp_ppo(row: pd.Series) -> str:
    area_delta = float(row["area_delta_4x4_minus_3x3"])
    runtime_delta = float(row["runtime_delta_4x4_minus_3x3_h"])
    if area_delta < -1e-6:
        return "4x4 for area"
    if area_delta > 1e-6:
        return "3x3 for area"
    if runtime_delta < -1e-6:
        return "4x4: same area, faster"
    if runtime_delta > 1e-6:
        return "3x3: same area, faster"
    return "tie"


def plot_patience_effect(runs: pd.DataFrame) -> pd.DataFrame:
    best = best_by(runs, ["beta", "aet", "pnum"])
    best.to_csv(OUT_DIR / "best_by_patience.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 8.2), sharex=True)
    colors = {(32, 250): GREEN, (32, 300): BLUE, (32, 350): ORANGE, (48, 250): PURPLE, (48, 300): RED, (48, 350): "#607d8b"}
    markers = {32: "o", 48: "s"}

    for (beta, aet), group in best.groupby(["beta", "aet"]):
        group = group.sort_values("pnum")
        label = f"b{int(beta)} e{int(aet)}"
        color = colors.get((int(beta), int(aet)), TEXT)
        axes[0].plot(group["pnum"], group["best_area"], marker=markers.get(int(beta), "o"), color=color, linewidth=2.0, label=label)
        axes[1].plot(group["pnum"], group["runtime_hours"], marker=markers.get(int(beta), "o"), color=color, linewidth=2.0, label=label)
        for _, row in group.iterrows():
            axes[0].text(row.pnum, row.best_area, f"{row.best_area:.1f}", fontsize=8, ha="center", va="bottom")
            axes[1].text(row.pnum, row.runtime_hours, format_hours(row.runtime_hours), fontsize=8, ha="center", va="bottom")

    axes[0].set_title("Patience effect: best area available at each patience")
    axes[0].set_ylabel("Best area")
    axes[0].grid(True, axis="y")
    axes[1].set_title("Patience effect: runtime of the best-area run")
    axes[1].set_ylabel("Runtime [h]")
    axes[1].set_xlabel("Pareto candidate patience")
    axes[1].set_xticks([1, 2, 3], ["p1", "p2", "p3"])
    axes[1].grid(True, axis="y")
    axes[0].legend(ncol=3, loc="best", fontsize=8)
    fig.suptitle("p2 is the useful step. Observed p3 cases do not improve area over p2.", color=MUTED, fontsize=10, y=0.985)
    fig.savefig(OUT_DIR / "patience_effect.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return best


def plot_fixed_grid_patience_effect(runs: pd.DataFrame, grid: str) -> pd.DataFrame:
    frame = runs[runs["grid"].eq(grid)].copy()
    frame = frame.sort_values(["beta", "aet", "pnum"]).reset_index(drop=True)
    records = []
    for (beta, aet), group in frame.groupby(["beta", "aet"]):
        baseline = group[group["pnum"].eq(1)]
        if baseline.empty:
            continue
        p1 = baseline.iloc[0]
        for _, row in group.iterrows():
            records.append(
                {
                    "beta": int(beta),
                    "aet": int(aet),
                    "grid": grid,
                    "patience": int(row.pnum),
                    "best_area": float(row.best_area),
                    "runtime_hours": float(row.runtime_hours),
                    "iterations": int(row.iterations),
                    "area_improvement_vs_p1_pct": area_improvement_pct(float(row.best_area), float(p1.best_area)),
                    "runtime_change_vs_p1_pct": pct_delta(float(row.runtime_hours), float(p1.runtime_hours)),
                    "runtime_improvement_vs_p1_pct": runtime_improvement_pct(float(row.runtime_hours), float(p1.runtime_hours)),
                    "row_timeline_png": str(row.row_timeline_png),
                    "run": row.run,
                }
            )
    table = pd.DataFrame(records).sort_values(["beta", "aet", "patience"]).reset_index(drop=True)
    safe_grid = grid.replace("x", "x")
    table.to_csv(OUT_DIR / f"patience_effect_{safe_grid}.csv", index=False)

    cases = sorted(table[["beta", "aet"]].drop_duplicates().itertuples(index=False), key=lambda row: (row.beta, row.aet))
    patience_values = [1, 2, 3]
    area_values = np.full((len(cases), len(patience_values)), np.nan)
    runtime_values = np.full((len(cases), len(patience_values)), np.nan)
    area_labels = [["" for _ in patience_values] for _ in cases]
    runtime_labels = [["" for _ in patience_values] for _ in cases]
    cell_urls: list[list[str | None]] = [[None for _ in patience_values] for _ in cases]

    for i, case in enumerate(cases):
        group = table[(table["beta"].eq(case.beta)) & (table["aet"].eq(case.aet))]
        for j, patience in enumerate(patience_values):
            row = group[group["patience"].eq(patience)]
            if row.empty:
                area_labels[i][j] = "missing"
                runtime_labels[i][j] = "missing"
                continue
            item = row.iloc[0]
            area_values[i, j] = float(item["area_improvement_vs_p1_pct"])
            runtime_values[i, j] = float(item["runtime_change_vs_p1_pct"])
            cell_urls[i][j] = patience_history_page_name(grid, int(case.beta), int(case.aet))
            if patience == 1:
                area_labels[i][j] = f"{item.best_area:.1f}\nbase"
                runtime_labels[i][j] = f"{item.runtime_hours:.1f}h\nbase"
            else:
                area_labels[i][j] = f"{item.best_area:.1f}\n{signed_pct(item.area_improvement_vs_p1_pct)}"
                runtime_labels[i][j] = f"{item.runtime_hours:.1f}h\n{signed_pct(item.runtime_change_vs_p1_pct)}"

    area_cmap = LinearSegmentedColormap.from_list("area_improvement", [RED, "#f0dfa4", GREEN])
    runtime_cmap = LinearSegmentedColormap.from_list("runtime_overhead", [GREEN, "#f0dfa4", RED])
    area_cmap.set_bad("#eee6da")
    runtime_cmap.set_bad("#eee6da")

    fig, axes = plt.subplots(1, 2, figsize=(12.2, 6.0), sharey=True)
    ylabels = [f"b{int(case.beta)} e{int(case.aet)}" for case in cases]
    xlabels = [f"p{value}" for value in patience_values]

    panels = [
        (axes[0], area_values, area_labels, area_cmap, symmetric_norm(area_values), "Area result", "Area improvement vs p1 [%]"),
        (axes[1], runtime_values, runtime_labels, runtime_cmap, symmetric_norm(runtime_values), "Runtime result", "Runtime overhead vs p1 [%]"),
    ]
    for ax, values, labels, cmap, norm, title, colorbar_label in panels:
        image = ax.imshow(np.ma.masked_invalid(values), cmap=cmap, norm=norm, aspect="auto")
        ax.set_title(title)
        ax.set_xticks(range(len(xlabels)), xlabels)
        ax.set_yticks(range(len(ylabels)), ylabels)
        ax.tick_params(axis="both", length=0)
        ax.set_xticks(np.arange(-0.5, len(xlabels), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(ylabels), 1), minor=True)
        ax.grid(which="minor", color=BG, linewidth=2.0)
        for i in range(len(ylabels)):
            for j in range(len(xlabels)):
                ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=8.5)
                if cell_urls[i][j]:
                    link_patch = Rectangle(
                        (j - 0.5, i - 0.5),
                        1,
                        1,
                        facecolor="#ffffff",
                        edgecolor="none",
                        alpha=0.001,
                    )
                    link_patch.set_url(cell_urls[i][j])
                    ax.add_patch(link_patch)
        colorbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.03)
        colorbar.set_label(colorbar_label, fontsize=8.5)

    axes[0].set_ylabel("Case")
    fig.suptitle(
        f"Patience comparison for fixed LPP/PPO {grid}. Area is reduction vs p1; runtime is overhead vs p1.",
        color=MUTED,
        fontsize=10,
        y=0.985,
    )
    fig.savefig(OUT_DIR / f"patience_effect_{safe_grid}.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / f"patience_effect_{safe_grid}.svg", bbox_inches="tight")
    plt.close(fig)
    return table


def plot_beta_effect(runs: pd.DataFrame) -> pd.DataFrame:
    p2 = runs[runs["pnum"].eq(2)].copy()
    rows = []
    for (aet, grid), group in p2.groupby(["aet", "grid"]):
        by_beta = group.set_index("beta")
        if 32 not in by_beta.index or 48 not in by_beta.index:
            continue
        b32 = by_beta.loc[32]
        b48 = by_beta.loc[48]
        rows.append(
            {
                "aet": int(aet),
                "grid": grid,
                "label": f"e{int(aet)} {grid}",
                "area_beta32": float(b32.best_area),
                "area_beta48": float(b48.best_area),
                "area_delta_b48_minus_b32": float(b48.best_area) - float(b32.best_area),
                "runtime_beta32_h": float(b32.runtime_hours),
                "runtime_beta48_h": float(b48.runtime_hours),
                "runtime_delta_b48_minus_b32_h": float(b48.runtime_hours) - float(b32.runtime_hours),
            }
        )
    beta_cmp = pd.DataFrame(rows).sort_values(["aet", "grid"]).reset_index(drop=True)
    beta_cmp.to_csv(OUT_DIR / "beta_p2_effect.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.5), sharex=True)
    x = range(len(beta_cmp))
    ax = axes[0]
    values = beta_cmp["area_delta_b48_minus_b32"]
    ax.bar(x, values, color=bar_colors(values), width=0.68)
    ax.axhline(0, color=TEXT, linewidth=0.8)
    ax.set_title("Beta effect at patience p2: area")
    ax.set_ylabel("Area delta\nb48 - b32")
    ax.grid(True, axis="y")
    for i, row in beta_cmp.iterrows():
        ax.text(i, row.area_delta_b48_minus_b32, signed(row.area_delta_b48_minus_b32),
                ha="center", va="bottom" if row.area_delta_b48_minus_b32 >= 0 else "top", fontsize=9)

    ax = axes[1]
    values = beta_cmp["runtime_delta_b48_minus_b32_h"]
    ax.bar(x, values, color=bar_colors(values), width=0.68)
    ax.axhline(0, color=TEXT, linewidth=0.8)
    ax.set_title("Beta effect at patience p2: runtime")
    ax.set_ylabel("Runtime delta\nb48 - b32 [h]")
    ax.set_xticks(list(x), beta_cmp["label"], rotation=0)
    ax.grid(True, axis="y")
    for i, row in beta_cmp.iterrows():
        ax.text(i, row.runtime_delta_b48_minus_b32_h, signed(row.runtime_delta_b48_minus_b32_h, "h"),
                ha="center", va="bottom" if row.runtime_delta_b48_minus_b32_h >= 0 else "top", fontsize=9)

    fig.suptitle("Negative deltas favor beta 48. Positive deltas favor beta 32.", color=MUTED, fontsize=10, y=0.985)
    fig.savefig(OUT_DIR / "beta_effect.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return beta_cmp


def plot_aet_effect(runs: pd.DataFrame) -> pd.DataFrame:
    p2_best = best_by(runs[runs["pnum"].eq(2)], ["beta", "aet"])
    p2_best.to_csv(OUT_DIR / "aet_best_p2.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(10.4, 7.7), sharex=True)
    for beta, group in p2_best.groupby("beta"):
        group = group.sort_values("aet")
        color = GREEN if int(beta) == 32 else BLUE
        axes[0].plot(group["aet"], group["best_area"], marker="o", linewidth=2.4, color=color, label=f"beta {int(beta)}")
        axes[1].plot(group["aet"], group["runtime_hours"], marker="o", linewidth=2.4, color=color, label=f"beta {int(beta)}")
        for _, row in group.iterrows():
            axes[0].text(row.aet, row.best_area, f"{row.best_area:.1f}\n{row.grid}", ha="center", va="bottom", fontsize=8)
            axes[1].text(row.aet, row.runtime_hours, format_hours(row.runtime_hours), ha="center", va="bottom", fontsize=8)

    axes[0].set_title("AET effect at patience p2: best area over 3x3/4x4")
    axes[0].set_ylabel("Best area")
    axes[0].grid(True, axis="y")
    axes[0].legend(loc="best")
    axes[1].set_title("AET effect at patience p2: runtime of best-area run")
    axes[1].set_ylabel("Runtime [h]")
    axes[1].set_xlabel("AET")
    axes[1].set_xticks([250, 300, 350])
    axes[1].grid(True, axis="y")
    fig.suptitle("AET is the error budget. The observed search is not guaranteed monotonic because termination/search path also changes.", color=MUTED, fontsize=10, y=0.985)
    fig.savefig(OUT_DIR / "aet_effect.png", dpi=220, bbox_inches="tight")
    plt.close(fig)
    return p2_best


def build_dynamic_vs_fixed_persistence(runs: pd.DataFrame, dynamic_grid: str | None = None) -> pd.DataFrame:
    dynamic_source = runs.copy()
    if dynamic_grid is not None:
        dynamic_source = dynamic_source[dynamic_source["grid"].eq(dynamic_grid)].copy()
    if dynamic_source.empty:
        return pd.DataFrame()

    previous = dyn_compare.discover_records(dyn_compare.DEFAULT_SWEEP)
    if previous.empty:
        return pd.DataFrame()

    dynamic_best = best_by(dynamic_source, ["beta", "aet"]).copy()
    dynamic_best = dynamic_best.rename(
        columns={
            "best_area": "dynamic_best_area",
            "runtime_hours": "dynamic_runtime_h",
            "iterations": "dynamic_iterations",
            "grid": "dynamic_grid",
            "pnum": "dynamic_patience",
            "run": "dynamic_run",
            "row_timeline_png": "dynamic_row_timeline_png",
        }
    )

    fixed = previous[
        (~previous["dynamic_persistence"].astype(bool))
        & previous["family"].isin(["previous none", "previous trivial"])
    ].copy()
    matched_rows = []
    for dyn_row in dynamic_best.itertuples():
        subset = fixed[(fixed["beta"].eq(dyn_row.beta)) & (fixed["aet"].eq(dyn_row.aet))]
        if subset.empty:
            continue
        record = {
            "beta": int(dyn_row.beta),
            "aet": int(dyn_row.aet),
            "dynamic_grid": dyn_row.dynamic_grid,
            "dynamic_setting": f"{dyn_row.dynamic_grid} p{int(dyn_row.dynamic_patience)}",
            "dynamic_best_area": float(dyn_row.dynamic_best_area),
            "dynamic_runtime_h": float(dyn_row.dynamic_runtime_h),
            "dynamic_iterations": int(dyn_row.dynamic_iterations),
            "dynamic_run": dyn_row.dynamic_run,
            "dynamic_row_timeline_png": dyn_row.dynamic_row_timeline_png,
        }
        for family, prefix in [("previous none", "none"), ("previous trivial", "trivial")]:
            baseline = subset[subset["family"].eq(family)]
            if baseline.empty:
                continue
            baseline = baseline.sort_values(["best_area", "runtime_hours", "iterations"]).iloc[0]
            record[f"{prefix}_area"] = float(baseline.best_area)
            record[f"{prefix}_runtime_h"] = float(baseline.runtime_hours)
            record[f"{prefix}_iterations"] = int(baseline.iterations)
            record[f"{prefix}_run"] = baseline.run
            record[f"{prefix}_summary_path"] = baseline.summary_path
            record[f"{prefix}_run_dir"] = baseline.run_dir
            record[f"area_reduction_vs_{prefix}"] = float(baseline.best_area) - float(dyn_row.dynamic_best_area)
            record[f"area_improvement_vs_{prefix}_pct"] = area_improvement_pct(
                float(dyn_row.dynamic_best_area), float(baseline.best_area)
            )
            record[f"runtime_overhead_vs_{prefix}_h"] = float(dyn_row.dynamic_runtime_h) - float(baseline.runtime_hours)
            record[f"runtime_overhead_vs_{prefix}_pct"] = pct_delta(
                float(dyn_row.dynamic_runtime_h), float(baseline.runtime_hours)
            )
        matched_rows.append(record)

    matched = pd.DataFrame(matched_rows).sort_values(["beta", "aet"]).reset_index(drop=True)
    return matched


def write_dynamic_vs_fixed_pages(matched: pd.DataFrame, grid_label: str, back_link: str) -> None:
    if matched.empty:
        return
    for row in matched.itertuples():
        title = f"Dynamic vs fixed persistence: {grid_label} b{int(row.beta)} e{int(row.aet)}"
        dynamic_image = relpath(Path(row.dynamic_row_timeline_png)) if Path(row.dynamic_row_timeline_png).exists() else None
        cards = []
        for prefix, heading in [("none", "Fixed none"), ("trivial", "Fixed trivial")]:
            area = getattr(row, f"{prefix}_area", np.nan)
            if pd.isna(area):
                continue
            summary_path = Path(getattr(row, f"{prefix}_summary_path"))
            media = fixed_media_block(summary_path, heading)
            cards.append(
                f"""<section class="card">
  <h2>{heading}</h2>
  <p>Run: <code>{html.escape(str(getattr(row, f'{prefix}_run')))}</code></p>
  <p>Area: <strong>{float(area):.1f}</strong> · Runtime: <strong>{float(getattr(row, f'{prefix}_runtime_h')):.1f}h</strong> · Iterations: <strong>{int(getattr(row, f'{prefix}_iterations'))}</strong></p>
  {media}
</section>"""
            )
        dynamic_card_image = (
            f"<a href='{dynamic_image}'><img src='{dynamic_image}' alt='dynamic row timeline'></a>"
            if dynamic_image
            else "<p>Missing dynamic row timeline.</p>"
        )
        cards.append(
            f"""<section class="card wide">
  <h2>Dynamic {html.escape(str(row.dynamic_setting))}</h2>
  <p>Run: <code>{html.escape(str(row.dynamic_run))}</code></p>
  <p>Area: <strong>{float(row.dynamic_best_area):.1f}</strong> · Runtime: <strong>{float(row.dynamic_runtime_h):.1f}h</strong> · Iterations: <strong>{int(row.dynamic_iterations)}</strong></p>
  {dynamic_card_image}
</section>"""
        )
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
    }}
    a {{ color: {BLUE}; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(3, minmax(280px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .card {{
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 14px;
      padding: 14px;
    }}
    .wide {{
      grid-column: span 1;
    }}
    img {{
      width: 100%;
      border: 1px solid #d8cbbb;
      border-radius: 10px;
      background: white;
    }}
    @media (max-width: 1200px) {{
      .cards {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <p><a href="index.md">Back to report</a> · <a href="{back_link}">Back to clickable plot</a></p>
  <h1>{html.escape(title)}</h1>
  <div class="cards">
    {"".join(cards)}
  </div>
</body>
</html>
"""
        (OUT_DIR / dynamic_fixed_page_name(grid_label, int(row.beta), int(row.aet))).write_text(body, encoding="utf-8")


def plot_dynamic_vs_fixed_persistence_frame(
    matched: pd.DataFrame,
    output_stem: str,
    title: str,
    dynamic_label: str,
    clickable: bool = False,
) -> None:
    if matched.empty:
        return
    labels = [f"b{int(row.beta)} e{int(row.aet)}" for row in matched.itertuples()]
    x = np.arange(len(matched))
    width = 0.24
    variants = [
        ("none", "Fixed none", "#6c7688"),
        ("trivial", "Fixed trivial", BLUE),
        ("dynamic", dynamic_label, GREEN),
    ]

    fig, axes = plt.subplots(3, 1, figsize=(11.6, 9.5), sharex=True)
    for offset, (prefix, variant_label, color) in enumerate(variants):
        positions = x + (offset - 1) * width
        if prefix == "dynamic":
            area_values = matched["dynamic_best_area"]
            runtime_values = matched["dynamic_runtime_h"]
            iteration_values = matched["dynamic_iterations"]
        else:
            area_values = matched.get(f"{prefix}_area", pd.Series([np.nan] * len(matched)))
            runtime_values = matched.get(f"{prefix}_runtime_h", pd.Series([np.nan] * len(matched)))
            iteration_values = matched.get(f"{prefix}_iterations", pd.Series([np.nan] * len(matched)))
        bars = axes[0].bar(positions, area_values, width=width, label=variant_label, color=color, alpha=0.9)
        if clickable:
            for bar, row in zip(bars, matched.itertuples()):
                bar.set_url(dynamic_fixed_page_name(str(row.dynamic_grid), int(row.beta), int(row.aet)))
        annotate_bar_values(axes[0], bars, "{:.1f}", rotation=90)
        bars = axes[1].bar(positions, runtime_values, width=width, label=variant_label, color=color, alpha=0.9)
        if clickable:
            for bar, row in zip(bars, matched.itertuples()):
                bar.set_url(dynamic_fixed_page_name(str(row.dynamic_grid), int(row.beta), int(row.aet)))
        annotate_bar_values(axes[1], bars, "{:.1f}", rotation=90)
        bars = axes[2].bar(positions, iteration_values, width=width, label=variant_label, color=color, alpha=0.9)
        if clickable:
            for bar, row in zip(bars, matched.itertuples()):
                bar.set_url(dynamic_fixed_page_name(str(row.dynamic_grid), int(row.beta), int(row.aet)))
        annotate_bar_values(axes[2], bars, "{:.0f}", rotation=90)

    axes[0].set_title(title)
    axes[0].set_ylabel("Best area")
    axes[1].set_ylabel("Runtime [h]")
    axes[2].set_ylabel("Iterations")
    axes[2].set_xticks(x, labels)
    for ax in axes:
        ax.grid(True, axis="y")
    axes[0].legend(ncol=3, loc="upper right")
    fig.text(
        0.5,
        0.01,
        "Fixed baselines are older 4x4 runs with persistance=1 and no dynamic persistence; dynamic uses the best observed matching setting from the current report.",
        ha="center",
        color=MUTED,
        fontsize=9,
    )
    fig.savefig(OUT_DIR / f"{output_stem}.png", dpi=220, bbox_inches="tight")
    if clickable:
        fig.savefig(OUT_DIR / f"{output_stem}.svg", bbox_inches="tight")
    plt.close(fig)


def plot_dynamic_vs_fixed_persistence(runs: pd.DataFrame) -> pd.DataFrame:
    matched = build_dynamic_vs_fixed_persistence(runs)
    if matched.empty:
        return matched
    matched.to_csv(OUT_DIR / "dynamic_vs_fixed_persistence_matched.csv", index=False)
    plot_dynamic_vs_fixed_persistence_frame(
        matched,
        "dynamic_vs_fixed_persistence",
        "Dynamic persistence vs fixed persistence baselines",
        "Dynamic best",
    )

    for grid in ["3x3", "4x4"]:
        grid_matched = build_dynamic_vs_fixed_persistence(runs, grid)
        if grid_matched.empty:
            continue
        grid_matched.to_csv(OUT_DIR / f"dynamic_vs_fixed_persistence_{grid}_matched.csv", index=False)
        output_stem = f"dynamic_vs_fixed_persistence_{grid}"
        html_name = f"{output_stem}_clickable.html"
        write_dynamic_vs_fixed_pages(grid_matched, grid, html_name)
        plot_dynamic_vs_fixed_persistence_frame(
            grid_matched,
            output_stem,
            f"Dynamic persistence vs fixed baselines: {grid} LPP/PPO",
            f"Dynamic {grid}",
            clickable=True,
        )
        write_clickable_svg_page(
            f"{output_stem}.svg",
            html_name,
            f"Clickable Dynamic Vs Fixed Persistence: {grid}",
        )
    return matched


def build_dynamic_vs_fixed_fourway(runs: pd.DataFrame) -> pd.DataFrame:
    previous = dyn_compare.discover_records(dyn_compare.DEFAULT_SWEEP)
    if previous.empty:
        return pd.DataFrame()

    fixed = previous[
        (~previous["dynamic_persistence"].astype(bool))
        & previous["family"].isin(["previous none", "previous trivial"])
    ].copy()
    dynamic_best = {}
    for grid in ["3x3", "4x4"]:
        frame = runs[runs["grid"].eq(grid)].copy()
        if frame.empty:
            continue
        dynamic_best[grid] = best_by(frame, ["beta", "aet"])

    keys = set()
    for frame in dynamic_best.values():
        keys.update((int(row.beta), int(row.aet)) for row in frame.itertuples())
    fixed_keys = set((int(row.beta), int(row.aet)) for row in fixed.itertuples())
    keys = sorted(keys & fixed_keys)

    records = []
    for beta, aet in keys:
        record = {"beta": beta, "aet": aet}
        subset = fixed[(fixed["beta"].eq(beta)) & (fixed["aet"].eq(aet))]
        for family, prefix in [("previous none", "none"), ("previous trivial", "trivial")]:
            baseline = subset[subset["family"].eq(family)]
            if baseline.empty:
                continue
            baseline = baseline.sort_values(["best_area", "runtime_hours", "iterations"]).iloc[0]
            record[f"{prefix}_area"] = float(baseline.best_area)
            record[f"{prefix}_runtime_h"] = float(baseline.runtime_hours)
            record[f"{prefix}_iterations"] = int(baseline.iterations)
            record[f"{prefix}_run"] = baseline.run
            record[f"{prefix}_summary_path"] = baseline.summary_path

        for grid in ["3x3", "4x4"]:
            frame = dynamic_best.get(grid)
            if frame is None:
                continue
            match = frame[(frame["beta"].eq(beta)) & (frame["aet"].eq(aet))]
            if match.empty:
                continue
            row = match.iloc[0]
            prefix = f"dyn_{grid}"
            record[f"{prefix}_area"] = float(row.best_area)
            record[f"{prefix}_runtime_h"] = float(row.runtime_hours)
            record[f"{prefix}_iterations"] = int(row.iterations)
            record[f"{prefix}_patience"] = int(row.pnum)
            record[f"{prefix}_run"] = row.run
            record[f"{prefix}_row_timeline_png"] = row.row_timeline_png

        if {"none_area", "trivial_area", "dyn_3x3_area", "dyn_4x4_area"}.issubset(record):
            records.append(record)

    fourway = pd.DataFrame(records).sort_values(["beta", "aet"]).reset_index(drop=True)
    if fourway.empty:
        return fourway
    for dyn_prefix in ["dyn_3x3", "dyn_4x4"]:
        for base_prefix in ["none", "trivial"]:
            fourway[f"{dyn_prefix}_area_reduction_vs_{base_prefix}"] = (
                fourway[f"{base_prefix}_area"] - fourway[f"{dyn_prefix}_area"]
            )
            fourway[f"{dyn_prefix}_area_improvement_vs_{base_prefix}_pct"] = fourway.apply(
                lambda row: area_improvement_pct(float(row[f"{dyn_prefix}_area"]), float(row[f"{base_prefix}_area"])),
                axis=1,
            )
            fourway[f"{dyn_prefix}_runtime_overhead_vs_{base_prefix}_h"] = (
                fourway[f"{dyn_prefix}_runtime_h"] - fourway[f"{base_prefix}_runtime_h"]
            )
            fourway[f"{dyn_prefix}_runtime_overhead_vs_{base_prefix}_pct"] = fourway.apply(
                lambda row: pct_delta(float(row[f"{dyn_prefix}_runtime_h"]), float(row[f"{base_prefix}_runtime_h"])),
                axis=1,
            )
    return fourway


def write_dynamic_fourway_pages(fourway: pd.DataFrame) -> None:
    if fourway.empty:
        return
    for row in fourway.itertuples():
        title = f"Fixed vs dynamic persistence: b{int(row.beta)} e{int(row.aet)}"
        cards = []
        for prefix, heading in [
            ("none", "Fixed none"),
            ("trivial", "Fixed trivial"),
            ("dyn_3x3", "Dynamic 3x3"),
            ("dyn_4x4", "Dynamic 4x4"),
        ]:
            area = getattr(row, f"{prefix}_area", np.nan)
            if pd.isna(area):
                continue
            runtime = getattr(row, f"{prefix}_runtime_h")
            iterations = getattr(row, f"{prefix}_iterations")
            run = getattr(row, f"{prefix}_run")
            if prefix.startswith("dyn"):
                image_path = Path(getattr(row, f"{prefix}_row_timeline_png"))
                image = relpath(image_path) if image_path.exists() else None
                suffix = f" p{int(getattr(row, f'{prefix}_patience'))}"
                media = (
                    f"<a href='{image}'><img src='{image}' alt='{heading} row timeline'></a>"
                    if image
                    else "<p>Missing row timeline.</p>"
                )
            else:
                summary_path = Path(getattr(row, f"{prefix}_summary_path"))
                suffix = ""
                media = fixed_media_block(summary_path, heading)
            cards.append(
                f"""<section class="card">
  <h2>{heading}{suffix}</h2>
  <p>Run: <code>{html.escape(str(run))}</code></p>
  <p>Area: <strong>{float(area):.1f}</strong> · Runtime: <strong>{float(runtime):.1f}h</strong> · Iterations: <strong>{int(iterations)}</strong></p>
  {media}
</section>"""
            )

        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    body {{
      margin: 24px;
      background: {BG};
      color: {TEXT};
      font-family: DejaVu Sans, sans-serif;
    }}
    a {{ color: {BLUE}; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(4, minmax(260px, 1fr));
      gap: 18px;
      align-items: start;
    }}
    .card {{
      background: {PANEL};
      border: 1px solid #d8cbbb;
      border-radius: 14px;
      padding: 14px;
    }}
    img {{
      width: 100%;
      border: 1px solid #d8cbbb;
      border-radius: 10px;
      background: white;
    }}
    @media (max-width: 1280px) {{
      .cards {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <p><a href="index.md">Back to report</a> · <a href="dynamic_vs_fixed_persistence_fourway_clickable.html">Back to clickable plot</a></p>
  <h1>{html.escape(title)}</h1>
  <div class="cards">
    {"".join(cards)}
  </div>
</body>
</html>
"""
        (OUT_DIR / dynamic_fourway_page_name(int(row.beta), int(row.aet))).write_text(body, encoding="utf-8")


def plot_dynamic_vs_fixed_fourway(fourway: pd.DataFrame) -> None:
    if fourway.empty:
        return
    fourway.to_csv(OUT_DIR / "dynamic_vs_fixed_persistence_fourway_matched.csv", index=False)
    write_dynamic_fourway_pages(fourway)

    labels = [f"b{int(row.beta)} e{int(row.aet)}" for row in fourway.itertuples()]
    x = np.arange(len(fourway))
    width = 0.18
    variants = [
        ("none", "Fixed none", "#6c7688"),
        ("trivial", "Fixed trivial", BLUE),
        ("dyn_3x3", "Dynamic 3x3", GREEN),
        ("dyn_4x4", "Dynamic 4x4", ORANGE),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(12.2, 9.5), sharex=True)
    for offset, (prefix, label, color) in enumerate(variants):
        positions = x + (offset - 1.5) * width
        area_values = fourway[f"{prefix}_area"]
        runtime_values = fourway[f"{prefix}_runtime_h"]
        iteration_values = fourway[f"{prefix}_iterations"]
        for ax, values, fmt in [
            (axes[0], area_values, "{:.1f}"),
            (axes[1], runtime_values, "{:.1f}"),
            (axes[2], iteration_values, "{:.0f}"),
        ]:
            bars = ax.bar(positions, values, width=width, label=label, color=color, alpha=0.9)
            for bar, row in zip(bars, fourway.itertuples()):
                bar.set_url(dynamic_fourway_page_name(int(row.beta), int(row.aet)))
            annotate_bar_values(ax, bars, fmt, rotation=90)

    axes[0].set_title("Fixed persistence vs dynamic persistence: all matched variants")
    axes[0].set_ylabel("Best area")
    axes[1].set_ylabel("Runtime [h]")
    axes[2].set_ylabel("Iterations")
    axes[2].set_xticks(x, labels)
    for ax in axes:
        ax.grid(True, axis="y")
    axes[0].legend(ncol=4, loc="upper right")
    fig.text(
        0.5,
        0.01,
        "Fixed baselines are older 4x4 runs with persistance=1; dynamic variants are best observed 3x3 and 4x4 runs from this report.",
        ha="center",
        color=MUTED,
        fontsize=9,
    )
    fig.savefig(OUT_DIR / "dynamic_vs_fixed_persistence_fourway.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUT_DIR / "dynamic_vs_fixed_persistence_fourway.svg", bbox_inches="tight")
    plt.close(fig)
    write_clickable_svg_page(
        "dynamic_vs_fixed_persistence_fourway.svg",
        "dynamic_vs_fixed_persistence_fourway_clickable.html",
        "Clickable Dynamic Vs Fixed Persistence: Four-Way",
    )


def annotate_bar_values(ax: plt.Axes, bars: object, fmt: str, rotation: int = 0) -> None:
    for bar in bars:
        height = bar.get_height()
        if pd.isna(height):
            continue
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            fmt.format(height),
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=rotation,
        )


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    return frame[columns].to_markdown(index=False)


def write_index(
    runs: pd.DataFrame,
    lpp: pd.DataFrame,
    patience: pd.DataFrame,
    beta: pd.DataFrame,
    aet: pd.DataFrame,
    dynamic_fixed: pd.DataFrame,
) -> None:
    best_p2 = aet.sort_values(["beta", "aet"])
    lpp_display = lpp.assign(
        area_3x3_label=lpp["area_3x3"].map(lambda value: f"{value:.1f}"),
        area_4x4_label=lpp["area_4x4"].map(lambda value: f"{value:.1f}"),
        runtime_3x3_label=lpp["runtime_3x3_h"].map(lambda value: f"{value:.1f}h"),
        runtime_4x4_label=lpp["runtime_4x4_h"].map(lambda value: f"{value:.1f}h"),
        area_reduction_label=lpp["area_reduction_4x4_vs_3x3"].map(lambda value: signed(value)),
        area_improvement_pct_label=lpp["area_improvement_4x4_vs_3x3_pct"].map(signed_pct),
        runtime_change_pct_label=lpp["runtime_change_4x4_vs_3x3_pct"].map(signed_pct),
        runtime_improvement_pct_label=lpp["runtime_improvement_4x4_vs_3x3_pct"].map(signed_pct),
        timeline_3x3=lpp["run_3x3"].map(lambda run: timeline_link(runs, str(run), "3x3")),
        timeline_4x4=lpp["run_4x4"].map(lambda run: timeline_link(runs, str(run), "4x4")),
        pair_page_link=lpp["pair_page"].map(lambda page: f"[pair]({page})"),
    )
    timeline_links = runs.sort_values(["beta", "aet", "grid_lpp", "grid_ppo", "pnum"]).assign(
        setting=lambda frame: frame["grid"] + " p" + frame["pnum"].astype(int).astype(str),
        area=lambda frame: frame["best_area"].map(lambda value: f"{value:.1f}"),
        runtime_h=lambda frame: frame["runtime_hours"].map(lambda value: f"{value:.1f}"),
        timeline=lambda frame: frame["run"].map(lambda run: timeline_link(runs, str(run), "timeline")),
    )
    dynamic_fixed_display = dynamic_fixed.copy()
    if not dynamic_fixed_display.empty:
        dynamic_fixed_display = dynamic_fixed_display.assign(
            dynamic_area=dynamic_fixed_display["dynamic_best_area"].map(lambda value: f"{value:.1f}"),
            dynamic_runtime=dynamic_fixed_display["dynamic_runtime_h"].map(lambda value: f"{value:.1f}h"),
            trivial_area=dynamic_fixed_display.get("trivial_area", pd.Series(dtype=float)).map(lambda value: f"{value:.1f}"),
            trivial_runtime=dynamic_fixed_display.get("trivial_runtime_h", pd.Series(dtype=float)).map(lambda value: f"{value:.1f}h"),
            none_area=dynamic_fixed_display.get("none_area", pd.Series(dtype=float)).map(lambda value: f"{value:.1f}"),
            none_runtime=dynamic_fixed_display.get("none_runtime_h", pd.Series(dtype=float)).map(lambda value: f"{value:.1f}h"),
            improvement_vs_trivial=dynamic_fixed_display.get("area_improvement_vs_trivial_pct", pd.Series(dtype=float)).map(signed_pct),
            runtime_vs_trivial=dynamic_fixed_display.get("runtime_overhead_vs_trivial_pct", pd.Series(dtype=float)).map(signed_pct),
        )
    lines = [
        "# i16 Dynamic-Persistence Parameter Sensitivity",
        "",
        "Generated on 2026-05-21 from the completed dynamic-persistence i16 runs.",
        "",
        "## How Persistence And Patience Work",
        "",
        "**Persistence** is an extraction-level retry budget. For extraction mode 0, SubXPAT picks an output node, computes its ancestor gate cone, asks Z3 for a valid subgraph, and measures `coverage = selected_subgraph_gate_count / ancestor_gate_count`. With dynamic persistence, low coverage receives more retries on the same output node: `coverage >= 0.75 -> L0`, `>= 0.40 -> L1`, `>= 0.20 -> L2`, and `< 0.20 -> L3` with the current `--dynamic-persistence-max 3`. The persisted counter decides whether the next outer iteration stays on the same output node or moves to the next one.",
        "",
        "**Patience** is a termination-level counter. Pareto patience counts consecutive outer iterations with no accepted SAT candidate. It does not count individual UNSAT cells. A grid iteration with many UNSAT/UNKNOWN/DOMINATED cells still counts as one bad iteration only if no SAT candidate is accepted. Duplicate-subgraph and no-subgraph iterations also increment the no-SAT streak. A successful accepted SAT resets the patience counter to zero.",
        "",
        "Persistence and patience are therefore mostly separate: persistence chooses what to try next; patience decides when the whole run has stopped making useful SAT progress.",
        "",
        "## Plots",
        "",
        "- [Decision plot hub](decision_plots/index.html)",
        "- [LPP/PPO effect](lpp_ppo_effect.png)",
        "- [Clickable LPP/PPO effect](lpp_ppo_effect_clickable.html)",
        "- [Patience effect for fixed 3x3 LPP/PPO](patience_effect_3x3.png)",
        "- [Clickable patience effect for fixed 3x3 LPP/PPO](patience_effect_3x3_clickable.html)",
        "- [Patience effect for fixed 4x4 LPP/PPO](patience_effect_4x4.png)",
        "- [Clickable patience effect for fixed 4x4 LPP/PPO](patience_effect_4x4_clickable.html)",
        "- [Beta effect](beta_effect.png)",
        "- [AET effect](aet_effect.png)",
        "- [Dynamic vs fixed persistence](dynamic_vs_fixed_persistence.png)",
        "- [Dynamic vs fixed persistence: none/trivial/3x3/4x4](dynamic_vs_fixed_persistence_fourway.png)",
        "- [Clickable dynamic vs fixed persistence: none/trivial/3x3/4x4](dynamic_vs_fixed_persistence_fourway_clickable.html)",
        "- [Dynamic vs fixed persistence: 3x3 LPP/PPO](dynamic_vs_fixed_persistence_3x3.png)",
        "- [Clickable dynamic vs fixed persistence: 3x3 LPP/PPO](dynamic_vs_fixed_persistence_3x3_clickable.html)",
        "- [Dynamic vs fixed persistence: 4x4 LPP/PPO](dynamic_vs_fixed_persistence_4x4.png)",
        "- [Clickable dynamic vs fixed persistence: 4x4 LPP/PPO](dynamic_vs_fixed_persistence_4x4_clickable.html)",
        "- [Historical dynamic/fixed comparison folder](dynamic_vs_fixed_persistence/index.md)",
        "",
        "## Viewing Clickable Plots",
        "",
        "VS Code's raw SVG/image preview intercepts clicks for zooming. To use clickable plot links, serve the repo over localhost and open the HTML wrapper pages in VS Code Simple Browser or an external browser:",
        "",
        "```bash",
        "cd /home/mykhailo/subxpat",
        "python3 -m http.server 8765 --bind 127.0.0.1",
        "```",
        "",
        "Then open:",
        "",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/decision_plots/index.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/lpp_ppo_effect_clickable.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/patience_effect_3x3_clickable.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/patience_effect_4x4_clickable.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/dynamic_vs_fixed_persistence_fourway_clickable.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/dynamic_vs_fixed_persistence_3x3_clickable.html`",
        "- `http://127.0.0.1:8765/benchmarking/reports/2026-05-21_i16_dynpers_parameter_sensitivity_report/dynamic_vs_fixed_persistence_4x4_clickable.html`",
        "",
        "## Result Summary",
        "",
        "The completed p2 grid is the most useful comparison set: it covers both betas, all three AETs, and both 3x3/4x4 grids.",
        "",
        "## 3x3 vs 4x4 LPP/PPO",
        "",
        "This is the cleanest completed comparison because p2 has all six beta/AET pairs. Area is shown as `3x3 - 4x4`, so positive means `4x4` found a smaller circuit. Runtime is shown as `4x4 - 3x3`, so positive means `4x4` was slower.",
        "",
        "[Open the LPP/PPO delta plot](lpp_ppo_effect.png).",
        "For direct navigation, open the [clickable HTML plot](lpp_ppo_effect_clickable.html): each bar opens a side-by-side row-timeline page for that case.",
        "",
        markdown_table(
            lpp_display[
                [
                    "label",
                    "area_3x3_label",
                    "area_4x4_label",
                    "area_reduction_label",
                    "area_improvement_pct_label",
                    "runtime_3x3_label",
                    "runtime_4x4_label",
                    "runtime_delta_label",
                    "runtime_change_pct_label",
                    "pair_page_link",
                    "timeline_3x3",
                    "timeline_4x4",
                    "recommendation",
                ]
            ].rename(
                columns={
                    "label": "case",
                    "area_3x3_label": "area 3x3",
                    "area_4x4_label": "area 4x4",
                    "area_reduction_label": "area reduction",
                    "area_improvement_pct_label": "area improvement",
                    "runtime_3x3_label": "runtime 3x3",
                    "runtime_4x4_label": "runtime 4x4",
                    "runtime_delta_label": "runtime overhead",
                    "runtime_change_pct_label": "runtime overhead %",
                    "pair_page_link": "pair page",
                    "timeline_3x3": "3x3 trace",
                    "timeline_4x4": "4x4 trace",
                }
            ),
            [
                "case",
                "area 3x3",
                "area 4x4",
                "area reduction",
                "area improvement",
                "runtime 3x3",
                "runtime 4x4",
                "runtime overhead",
                "runtime overhead %",
                "pair page",
                "3x3 trace",
                "4x4 trace",
                "recommendation",
            ],
        ),
        "",
        "Conclusions:",
        "",
        "- `4x4` wins on area in three p2 cases: `b32/e300`, `b32/e350`, and `b48/e300`.",
        "- `3x3` is faster in every p2 case, including the cases where `4x4` improves area.",
        "- When area ties, choose `3x3`: `b32/e250`, `b48/e250`, and `b48/e350`.",
        "- The practical rule is: start with `3x3`; use `4x4` only when the target case is known to benefit in area or when we explicitly want to pay runtime for possible area gains.",
        "",
        "Recommended best observed p2 settings:",
        "",
        markdown_table(
            best_p2.assign(
                setting=best_p2["grid"] + " p" + best_p2["pnum"].astype(int).astype(str),
                runtime_h=best_p2["runtime_hours"].map(lambda value: f"{value:.1f}"),
                area=best_p2["best_area"].map(lambda value: f"{value:.1f}"),
            ),
            ["beta", "aet", "setting", "area", "runtime_h", "iterations"],
        ),
        "",
        "## Interpretation",
        "",
        "- `4x4` is valuable when it unlocks a lower area: b32/e300, b32/e350, and b48/e300. When area ties, `3x3` is usually faster.",
        "- `p2` is the useful patience setting. It improves several p1 cases, while observed p3 runs do not improve area over p2.",
        "- `beta` has no universal winner. At p2, beta 48 helps at AET 250, but beta 32 is better at AET 300/350 for the best observed area.",
        "- `AET` is not perfectly monotonic in observed results because search and early termination change the path. Treat AET trends as empirical, not guaranteed.",
        "",
        "## Dynamic Persistence Vs Fixed Persistence",
        "",
        "The matched complete comparison on disk is beta 32 at AET 250/300/350. The old fixed-persistence baselines used `persistance = 1`, 4x4 extraction, and no dynamic persistence. The dynamic column uses the best observed setting in this report for the same beta/AET. This is not a perfectly controlled one-knob experiment because termination settings also changed, but it is the most useful available before/after comparison.",
        "",
        "[Open the dynamic vs fixed persistence plot](dynamic_vs_fixed_persistence.png). A broader historical folder is also available at [dynamic_vs_fixed_persistence](dynamic_vs_fixed_persistence/index.md).",
        "",
        "Separate dynamic-grid comparisons:",
        "",
        "- [Four-way fixed/dynamic comparison](dynamic_vs_fixed_persistence_fourway.png)",
        "- [Clickable four-way fixed/dynamic comparison](dynamic_vs_fixed_persistence_fourway_clickable.html)",
        "- [3x3 dynamic vs fixed persistence](dynamic_vs_fixed_persistence_3x3.png)",
        "- [Clickable 3x3 dynamic vs fixed persistence](dynamic_vs_fixed_persistence_3x3_clickable.html)",
        "- [4x4 dynamic vs fixed persistence](dynamic_vs_fixed_persistence_4x4.png)",
        "- [Clickable 4x4 dynamic vs fixed persistence](dynamic_vs_fixed_persistence_4x4_clickable.html)",
        "",
        "The clickable dynamic-vs-fixed pages embed cached row timelines for the old `none` and `trivial` runs next to the dynamic timelines. The old April traces did not log per-cell runtime, so those fixed timelines show the iteration/cell/area/status history but have less timing detail than the new dynamic runs.",
        "",
        markdown_table(
            dynamic_fixed_display.rename(
                columns={
                    "beta": "beta",
                    "aet": "aet",
                    "dynamic_setting": "dynamic setting",
                    "dynamic_area": "dynamic area",
                    "dynamic_runtime": "dynamic runtime",
                    "trivial_area": "fixed trivial area",
                    "trivial_runtime": "fixed trivial runtime",
                    "improvement_vs_trivial": "area vs trivial",
                    "runtime_vs_trivial": "runtime overhead vs trivial",
                    "none_area": "fixed none area",
                    "none_runtime": "fixed none runtime",
                }
            ),
            [
                "beta",
                "aet",
                "dynamic setting",
                "dynamic area",
                "dynamic runtime",
                "fixed trivial area",
                "fixed trivial runtime",
                "area vs trivial",
                "runtime overhead vs trivial",
                "fixed none area",
                "fixed none runtime",
            ],
        )
        if not dynamic_fixed_display.empty
        else "No matched fixed-persistence baselines were found.",
        "",
        "## Fixed-Grid Patience Comparisons",
        "",
        "The fixed-grid patience plots isolate patience from LPP/PPO changes. Percentage labels on p2/p3 are relative to p1 for the same beta, AET, and grid. Positive area improvement means patience found a smaller circuit; positive runtime overhead means it took longer.",
        "In the clickable versions, each heatmap cell opens a side-by-side p1/p2/p3 row-timeline history page for that beta/AET/grid case.",
        "",
        "- [3x3 patience comparison](patience_effect_3x3.png)",
        "- [Clickable 3x3 patience comparison](patience_effect_3x3_clickable.html)",
        "- [4x4 patience comparison](patience_effect_4x4.png)",
        "- [Clickable 4x4 patience comparison](patience_effect_4x4_clickable.html)",
        "",
        "Timeline links for the fixed-grid patience comparisons:",
        "",
        "3x3:",
        "",
        markdown_table(timeline_table(runs, "3x3"), ["case", "p1", "p2", "p3"]),
        "",
        "4x4:",
        "",
        markdown_table(timeline_table(runs, "4x4"), ["case", "p1", "p2", "p3"]),
        "",
        "## All Run Timelines",
        "",
        markdown_table(
            timeline_links.rename(
                columns={
                    "beta": "beta",
                    "aet": "aet",
                    "setting": "setting",
                    "area": "area",
                    "runtime_h": "runtime h",
                    "iterations": "iterations",
                    "timeline": "timeline",
                }
            ),
            ["beta", "aet", "setting", "area", "runtime h", "iterations", "timeline"],
        ),
        "",
        "## Data Files",
        "",
        "- [lpp_ppo_p2_effect.csv](lpp_ppo_p2_effect.csv)",
        "- [lpp_ppo_p2_decisions.csv](lpp_ppo_p2_decisions.csv)",
        "- [best_by_patience.csv](best_by_patience.csv)",
        "- [patience_effect_3x3.csv](patience_effect_3x3.csv)",
        "- [patience_effect_4x4.csv](patience_effect_4x4.csv)",
        "- [beta_p2_effect.csv](beta_p2_effect.csv)",
        "- [aet_best_p2.csv](aet_best_p2.csv)",
        "- [dynamic_vs_fixed_persistence_matched.csv](dynamic_vs_fixed_persistence_matched.csv)",
        "- [dynamic_vs_fixed_persistence_fourway_matched.csv](dynamic_vs_fixed_persistence_fourway_matched.csv)",
        "- [dynamic_vs_fixed_persistence_3x3_matched.csv](dynamic_vs_fixed_persistence_3x3_matched.csv)",
        "- [dynamic_vs_fixed_persistence_4x4_matched.csv](dynamic_vs_fixed_persistence_4x4_matched.csv)",
        "",
    ]
    (OUT_DIR / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    setup_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    runs = load_runs()
    pairs = load_pairs()
    runs.to_csv(OUT_DIR / "all_dynamic_grid_runs.csv", index=False)
    pairs.to_csv(OUT_DIR / "paired_grid_comparisons.csv", index=False)
    lpp = plot_lpp_ppo_effect(pairs)
    write_lpp_pair_pages(runs, lpp)
    patience = plot_patience_effect(runs)
    plot_fixed_grid_patience_effect(runs, "3x3")
    plot_fixed_grid_patience_effect(runs, "4x4")
    write_patience_history_pages(runs, "3x3")
    write_patience_history_pages(runs, "4x4")
    write_clickable_plot_pages()
    beta = plot_beta_effect(runs)
    aet = plot_aet_effect(runs)
    dynamic_fixed = plot_dynamic_vs_fixed_persistence(runs)
    plot_dynamic_vs_fixed_fourway(build_dynamic_vs_fixed_fourway(runs))
    write_decision_plot_hub()
    write_index(runs, lpp, patience, beta, aet, dynamic_fixed)
    print(f"Wrote {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
