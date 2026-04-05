from __future__ import annotations

import argparse
import csv
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from poolex import dict_to_args, run_experiment


DEFAULT_BENCHMARKS = ("mul_i10_o10", "mul_i12_o12", "mul_i16_o16")
DEFAULT_ALPHAS = (1, 2, 3)
DEFAULT_BETAS = (32, 64, 96)
DEFAULT_MODES = ("none", "trivial")
DEFAULT_AETS = (300,)


def _parse_csv_positive_ints(raw: str) -> List[int]:
    values = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        value = int(item)
        if value <= 0:
            raise ValueError(f"Expected positive integer, got {value}")
        values.append(value)
    if not values:
        raise ValueError("Expected a non-empty comma-separated list of positive integers")
    return values


def _parse_csv_strings(raw: str) -> List[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise ValueError("Expected a non-empty comma-separated list")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a large parallel ZONE_AET sweep via poolex-style isolated experiment copies.",
    )
    parser.add_argument(
        "--benchmarks",
        default=",".join(DEFAULT_BENCHMARKS),
        help="Comma-separated benchmark names (default: mul_i10_o10,mul_i12_o12,mul_i16_o16)",
    )
    parser.add_argument(
        "--alphas",
        default=",".join(str(value) for value in DEFAULT_ALPHAS),
        help="Comma-separated alpha values (default: 1,2,3)",
    )
    parser.add_argument(
        "--betas",
        default=",".join(str(value) for value in DEFAULT_BETAS),
        help="Comma-separated beta values (default: 32,64,96)",
    )
    parser.add_argument(
        "--modes",
        default=",".join(DEFAULT_MODES),
        help="Comma-separated termination modes (default: none,trivial)",
    )
    parser.add_argument(
        "--aets",
        default=",".join(str(value) for value in DEFAULT_AETS),
        help="Comma-separated AET / max-error values for the sweep (default: 300)",
    )
    parser.add_argument(
        "--aet",
        type=int,
        default=None,
        help="Single AET shortcut (overrides --aets when provided)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10800,
        help="Per-run timeout in seconds (default: 10800)",
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=3,
        help="Maximum number of isolated parallel experiments (default: 3)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        help="Output root for copied experiment folders (default: benchmarking/generated/zone_aet_large_mul_YYYYMMDD_HHMMSS)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned experiments and manifest without running them",
    )
    return parser.parse_args()


def _task_name(benchmark: str, aet: int, beta: int, alpha: int, mode: str) -> str:
    return f"{benchmark}_e{aet}_b{beta}_a{alpha}_{mode}"


def _build_common_args(timeout: int) -> Dict[str, object]:
    return {
        "subxpat": True,
        "metric": "wre",
        "extraction-mode": 0,
        "input-max": 4,
        "output-max": 2,
        "template": "nonshared",
        "encoding": "z3bvec",
        "max-lpp": 4,
        "max-ppo": 4,
        "constants": "never",
        "error-partitioning": "asc",
        "timeout": timeout,
        "cnn-constraint": "zone_aet",
        "skip-verification": True,
    }


def _write_manifest(
    manifest_path: Path,
    tasks: List[Tuple[str, str, Dict[str, object]]],
    base_dir: Path,
    output_root: Path,
) -> None:
    with manifest_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "task_name",
                "benchmark",
                "aet",
                "alpha",
                "beta",
                "termination_mode",
                "destination_dir",
                "command",
            ]
        )
        python_executable = os.getenv("PYTHON", "python")
        for name, benchmark, args in tasks:
            destination_dir = output_root / name
            command = " ".join(
                [python_executable, "main.py", benchmark, *dict_to_args(args)]
            )
            writer.writerow(
                [
                    name,
                    benchmark,
                    args["max-error"],
                    args["alpha"],
                    args["beta"],
                    args["termination-mode"],
                    destination_dir,
                    command,
                ]
            )


def main() -> int:
    args = parse_args()

    benchmarks = _parse_csv_strings(args.benchmarks)
    alphas = _parse_csv_positive_ints(args.alphas)
    betas = _parse_csv_positive_ints(args.betas)
    aets = [args.aet] if args.aet is not None else _parse_csv_positive_ints(args.aets)
    modes = _parse_csv_strings(args.modes)

    invalid_modes = [mode for mode in modes if mode not in {"none", "trivial"}]
    if invalid_modes:
        raise ValueError(f"Unsupported modes: {', '.join(invalid_modes)}")

    base_dir = Path.cwd()
    output_root = args.output_root or (
        base_dir
        / "benchmarking"
        / "generated"
        / f"zone_aet_large_mul_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    output_root.mkdir(parents=True, exist_ok=True)

    common_args = _build_common_args(args.timeout)
    tasks: List[Tuple[str, str, Dict[str, object]]] = []
    for benchmark in benchmarks:
        for aet in aets:
            for beta in betas:
                for alpha in alphas:
                    for mode in modes:
                        task_args = {
                            **common_args,
                            "max-error": aet,
                            "baseet": aet,
                            "beta": beta,
                            "alpha": alpha,
                            "termination-mode": mode,
                        }
                        tasks.append((_task_name(benchmark, aet, beta, alpha, mode), benchmark, task_args))

    manifest_path = output_root / "run_manifest.tsv"
    summary_path = output_root / "run_summary.tsv"
    _write_manifest(manifest_path, tasks, base_dir, output_root)

    with summary_path.open("w", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "task_name",
                "benchmark",
                "aet",
                "alpha",
                "beta",
                "termination_mode",
                "returncode",
                "destination_dir",
            ]
        )

    print("Running large ZONE_AET sweep with poolex isolation")
    print(f"Benchmarks:   {', '.join(benchmarks)}")
    print(f"AETs:         {aets}")
    print(f"Alphas:       {alphas}")
    print(f"Betas:        {betas}")
    print(f"Modes:        {modes}")
    print(f"Max parallel: {args.max_parallel}")
    print(f"Output root:  {output_root}")
    print(f"Total tasks:  {len(tasks)}")

    if args.dry_run:
        for task_name, benchmark, task_args in tasks:
            print(f"DRY-RUN {task_name}: {benchmark} {dict_to_args(task_args)}")
        return 0

    with ThreadPoolExecutor(max_workers=args.max_parallel) as executor:
        future_to_task = {
            executor.submit(
                run_experiment,
                task_name,
                benchmark,
                task_args,
                str(base_dir),
                str(output_root),
            ): (task_name, benchmark, task_args)
            for task_name, benchmark, task_args in tasks
        }

        with summary_path.open("a", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t")
            for future in as_completed(future_to_task):
                task_name, benchmark, task_args = future_to_task[future]
                destination_dir = output_root / task_name
                try:
                    _, completed = future.result()
                    returncode = completed.returncode
                except Exception:
                    returncode = -1
                writer.writerow(
                    [
                        task_name,
                        benchmark,
                        task_args["max-error"],
                        task_args["alpha"],
                        task_args["beta"],
                        task_args["termination-mode"],
                        returncode,
                        destination_dir,
                    ]
                )
                handle.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
