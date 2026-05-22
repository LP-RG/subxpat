from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SWEEP = ROOT / "benchmarking/generated/zone_aet_i16_dynpers_p1_grid_sweep_20260508"
DEFAULT_OUTPUT = DEFAULT_SWEEP / "plots/comparison_to_previous"

BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"
MUTED = "#5a5047"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare the i16 dynamic-persistence sweep against previous i16 zone-AET runs."
    )
    parser.add_argument("--sweep-dir", type=Path, default=DEFAULT_SWEEP)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
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


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def numeric(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed):
        return None
    return parsed


def int_or_none(value: Any) -> Optional[int]:
    parsed = numeric(value)
    return None if parsed is None else int(parsed)


def read_trace(summary_path: Path) -> List[Dict[str, str]]:
    trace_path = summary_path.with_name(summary_path.name.replace("_summary.json", "_trace.csv"))
    if not trace_path.exists():
        return []
    with trace_path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def parse_grid(summary_path: Path) -> str:
    match = re.search(r"_(\d+)X(\d+)_et", summary_path.name)
    if not match:
        return ""
    return f"{match.group(1)}x{match.group(2)}"


def parse_aet(summary_path: Path, summary: Dict[str, Any]) -> Optional[int]:
    match = re.search(r"_et(\d+)_", summary_path.name)
    if match:
        return int(match.group(1))
    return int_or_none(summary.get("max_error"))


def run_family(summary_path: Path, summary: Dict[str, Any]) -> str:
    path_text = str(summary_path)
    mode = str(summary.get("termination_mode") or "")
    patience = summary.get("pareto_candidate_patience")
    dyn = bool(summary.get("dynamic_persistence"))
    if "zone_aet_i16_dynpers_p1_grid_sweep_20260508" in path_text:
        return "new dynpers p1"
    if "zone_aet_large_mul_i16_a2_multiAET_20260402" in path_text:
        return f"previous {mode}"
    if dyn:
        return f"previous dynpers p{patience}"
    if "pareto_annealed" in path_text or "termpareto_annealed" in summary_path.name:
        return "previous pareto annealed"
    if mode == "pareto" and patience is not None:
        return f"previous pareto p{patience}"
    return f"previous {mode or 'unknown'}"


def short_run_name(summary_path: Path, record: Dict[str, Any]) -> str:
    beta = record.get("beta")
    aet = record.get("aet")
    grid = record.get("grid")
    family = record.get("family", "")
    if "zone_aet_i16_dynpers_p1_grid_sweep_20260508" in str(summary_path):
        return f"b{beta} e{aet} {grid} dyn-p1"
    return f"b{beta} e{aet} {grid} {family.replace('previous ', '')}"


def extract_record(summary_path: Path) -> Optional[Dict[str, Any]]:
    summary = read_json(summary_path)
    if summary.get("exact_benchmark") not in (None, "mul_i16_o16"):
        return None
    if "mul_i16_o16" not in summary_path.name:
        return None

    trace = read_trace(summary_path)
    final_area = numeric(summary.get("final_area"))
    best_area = numeric(summary.get("best_seen_area")) or final_area
    best_iteration = int_or_none(summary.get("best_seen_iteration")) or int_or_none(summary.get("iterations"))
    runtime_hours = None
    best_runtime_hours = None

    runtime_seconds = numeric(summary.get("runtime_seconds"))
    if runtime_seconds is not None:
        runtime_hours = runtime_seconds / 3600.0

    if trace:
        last = trace[-1]
        elapsed = numeric(last.get("runtime_elapsed_seconds"))
        if elapsed is not None:
            runtime_hours = elapsed / 3600.0
        run_best = numeric(last.get("run_best_area"))
        if run_best is not None:
            best_area = run_best
        run_best_iter = int_or_none(last.get("run_best_iteration"))
        if run_best_iter is not None:
            best_iteration = run_best_iter
        run_best_runtime = numeric(last.get("run_best_runtime_at_accept_seconds"))
        if run_best_runtime is not None:
            best_runtime_hours = run_best_runtime / 3600.0

        row_areas = [(numeric(row.get("best_area")), int_or_none(row.get("iteration")), row) for row in trace]
        row_areas = [(area, iteration, row) for area, iteration, row in row_areas if area is not None]
        if row_areas and numeric(last.get("run_best_area")) is None:
            area, iteration, row = min(row_areas, key=lambda item: item[0])
            best_area = area
            best_iteration = iteration
            elapsed_at_best = numeric(row.get("runtime_elapsed_seconds"))
            if elapsed_at_best is not None:
                best_runtime_hours = elapsed_at_best / 3600.0

    if best_runtime_hours is None:
        best_runtime_hours = runtime_hours

    record: Dict[str, Any] = {
        "summary_path": str(summary_path),
        "run_dir": str(run_dir_for_summary(summary_path)),
        "beta": int_or_none(summary.get("beta")),
        "aet": parse_aet(summary_path, summary),
        "alpha": int_or_none(summary.get("alpha")),
        "grid": parse_grid(summary_path),
        "termination_mode": summary.get("termination_mode"),
        "pareto_candidate_patience": summary.get("pareto_candidate_patience"),
        "dynamic_persistence": bool(summary.get("dynamic_persistence")),
        "iterations": int_or_none(summary.get("iterations")) or (max((int_or_none(r.get("iteration")) or 0 for r in trace), default=None)),
        "best_iteration": best_iteration,
        "best_area": best_area,
        "final_area": final_area,
        "runtime_hours": runtime_hours,
        "best_runtime_hours": best_runtime_hours,
        "stop_reason": summary.get("stop_reason"),
        "trace_rows": len(trace),
    }
    record["family"] = run_family(summary_path, summary)
    record["run"] = short_run_name(summary_path, record)
    return record


