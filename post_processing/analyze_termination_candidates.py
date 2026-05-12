from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class RuleHit:
    rule: str
    iteration: int | None
    value: float | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect SubXPAT trace CSVs and summarize online termination signals "
            "against the observed first global-minimum iteration."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/figure/iteration_area_trajectories_20260424/termination_analysis"),
        help="Directory where CSV summaries are written.",
    )
    parser.add_argument(
        "--scope",
        choices=("latest", "all"),
        default="latest",
        help="Use the latest new-pareto experiment families by default; use all for every discovered trace.",
    )
    return parser.parse_args()


def collect_trace_paths(scope: str) -> list[Path]:
    paths: set[Path] = set()
    latest_patterns = (
        "benchmarking/generated/zone_aet_i8_pareto_satstreak_20260425_110043/**/artifacts/*_trace.csv",
        "benchmarking/generated/zone_aet_i8_pareto_satstreak_patience_20260425_142805_p*/**/artifacts/*_trace.csv",
        "benchmarking/generated/zone_aet_i10_pareto_satstreak_20260425_110043/**/artifacts/*_trace.csv",
        "benchmarking/generated/zone_aet_i10_pareto_satstreak_patience_20260425_142805_p*/**/artifacts/*_trace.csv",
        "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_annealed_isolated_20260424/artifacts/*_trace.csv",
        "benchmarking/generated/zone_aet_i16_singlecase_350_b64_pareto_patience3_20260426_081734/artifacts/*_trace.csv",
        "output/report/termination_study/*mul_i16_o16*termnone*20260419:151608_trace.csv",
    )
    all_patterns = (
        "benchmarking/generated/*pareto*/**/artifacts/*_trace.csv",
        "output/report/termination_study/*_trace.csv",
    )
    patterns = latest_patterns if scope == "latest" else all_patterns
    for pattern in patterns:
        paths.update(ROOT.glob(pattern))
    return sorted(paths)


def parse_case_metadata(path: Path, df: pd.DataFrame) -> dict[str, object]:
    name = path.name
    benchmark = None
    max_error = None
    mode = None
    match = re.search(
        r"grid_(?P<benchmark>mul_i\d+_o\d+)_.*?_et(?P<et>\d+)_.*?_term(?P<mode>[a-z_]+)_",
        name,
    )
    if match:
        benchmark = match.group("benchmark")
        max_error = int(match.group("et"))
        mode = match.group("mode")

    if benchmark is None and "benchmark" in df.columns and not df.empty:
        raw_benchmark = str(df["benchmark"].dropna().iloc[0])
        bench_match = re.match(r"(mul_i\d+_o\d+)", raw_benchmark)
        benchmark = bench_match.group(1) if bench_match else raw_benchmark

    if max_error is None and "et" in df.columns and not df.empty:
        et_series = pd.to_numeric(df["et"], errors="coerce").dropna()
        if not et_series.empty:
            max_error = int(et_series.iloc[0])

    if mode is None and "termination_mode" in df.columns and not df.empty:
        mode = str(df["termination_mode"].dropna().iloc[0])

    beta = None
    alpha = None
    text_path = str(path)
    beta_match = re.search(r"/b(?P<beta>\d+)_a(?P<alpha>\d+)_e\d+_", text_path)
    if beta_match:
        beta = int(beta_match.group("beta"))
        alpha = int(beta_match.group("alpha"))
    else:
        beta_match = re.search(r"_b(?P<beta>\d+)_", text_path)
        if beta_match:
            beta = int(beta_match.group("beta"))
        if benchmark == "mul_i16_o16" and max_error == 350:
            beta = 64
            alpha = 2

    if path.parent.name == "artifacts":
        case_dir = path.parent.parent
        run_dir = case_dir.parent
        label = case_dir.name if run_dir.name == "generated" else f"{run_dir.name}/{case_dir.name}"
    else:
        label = path.stem
    return {
        "case": label,
        "benchmark": benchmark,
        "max_error": max_error,
        "termination_mode": mode,
        "beta": beta,
        "alpha": alpha,
        "path": str(path.relative_to(ROOT)),
    }


def operand_bits_from_benchmark(benchmark: object) -> int | None:
    if benchmark is None or pd.isna(benchmark):
        return None
    match = re.search(r"_i(?P<bits>\d+)_o\d+$", str(benchmark))
    if match is None:
        return None
    total_input_bits = int(match.group("bits"))
    if total_input_bits <= 0 or total_input_bits % 2:
        return None
    return total_input_bits // 2


def trivial_ceiling(benchmark: object, max_error: object, beta: object) -> float | None:
    operand_bits = operand_bits_from_benchmark(benchmark)
    if operand_bits is None or beta is None or max_error is None:
        return None
    if pd.isna(beta) or pd.isna(max_error):
        return None
    return float(beta) * float(max_error) / float(operand_bits)


def numeric_column(df: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[column], errors="coerce").fillna(default)


