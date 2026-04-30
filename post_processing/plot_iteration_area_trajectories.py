from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import Iterable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_LOG_ROOTS = (
    Path("benchmarking/generated/zone_aet_i8_adaptive_guard_20260411_rerun"),
    Path("benchmarking/generated/zone_aet_i10_adaptive_guard_20260411_rerun"),
    Path("benchmarking/generated/zone_aet_large_mul_i16_a2_multiAET_20260402"),
)
DEFAULT_BENCHMARKS = ("mul_i8_o8", "mul_i10_o10", "mul_i16_o16")

BENCHMARK_TITLES = {
    "mul_i8_o8": "mul_i8_o8",
    "mul_i10_o10": "mul_i10_o10",
    "mul_i16_o16": "mul_i16_o16",
}

MODE_COLORS = {
    "none": "#6c7688",
    "trivial": "#d24b40",
    "pareto": "#0f766e",
    "pareto_annealed": "#8c510a",
    "sentinel": "#4d9221",
    "predictor": "#1d4ed8",
    "hybrid": "#7c3aed",
    "unknown": "#525252",
}

BG = "#f6f0e8"
PANEL = "#fbf7f2"
GRID = "#d9ccbe"
TEXT = "#2b2724"

NUMBER_RE = r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?"
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
ITERATION_RE = re.compile(
    rf"^\s*iteration\s+(?P<iteration>\d+)\s+with\s+et\s+(?P<et>{NUMBER_RE}),\s+available error\s+(?P<available>{NUMBER_RE})\s*$",
    re.IGNORECASE | re.MULTILINE,
)
TABLE_ROW_RE = re.compile(
    rf"^\s*(?P<design>\S+)\s+(?P<area>{NUMBER_RE})\s+(?P<power>{NUMBER_RE})\s+(?P<delay>{NUMBER_RE})(?:\s+(?P<error>{NUMBER_RE}|None))?\s*$",
    re.IGNORECASE,
)
RUN_LOG_NAME_RE = re.compile(r"^(?:\d+_.*|.*_r\d+)\.log$", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract per-iteration area trajectories from SubXPAT logs and plot one current-area figure per benchmark."
    )
    parser.add_argument(
        "--logs-root",
        type=Path,
        action="append",
        default=None,
        help="Repeatable batch root to scan. Defaults to the repo's i8/i10/i16 study folders.",
    )
    parser.add_argument(
        "--benchmark",
        dest="benchmarks",
        action="append",
        default=None,
        help="Repeatable benchmark filter (for example: mul_i8_o8). Defaults to mul_i8_o8, mul_i10_o10, mul_i16_o16.",
    )
    parser.add_argument(
        "--mode",
        dest="modes",
        action="append",
        default=None,
        help="Repeatable termination-mode filter (for example: none or trivial). Defaults to all discovered modes.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/iteration_area_trajectories_20260424"),
        help="Directory for the generated CSV and plots.",
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


def _clean_text(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text).replace("\r", "")


def _normalize_value(raw_value: str) -> object:
    value = raw_value.strip().rstrip(",")
    if value == "None":
        return None
    if value in {"True", "False"}:
        return value == "True"
    try:
        if any(token in value.lower() for token in (".", "e")):
            return float(value)
        return int(value)
    except ValueError:
        if "." in value:
            return value.split(".")[-1]
        return value


def _parse_specs_block(text: str) -> dict[str, object]:
    match = re.search(r"specs_obj = Specifications\(\n(?P<body>.*?)\n\)", text, re.DOTALL)
    if match is None:
        return {}

    specs: dict[str, object] = {}
    for raw_line in match.group("body").splitlines():
        line = raw_line.strip()
        if " = " not in line:
            continue
        key, value = line.split(" = ", 1)
        specs[key] = _normalize_value(value)
    return specs


def _normalize_mode(raw_mode: object) -> str:
    mode = str(raw_mode or "unknown").strip().lower()
    if mode == "smart":
        return "trivial"
    return mode


def _discover_logs(log_roots: Iterable[Path]) -> list[Path]:
    discovered: list[Path] = []
    seen: set[Path] = set()

    for raw_root in log_roots:
        root = raw_root if raw_root.is_absolute() else ROOT / raw_root
        if root.is_file():
            if root.suffix == ".log" and root not in seen:
                discovered.append(root)
                seen.add(root)
            continue
        if not root.exists():
            continue

        for path in sorted(root.rglob("*.log")):
            if path in seen:
                continue
            if path.name == "terminal.err.log" or path.name == "yosys_graph.log":
                continue
            if path.name == "terminal.out.log" or RUN_LOG_NAME_RE.match(path.name):
                discovered.append(path)
                seen.add(path)

    return discovered


def _extract_iteration_blocks(text: str) -> list[tuple[int, str]]:
    matches = list(ITERATION_RE.finditer(text))
    blocks: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        iteration = int(match.group("iteration"))
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((iteration, text[start:end]))
    return blocks