def run_dir_for_summary(summary_path: Path) -> Path:
    parts = summary_path.parts
    if "artifacts" in parts:
        return summary_path.parents[1]
    if "termination_study" in parts:
        return summary_path.parents[2]
    return summary_path.parent


def discover_records(sweep_dir: Path) -> pd.DataFrame:
    roots: List[Iterable[Path]] = [
        sweep_dir.glob("*/artifacts/*_summary.json"),
        (ROOT / "benchmarking/generated/zone_aet_large_mul_i16_a2_multiAET_20260402").glob(
            "*/output/report/termination_study/*_summary.json"
        ),
        (ROOT / "benchmarking/generated").glob("zone_aet_i16_singlecase_350_b64*/artifacts/*_summary.json"),
    ]
    records: List[Dict[str, Any]] = []
    seen = set()
    for paths in roots:
        for summary_path in paths:
            resolved = str(summary_path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            record = extract_record(summary_path)
            if record is not None:
                records.append(record)
    frame = pd.DataFrame(records)
    if frame.empty:
        return frame
    frame = frame.sort_values(["family", "beta", "aet", "grid", "run"], na_position="last")
    return frame


def annotate_bars(ax: plt.Axes, bars: Any, fmt: str = "{:.1f}") -> None:
    for bar in bars:
        height = bar.get_height()
        if pd.notna(height):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                fmt.format(height),
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )


