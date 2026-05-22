#!/usr/bin/env python3
"""Generate row-timeline plots for one SubXPAT run or a whole sweep.

This is a small convenience wrapper around plot_run_artifacts.py. It writes the
specific files people usually want when inspecting an iteration story:
plots/row_timeline.png and plots/row_timeline.csv.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from plot_run_artifacts import (
    discover_run_dirs,
    make_grid_rows,
    make_trace_table,
    plot_row_timeline,
    resolve_artifacts,
    resolve_path,
    safe_read_csv,
    safe_read_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create row_timeline.png/csv for one run or recursively for a sweep."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Run directories, or sweep/group directories when --recursive is used.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Find all run directories below each provided path.",
    )
    parser.add_argument(
        "--plots-dir-name",
        default="plots",
        help="Name of the plots folder inside each run directory (default: plots).",
    )
    return parser.parse_args()


def generate_for_run(run_dir: Path, plots_dir_name: str) -> Optional[Path]:
    artifacts = resolve_artifacts(run_dir)
    summary = safe_read_json(artifacts["summary_json"])
    trace = safe_read_csv(artifacts["trace_csv"])
    grid = safe_read_csv(artifacts["grid_csv"])

    trace_table = make_trace_table(trace, summary)
    grid_rows = make_grid_rows(grid, trace_table)
    if grid_rows.empty:
        print(f"Skipped {run_dir}: no grid rows found")
        return None

    plots_dir = run_dir / plots_dir_name
    plots_dir.mkdir(parents=True, exist_ok=True)
    grid_rows.to_csv(plots_dir / "row_timeline.csv", index=False)
    output_path = plot_row_timeline(grid_rows, summary, plots_dir / "row_timeline.png")
    if output_path is None:
        print(f"Skipped {run_dir}: row timeline could not be plotted")
        return None

    print(f"Wrote {output_path}")
    return output_path


def main() -> int:
    args = parse_args()
    run_dirs = discover_run_dirs(
        [resolve_path(path) for path in args.paths],
        recursive=args.recursive,
        include_incomplete=False,
    )
    if not run_dirs:
        raise SystemExit("No completed run directories found.")

    written = 0
    for run_dir in run_dirs:
        if generate_for_run(run_dir, args.plots_dir_name) is not None:
            written += 1

    print(f"Generated {written} row timeline plot(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