def _parse_iteration_candidate(block_text: str) -> tuple[float | None, float | None]:
    exact_area = None
    accepted_area = None
    for raw_line in block_text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("Design ID") or stripped.startswith("-----------"):
            continue
        match = TABLE_ROW_RE.match(stripped)
        if match is None:
            continue
        area = float(match.group("area"))
        design = match.group("design").lower()
        if design == "exact":
            exact_area = area
        else:
            accepted_area = area
    return exact_area, accepted_area


def _relative_log_path(log_path: Path) -> str:
    try:
        return str(log_path.resolve().relative_to(ROOT))
    except ValueError:
        return str(log_path.resolve())


def parse_log_trajectory(log_path: Path) -> pd.DataFrame | None:
    cleaned = _clean_text(log_path.read_text(errors="replace"))
    specs = _parse_specs_block(cleaned)
    if not specs:
        return None

    benchmark = str(specs.get("exact_benchmark") or specs.get("current_benchmark") or log_path.stem)
    termination_mode = _normalize_mode(specs.get("termination_mode"))
    alpha = specs.get("alpha")
    beta = specs.get("beta")
    aet = specs.get("max_error")

    blocks = _extract_iteration_blocks(cleaned)
    if not blocks:
        return None

    run_id = _relative_log_path(log_path)
    rows: list[dict[str, object]] = []
    exact_area = None
    current_area = None
    best_area = None

    for iteration, block in blocks:
        block_exact_area, accepted_area = _parse_iteration_candidate(block)
        if exact_area is None and block_exact_area is not None:
            exact_area = block_exact_area

        if accepted_area is not None:
            current_area = accepted_area
            best_area = accepted_area if best_area is None else min(best_area, accepted_area)

        rows.append(
            {
                "run_id": run_id,
                "log_path": str(log_path),
                "benchmark": benchmark,
                "termination_mode": termination_mode,
                "alpha": alpha,
                "beta": beta,
                "aet": aet,
                "iteration": iteration,
                "accepted": accepted_area is not None,
                "accepted_area": accepted_area,
                "current_area": current_area,
                "best_area_so_far": best_area,
                "exact_area": exact_area,
            }
        )

    df = pd.DataFrame(rows)
    if df["exact_area"].isna().all():
        return None

    df["exact_area"] = df["exact_area"].ffill().bfill()
    exact_area_value = df["exact_area"].iloc[0]
    if pd.notna(exact_area_value) and float(exact_area_value) != 0.0:
        df["accepted_area_pct_of_exact"] = df["accepted_area"] / df["exact_area"] * 100.0
        df["current_area_pct_of_exact"] = df["current_area"] / df["exact_area"] * 100.0
        df["best_area_pct_of_exact"] = df["best_area_so_far"] / df["exact_area"] * 100.0
    else:
        df["accepted_area_pct_of_exact"] = pd.NA
        df["current_area_pct_of_exact"] = pd.NA
        df["best_area_pct_of_exact"] = pd.NA

    return df


def build_trajectory_table(log_paths: Iterable[Path]) -> pd.DataFrame:
    frames = [frame for frame in (parse_log_trajectory(path) for path in log_paths) if frame is not None]
    if not frames:
        raise SystemExit("No parseable iteration trajectories were found in the selected logs.")
    return pd.concat(frames, ignore_index=True)


def _format_case_label(row: pd.Series) -> str:
    pieces = [str(row["termination_mode"])]
    if pd.notna(row["beta"]):
        pieces.append(f"b{int(row['beta'])}")
    if pd.notna(row["aet"]):
        pieces.append(f"e{int(row['aet'])}")
    return " / ".join(pieces)


LINE_STYLES = ("-", "--", "-.", ":")
MIN_MARKERS = ("o", "s", "D", "^", "v", "P", "X", "*")


def _build_style_map(values: Iterable[object], styles: tuple[str, ...]) -> dict[object, str]:
    ordered = sorted({value for value in values if pd.notna(value)})
    return {value: styles[index % len(styles)] for index, value in enumerate(ordered)}


def _plot_run_minimum(
    ax: plt.Axes,
    run: pd.DataFrame,
    accepted_value_col: str,
    color: str,
    marker: str,
) -> None:
    accepted = run.dropna(subset=[accepted_value_col]).sort_values("iteration")
    if accepted.empty:
        return

    min_index = accepted[accepted_value_col].idxmin()
    min_row = accepted.loc[min_index]
    ax.scatter(
        [min_row["iteration"]],
        [min_row[accepted_value_col]],
        s=70,
        marker=marker,
        facecolor=color,
        edgecolor="#ffffff",
        linewidth=0.9,
        zorder=5,
    )