def plot_beta32_matched(frame: pd.DataFrame, output_dir: Path) -> Optional[Path]:
    matched = frame[
        (frame["beta"] == 32)
        & (frame["aet"].isin([250, 300, 350]))
        & (
            ((frame["family"].isin(["previous none", "previous trivial"])) & (frame["grid"] == "4x4"))
            | (frame["family"] == "new dynpers p1")
        )
    ].copy()
    if matched.empty:
        return None

    def variant(row: pd.Series) -> str:
        if row["family"] == "new dynpers p1":
            return f"dyn p1 {row['grid']}"
        return str(row["family"]).replace("previous ", "")

    matched["variant"] = matched.apply(variant, axis=1)
    order = ["none", "trivial", "dyn p1 3x3", "dyn p1 4x4"]
    colors = {"none": "#6c7688", "trivial": "#2f6f9f", "dyn p1 3x3": "#1f6d3a", "dyn p1 4x4": "#b7791f"}

    configure_style()
    fig, axes = plt.subplots(3, 1, figsize=(13.5, 10), sharex=True, gridspec_kw={"hspace": 0.13})
    metrics = [("best_area", "Best Area"), ("runtime_hours", "Runtime [h]"), ("iterations", "Iterations")]
    x = list(range(len(sorted(matched["aet"].unique()))))
    width = 0.18
    for ax, (metric, label) in zip(axes, metrics):
        for offset, variant_name in enumerate(order):
            values = []
            for aet in sorted(matched["aet"].unique()):
                subset = matched[(matched["aet"] == aet) & (matched["variant"] == variant_name)]
                values.append(float(subset.iloc[0][metric]) if not subset.empty and pd.notna(subset.iloc[0][metric]) else float("nan"))
            positions = [pos + (offset - 1.5) * width for pos in x]
            bars = ax.bar(positions, values, width=width, label=variant_name, color=colors.get(variant_name, "#8a8a8a"), alpha=0.88)
            annotate_bars(ax, bars, "{:.1f}" if metric != "iterations" else "{:.0f}")
        metric_values = pd.to_numeric(matched[metric], errors="coerce").dropna()
        if not metric_values.empty:
            ax.set_ylim(0, float(metric_values.max()) * 1.20)
        ax.set_ylabel(label)
        ax.grid(True, axis="y", alpha=0.8)
    axes[0].set_title("Matched beta=32 comparison: previous 4x4 baselines vs new dynamic persistence", pad=14)
    axes[-1].set_xticks(x)
    axes[-1].set_xticklabels([f"AET {int(aet)}" for aet in sorted(matched["aet"].unique())])
    axes[0].legend(ncols=4, loc="upper right")
    fig.text(0.5, 0.02, "Previous none/trivial used 4x4; new sweep includes both 3x3 and 4x4 dynamic persistence with patience 1.", ha="center", color=MUTED)
    output = output_dir / "beta32_matched_previous_vs_dynpers.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_e350_history(frame: pd.DataFrame, output_dir: Path) -> Optional[Path]:
    hist = frame[
        (frame["aet"] == 350)
        & (
            (frame["family"].str.startswith("previous", na=False))
            | (frame["family"] == "new dynpers p1")
        )
    ].copy()
    hist = hist[hist["best_area"].notna()]
    if hist.empty:
        return None
    hist["label"] = hist.apply(
        lambda row: f"b{int(row.beta)} {row.grid}\\n{str(row.family).replace('previous ', '')}",
        axis=1,
    )
    hist = hist.sort_values(["best_area", "runtime_hours"], na_position="last")
    colors = hist["family"].map(
        {
            "new dynpers p1": "#1f6d3a",
            "previous none": "#6c7688",
            "previous trivial": "#2f6f9f",
            "previous pareto p3": "#b7791f",
            "previous pareto annealed": "#d24b40",
            "previous dynpers p1": "#7c3aed",
        }
    ).fillna("#8a8a8a")

    configure_style()
    fig, axes = plt.subplots(2, 1, figsize=(15, 8.5), sharex=True, gridspec_kw={"height_ratios": [1.45, 1.0], "hspace": 0.08})
    x = range(len(hist))
    bars = axes[0].bar(x, hist["best_area"], color=colors, alpha=0.88)
    annotate_bars(axes[0], bars)
    axes[0].set_ylabel("Best Area")
    axes[0].set_title("AET=350 history: dynamic persistence vs earlier i16 runs")
    axes[0].grid(True, axis="y", alpha=0.8)

    runtime_values = hist["runtime_hours"]
    axes[1].bar(x, runtime_values, color="#6c7688", alpha=0.85)
    axes[1].set_ylabel("Runtime [h]")
    axes[1].grid(True, axis="y", alpha=0.8)
    axes[1].set_xticks(list(x))
    axes[1].set_xticklabels(hist["label"], rotation=45, ha="right")
    output = output_dir / "e350_i16_history.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def plot_tradeoff(frame: pd.DataFrame, output_dir: Path) -> Optional[Path]:
    plot_frame = frame[frame["best_area"].notna() & frame["runtime_hours"].notna()].copy()
    if plot_frame.empty:
        return None
    plot_frame = plot_frame[
        (plot_frame["family"] == "new dynpers p1")
        | (plot_frame["family"].isin(["previous none", "previous trivial", "previous pareto p3", "previous pareto annealed", "previous dynpers p1"]))
    ]
    if plot_frame.empty:
        return None

    family_colors = {
        "new dynpers p1": "#1f6d3a",
        "previous none": "#6c7688",
        "previous trivial": "#2f6f9f",
        "previous pareto p3": "#b7791f",
        "previous pareto annealed": "#d24b40",
        "previous dynpers p1": "#7c3aed",
    }
    configure_style()
    fig, ax = plt.subplots(figsize=(11.5, 7))
    for family, group in plot_frame.groupby("family"):
        ax.scatter(
            group["runtime_hours"],
            group["best_area"],
            s=90,
            label=family,
            color=family_colors.get(family, "#8a8a8a"),
            edgecolor="#2b2724",
            linewidth=0.7,
            alpha=0.9,
        )
        for row in group.itertuples():
            label = f"b{int(row.beta)} e{int(row.aet)} {row.grid}"
            ax.annotate(label, (row.runtime_hours, row.best_area), xytext=(5, 4), textcoords="offset points", fontsize=7.5)
    ax.set_title("i16 area/runtime tradeoff: new dynamic persistence vs previous runs")
    ax.set_xlabel("Runtime [h]")
    ax.set_ylabel("Best Area")
    ax.grid(True, alpha=0.8)
    ax.legend(loc="best")
    output = output_dir / "i16_area_runtime_tradeoff_vs_previous.png"
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output


def write_index(output_dir: Path, generated: List[Path]) -> None:
    lines = [
        "# i16 Dynamic Persistence Comparison",
        "",
        "## Generated Files",
        "",
        "- [comparison_records.csv](comparison_records.csv)",
    ]
    for path in generated:
        lines.append(f"- [{path.name}]({path.name})")
    lines.append("")
    lines.append("This comparison combines the new dynamic-persistence sweep with previous i16 zone-AET runs available on disk.")
    (output_dir / "index.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    frame = discover_records(args.sweep_dir)
    frame.to_csv(output_dir / "comparison_records.csv", index=False)
    generated = [
        path
        for path in (
            plot_beta32_matched(frame, output_dir),
            plot_e350_history(frame, output_dir),
            plot_tradeoff(frame, output_dir),
        )
        if path is not None
    ]
    write_index(output_dir, generated)
    print(f"Wrote comparison outputs to {output_dir}")


if __name__ == "__main__":
    main()