def bool_column(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series([False] * len(df), index=df.index)
    values = df[column]
    if values.dtype == bool:
        return values.fillna(False)
    return values.astype(str).str.lower().isin({"true", "1", "yes"})


def prepare_trace(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["iteration"] = pd.to_numeric(out["iteration"], errors="coerce").astype("Int64")
    out = out.dropna(subset=["iteration"]).copy()
    out["iteration"] = out["iteration"].astype(int)
    out["status"] = out.get("status", "").astype(str).str.upper()
    out["candidate_area"] = pd.to_numeric(out.get("best_area"), errors="coerce")
    out["accepted_sat"] = out["status"].eq("SAT") & out["candidate_area"].notna()
    accepted_area = out["candidate_area"].where(out["accepted_sat"])
    out["current_area"] = accepted_area.cummin().ffill()
    return out


def first_iteration_where(mask: pd.Series, iterations: pd.Series) -> int | None:
    hits = iterations[mask.fillna(False)]
    if hits.empty:
        return None
    return int(hits.iloc[0])


def first_streak_hit(mask: pd.Series, iterations: pd.Series, patience: int) -> RuleHit:
    streak = 0
    for ok, iteration in zip(mask.fillna(False), iterations):
        streak = streak + 1 if ok else 0
        if streak >= patience:
            return RuleHit(rule="", iteration=int(iteration), value=float(streak))
    return RuleHit(rule="", iteration=None, value=None)


def compute_rule_hits(df: pd.DataFrame, meta: dict[str, object]) -> list[RuleHit]:
    iterations = df["iteration"]
    grid_sat = numeric_column(df, "grid_sat_count")
    grid_unsat = numeric_column(df, "grid_unsat_count")
    grid_unknown = numeric_column(df, "grid_unknown_count")
    grid_dominated = numeric_column(df, "grid_dominated_count")
    grid_timeout = numeric_column(df, "grid_timeout_count")
    grid_negative = numeric_column(df, "grid_negative_ratio")
    best_improved = bool_column(df, "best_seen_improved")
    status = df["status"]

    grid_work = grid_sat.add(grid_unsat).add(grid_unknown).add(grid_dominated).add(grid_timeout).gt(0)
    active_row = ~status.eq("STOPPED") | grid_work
    no_sat = grid_sat.eq(0) & active_row
    no_improvement = ~best_improved & active_row
    all_negative = grid_negative.ge(1.0) & active_row
    timeout_heavy = no_sat & (grid_unknown.add(grid_timeout).gt(0))

    hits: list[RuleHit] = []
    for patience in range(1, 6):
        hit = first_streak_hit(no_sat, iterations, patience)
        hits.append(RuleHit(f"no_sat_streak_{patience}", hit.iteration, hit.value))
        hit = first_streak_hit(no_improvement, iterations, patience)
        hits.append(RuleHit(f"best_area_patience_{patience}", hit.iteration, hit.value))
        hit = first_streak_hit(all_negative, iterations, patience)
        hits.append(RuleHit(f"all_negative_grid_streak_{patience}", hit.iteration, hit.value))
        hit = first_streak_hit(timeout_heavy, iterations, patience)
        hits.append(RuleHit(f"timeout_negative_streak_{patience}", hit.iteration, hit.value))

    ceiling = trivial_ceiling(meta["benchmark"], meta["max_error"], meta["beta"])
    if ceiling is not None and "bit_weight" in df.columns:
        bit_weight = pd.to_numeric(df["bit_weight"], errors="coerce")
        iteration = first_iteration_where(bit_weight.gt(ceiling), iterations)
        hits.append(RuleHit("trivial_bit_ceiling", iteration, ceiling))

    if "same_subgraph_streak" in df.columns:
        same_subgraph = numeric_column(df, "same_subgraph_streak")
        for patience in range(1, 4):
            iteration = first_iteration_where(same_subgraph.ge(patience), iterations)
            hits.append(RuleHit(f"same_subgraph_streak_{patience}", iteration, float(patience)))

    return hits


def summarize_case(path: Path) -> tuple[dict[str, object], list[dict[str, object]]]:
    raw_df = pd.read_csv(path)
    df = prepare_trace(raw_df)
    meta = parse_case_metadata(path, df)

    area = df["current_area"].dropna()
    if area.empty:
        first_min_iteration = None
        global_min_area = math.nan
    else:
        global_min_area = float(area.min())
        first_min_iteration = int(df.loc[df["current_area"].eq(global_min_area), "iteration"].iloc[0])

    final_iteration = int(df["iteration"].max()) if not df.empty else None
    final_area = float(area.iloc[-1]) if not area.empty else math.nan
    final_status = str(df["status"].iloc[-1]) if not df.empty else ""
    stop_reason = str(df.get("stop_reason", pd.Series([""] * len(df))).fillna("").iloc[-1]) if not df.empty else ""
    runtime = numeric_column(df, "runtime_elapsed_seconds", math.nan)
    final_runtime_seconds = float(runtime.dropna().iloc[-1]) if not runtime.dropna().empty else math.nan
    post_min_rows = 0 if first_min_iteration is None else int((df["iteration"] > first_min_iteration).sum())
    post_min_runtime_seconds = math.nan
    if first_min_iteration is not None and "runtime_elapsed_seconds" in df.columns:
        at_min = pd.to_numeric(
            df.loc[df["iteration"].eq(first_min_iteration), "runtime_elapsed_seconds"],
            errors="coerce",
        ).dropna()
        end = pd.to_numeric(df["runtime_elapsed_seconds"], errors="coerce").dropna()
        if not at_min.empty and not end.empty:
            post_min_runtime_seconds = float(end.iloc[-1] - at_min.iloc[-1])

    summary = {
        **meta,
        "iterations": final_iteration,
        "first_observed_min_iteration": first_min_iteration,
        "observed_min_area": global_min_area,
        "final_area": final_area,
        "final_status": final_status,
        "stop_reason": stop_reason,
        "runtime_hours": final_runtime_seconds / 3600.0 if not math.isnan(final_runtime_seconds) else math.nan,
        "post_min_iterations": post_min_rows,
        "post_min_runtime_hours": post_min_runtime_seconds / 3600.0
        if not math.isnan(post_min_runtime_seconds)
        else math.nan,
    }

    rule_rows: list[dict[str, object]] = []
    for hit in compute_rule_hits(df, meta):
        iteration = hit.iteration
        if first_min_iteration is None or iteration is None:
            relation = "missing"
            overshoot = math.nan
            saved = math.nan
        else:
            overshoot = iteration - first_min_iteration
            saved = final_iteration - iteration if final_iteration is not None else math.nan
            relation = "early" if overshoot < 0 else "safe_or_at_min"
        rule_rows.append(
            {
                **meta,
                "rule": hit.rule,
                "rule_iteration": iteration,
                "rule_value": hit.value,
                "first_observed_min_iteration": first_min_iteration,
                "observed_min_area": global_min_area,
                "final_iteration": final_iteration,
                "overshoot_iterations": overshoot,
                "saved_iterations_vs_observed_end": saved,
                "relation_to_observed_min": relation,
            }
        )

    return summary, rule_rows


def aggregate_rules(rule_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule, group in rule_df.groupby("rule", sort=True):
        fired = group["rule_iteration"].notna()
        safe = group["relation_to_observed_min"].eq("safe_or_at_min")
        early = group["relation_to_observed_min"].eq("early")
        rows.append(
            {
                "rule": rule,
                "cases": len(group),
                "fired_cases": int(fired.sum()),
                "safe_cases": int(safe.sum()),
                "early_cases": int(early.sum()),
                "missing_cases": int((~fired).sum()),
                "median_overshoot_iterations": group.loc[safe, "overshoot_iterations"].median(),
                "median_saved_iterations": group.loc[safe, "saved_iterations_vs_observed_end"].median(),
                "mean_saved_iterations": group.loc[safe, "saved_iterations_vs_observed_end"].mean(),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["early_cases", "missing_cases", "median_overshoot_iterations", "rule"],
        ascending=[True, True, True, True],
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    rules = []
    for path in collect_trace_paths(args.scope):
        try:
            summary, rule_rows = summarize_case(path)
        except Exception as exc:  # Keep exploratory scans robust.
            summaries.append({"case": path.stem, "path": str(path.relative_to(ROOT)), "error": str(exc)})
            continue
        summaries.append(summary)
        rules.extend(rule_rows)

    summary_df = pd.DataFrame(summaries)
    rule_df = pd.DataFrame(rules)
    aggregate_df = aggregate_rules(rule_df) if not rule_df.empty else pd.DataFrame()

    summary_path = output_dir / "termination_candidate_case_summary.csv"
    rule_path = output_dir / "termination_candidate_rule_hits.csv"
    aggregate_path = output_dir / "termination_candidate_rule_aggregate.csv"
    summary_df.to_csv(summary_path, index=False)
    rule_df.to_csv(rule_path, index=False)
    aggregate_df.to_csv(aggregate_path, index=False)

    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {rule_path.relative_to(ROOT)}")
    print(f"Wrote {aggregate_path.relative_to(ROOT)}")
    if not aggregate_df.empty:
        print("\nBest aggregate rule candidates:")
        print(
            aggregate_df.head(12).to_string(
                index=False,
                columns=[
                    "rule",
                    "cases",
                    "fired_cases",
                    "safe_cases",
                    "early_cases",
                    "missing_cases",
                    "median_overshoot_iterations",
                    "median_saved_iterations",
                ],
            )
        )
    if not summary_df.empty:
        interesting = summary_df[
            summary_df["benchmark"].isin(["mul_i8_o8", "mul_i10_o10", "mul_i16_o16"])
            & summary_df["termination_mode"].astype(str).str.contains("pareto|none", na=False)
        ].copy()
        if not interesting.empty:
            interesting = interesting.sort_values(["benchmark", "max_error", "beta", "termination_mode", "case"])
            print("\nObserved minima by case:")
            print(
                interesting[
                    [
                        "case",
                        "benchmark",
                        "termination_mode",
                        "beta",
                        "max_error",
                        "iterations",
                        "first_observed_min_iteration",
                        "observed_min_area",
                        "post_min_iterations",
                        "post_min_runtime_hours",
                    ]
                ].to_string(index=False)
            )


if __name__ == "__main__":
    main()