def plot_benchmark_trajectory(df: pd.DataFrame, benchmark: str, output_path: Path) -> Path:
    configure_style()
    subset = df[df["benchmark"] == benchmark].copy()
    subset = subset.sort_values(["termination_mode", "beta", "aet", "run_id", "iteration"])
    if subset.empty:
        raise SystemExit(f"No rows found for benchmark {benchmark}")

    fig, ax = plt.subplots(figsize=(11.0, 6.5))

    beta_styles = _build_style_map(subset["beta"].unique(), LINE_STYLES)
    aet_markers = _build_style_map(subset["aet"].unique(), MIN_MARKERS)

    for _, run in subset.groupby("run_id", sort=False):
        run = run.sort_values("iteration")
        mode = str(run["termination_mode"].iloc[0])
        beta = run["beta"].iloc[0]
        aet = run["aet"].iloc[0]
        color = MODE_COLORS.get(mode, MODE_COLORS["unknown"])
        linestyle = beta_styles.get(beta, "-")
        marker = aet_markers.get(aet, "o")

        series = run.dropna(subset=["current_area"])
        if series.empty:
            continue

        ax.step(
            series["iteration"],
            series["current_area"],
            where="post",
            color=color,
            linestyle=linestyle,
            linewidth=2.0,
            alpha=0.78,
        )
        _plot_run_minimum(
            ax,
            run,
            accepted_value_col="accepted_area",
            color=color,
            marker=marker,
        )

    title = BENCHMARK_TITLES.get(benchmark, benchmark)
    run_count = subset["run_id"].nunique()
    mode_counts = (
        subset[["run_id", "termination_mode"]]
        .drop_duplicates()
        .groupby("termination_mode")["run_id"]
        .nunique()
        .sort_index()
        .to_dict()
    )
    mode_summary = ", ".join(f"{mode}: {count}" for mode, count in mode_counts.items())

    ax.set_title(
        f"{title}: current area over iterations\n"
        f"{run_count} runs ({mode_summary}) | color = mode, line style = beta, marker = run minimum AET"
    )
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Current area (area units)")
    max_iteration = int(subset["iteration"].max())
    ax.set_xlim(1, max_iteration)
    ax.set_xticks(range(1, max_iteration + 1))
    ax.grid(True, axis="both", alpha=0.8)
    ax.set_axisbelow(True)

    mode_handles = [
        Line2D([0], [0], color=MODE_COLORS[mode], linewidth=2.2, label=mode)
        for mode in sorted(set(subset["termination_mode"]))
    ]
    beta_handles = [
        Line2D([0], [0], color="#4b5563", linewidth=2.2, linestyle=style, label=f"beta {int(beta)}")
        for beta, style in beta_styles.items()
    ]
    aet_handles = [
        Line2D(
            [0],
            [0],
            color="#2b2724",
            marker=marker,
            linestyle="None",
            markerfacecolor="#2b2724",
            markeredgecolor="#ffffff",
            markeredgewidth=0.9,
            markersize=8,
            label=f"min @ AET {int(aet)}",
        )
        for aet, marker in aet_markers.items()
    ]
    handles = mode_handles + beta_handles + aet_handles
    ax.legend(handles=handles, loc="upper right", ncol=2)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return output_path


def main() -> None:
    args = parse_args()
    log_roots = list(args.logs_root or DEFAULT_LOG_ROOTS)
    requested_benchmarks = list(args.benchmarks or DEFAULT_BENCHMARKS)
    requested_modes = {mode.strip().lower() for mode in (args.modes or []) if mode.strip()}

    log_paths = _discover_logs(log_roots)
    if not log_paths:
        raise SystemExit("No candidate run logs were found under the selected roots.")

    trajectories = build_trajectory_table(log_paths)
    trajectories = trajectories[trajectories["benchmark"].isin(requested_benchmarks)].copy()
    if requested_modes:
        trajectories = trajectories[trajectories["termination_mode"].isin(requested_modes)].copy()
    if trajectories.empty:
        raise SystemExit("No iteration trajectories matched the selected benchmark/mode filters.")

    available_benchmarks = [bench for bench in requested_benchmarks if bench in set(trajectories["benchmark"])]
    if not available_benchmarks:
        available_benchmarks = sorted(trajectories["benchmark"].unique())

    trajectories = trajectories.sort_values(
        ["benchmark", "termination_mode", "beta", "aet", "run_id", "iteration"]
    ).reset_index(drop=True)

    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "iteration_area_trajectories.csv"
    trajectories.to_csv(csv_path, index=False)

    plot_paths = []
    for benchmark in available_benchmarks:
        plot_paths.append(
            plot_benchmark_trajectory(
                trajectories,
                benchmark,
                output_dir / f"{benchmark}_current_area_trajectory.png",
            )
        )

    print(f"Wrote trajectory CSV to {csv_path}")
    for plot_path in plot_paths:
        print(f"Wrote benchmark plot to {plot_path}")


if __name__ == "__main__":
    main()
