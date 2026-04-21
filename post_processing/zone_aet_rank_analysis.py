from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import os

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-cache")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd


THRESHOLD_BANDS = ["highest", "high", "middle-high", "middle", "middle-low", "lowest"]
THRESHOLD_BAND_INDEX = {label: idx for idx, label in enumerate(THRESHOLD_BANDS)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create clearer threshold-rank plots for ZONE_AET rank sweeps."
    )
    parser.add_argument(
        "--runs-csv",
        type=Path,
        required=True,
        help="Path to termination_study_runs.csv for the rank sweep.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where the extra plots and summaries should be written.",
    )
    return parser.parse_args()


def band_from_rank(rank: int, level_count: int) -> str:
    if level_count <= 1:
        return "highest"
    normalized = rank / (level_count - 1)
    band_idx = int(round(normalized * (len(THRESHOLD_BANDS) - 1)))
    band_idx = min(max(band_idx, 0), len(THRESHOLD_BANDS) - 1)
    return THRESHOLD_BANDS[band_idx]


def load_rank_runs(runs_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(runs_csv)
    df = df[df["cnn_constraint"] == "ZONE_AET"].copy()
    df = df[df["benchmark"] == "mul_i8_o8"].copy()
    df["max_error"] = pd.to_numeric(df["max_error"], errors="coerce")
    df["beta"] = pd.to_numeric(df["beta"], errors="coerce")
    df["runtime_seconds"] = pd.to_numeric(df["runtime_seconds"], errors="coerce")
    df["final_area"] = pd.to_numeric(df["final_area"], errors="coerce")
    df["termination_zone_rank_from_max"] = pd.to_numeric(
        df["termination_zone_rank_from_max"], errors="coerce"
    )
    df["termination_zone_level_count"] = pd.to_numeric(
        df["termination_zone_level_count"], errors="coerce"
    )
    df["termination_ceiling"] = pd.to_numeric(df["termination_ceiling"], errors="coerce")
    return df.dropna(subset=["max_error", "beta", "runtime_seconds", "final_area"])


def build_rank_delta_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []
    for (aet, beta), group in df.groupby(["max_error", "beta"]):
        none_rows = group[group["termination_mode"] == "none"]
        if none_rows.empty:
            continue
        none = none_rows.iloc[0]
        trivial = group[group["termination_mode"] == "trivial"].copy()
        if trivial.empty:
            continue

        fallback_level_count = int(trivial["termination_zone_rank_from_max"].max()) + 1
        for _, row in trivial.sort_values("termination_zone_rank_from_max").iterrows():
            level_count = row["termination_zone_level_count"]
            if pd.isna(level_count) or int(level_count) <= 0:
                level_count = fallback_level_count
            level_count = int(level_count)
            rank = int(row["termination_zone_rank_from_max"])
            band = band_from_rank(rank, level_count)
            area_improvement = float(none["final_area"]) - float(row["final_area"])
            runtime_improvement = float(none["runtime_seconds"]) - float(row["runtime_seconds"])
            rows.append(
                {
                    "case_id": f"AET={int(aet)}, beta={int(beta)}",
                    "aet": int(aet),
                    "beta": int(beta),
                    "rank": rank,
                    "level_count": level_count,
                    "band": band,
                    "band_index": THRESHOLD_BAND_INDEX[band],
                    "termination_ceiling": None if pd.isna(row["termination_ceiling"]) else int(row["termination_ceiling"]),
                    "none_area": float(none["final_area"]),
                    "none_runtime_seconds": float(none["runtime_seconds"]),
                    "trivial_area": float(row["final_area"]),
                    "trivial_runtime_seconds": float(row["runtime_seconds"]),
                    "area_improvement": area_improvement,
                    "runtime_improvement": runtime_improvement,
                    "stop_reason": row["stop_reason"],
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["quality_flag"] = np.where(
        out["area_improvement"] > 1e-9,
        "better",
        np.where(out["area_improvement"] < -1e-9, "worse", "same"),
    )
    return out.sort_values(["aet", "beta", "rank"]).reset_index(drop=True)


def build_heatmap_matrix(data: pd.DataFrame, value_column: str) -> tuple[np.ndarray, List[str], List[str], Dict[tuple[int, int], str]]:
    cases = list(dict.fromkeys(data["case_id"].tolist()))
    matrix = np.full((len(cases), len(THRESHOLD_BANDS)), np.nan)
    annotations: Dict[tuple[int, int], str] = {}
    case_index = {case: idx for idx, case in enumerate(cases)}

    for _, row in data.iterrows():
        row_idx = case_index[row["case_id"]]
        col_idx = THRESHOLD_BAND_INDEX[row["band"]]
        matrix[row_idx, col_idx] = row[value_column]
        ceiling_text = "NA" if pd.isna(row["termination_ceiling"]) else str(int(row["termination_ceiling"]))
        if value_column == "area_improvement":
            metric_text = f"{row[value_column]:+.2f}"
        else:
            metric_text = f"{row[value_column]:+.0f}s"
        annotations[(row_idx, col_idx)] = f"zr{int(row['rank'])}\n{ceiling_text}\n{metric_text}"

    return matrix, cases, THRESHOLD_BANDS, annotations


def plot_heatmaps(rank_df: pd.DataFrame, output_dir: Path) -> Path:
    area_matrix, cases, bands, area_annotations = build_heatmap_matrix(rank_df, "area_improvement")
    runtime_matrix, _, _, runtime_annotations = build_heatmap_matrix(rank_df, "runtime_improvement")

    area_limit = float(np.nanmax(np.abs(area_matrix))) if np.isfinite(area_matrix).any() else 1.0
    runtime_limit = float(np.nanmax(np.abs(runtime_matrix))) if np.isfinite(runtime_matrix).any() else 1.0
    area_limit = max(area_limit, 1e-6)
    runtime_limit = max(runtime_limit, 1e-6)

    fig, (ax_area, ax_runtime) = plt.subplots(
        nrows=1,
        ncols=2,
        figsize=(16, max(6.5, len(cases) * 0.8)),
        sharey=True,
    )

    area_image = ax_area.imshow(
        area_matrix,
        aspect="auto",
        cmap="RdYlGn",
        norm=TwoSlopeNorm(vmin=-area_limit, vcenter=0.0, vmax=area_limit),
    )
    runtime_image = ax_runtime.imshow(
        runtime_matrix,
        aspect="auto",
        cmap="RdYlGn",
        norm=TwoSlopeNorm(vmin=-runtime_limit, vcenter=0.0, vmax=runtime_limit),
    )

    for ax, annotations in ((ax_area, area_annotations), (ax_runtime, runtime_annotations)):
        ax.set_xticks(range(len(bands)))
        ax.set_xticklabels(bands, rotation=25, ha="right")
        ax.set_yticks(range(len(cases)))
        ax.set_yticklabels(cases)
        ax.set_xticks(np.arange(-0.5, len(bands), 1), minor=True)
        ax.set_yticks(np.arange(-0.5, len(cases), 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)
        for (row_idx, col_idx), text in annotations.items():
            ax.text(col_idx, row_idx, text, ha="center", va="center", fontsize=8, color="black")

    ax_area.set_title("Area improvement vs none\npositive is better")
    ax_area.set_xlabel("Threshold band")
    ax_area.set_ylabel("AET / beta case")

    ax_runtime.set_title("Runtime improvement vs none\npositive is faster")
    ax_runtime.set_xlabel("Threshold band")

    area_colorbar = fig.colorbar(area_image, ax=ax_area, fraction=0.046, pad=0.04)
    area_colorbar.set_label("none area - trivial area")
    runtime_colorbar = fig.colorbar(runtime_image, ax=ax_runtime, fraction=0.046, pad=0.04)
    runtime_colorbar.set_label("none runtime - trivial runtime (s)")

    fig.suptitle(
        "ZONE_AET ranked-threshold sweep on mul_i8_o8\n"
        "Each cell shows rank, selected ceiling, and improvement relative to the none baseline",
        y=0.98,
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    output_path = output_dir / "mul_i8_o8_threshold_band_heatmaps.png"
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def plot_case_lines(rank_df: pd.DataFrame, output_dir: Path) -> Path:
    fig, (ax_area, ax_runtime) = plt.subplots(nrows=2, ncols=1, figsize=(13, 9), sharex=True)

    color_map = {4: "#c2410c", 6: "#2563eb", 8: "#7c3aed"}
    marker_map = {16: "o", 24: "s", 32: "^"}

    for (aet, beta), group in rank_df.groupby(["aet", "beta"]):
        group = group.sort_values("band_index")
        label = f"AET={int(aet)}, beta={int(beta)}"
        color = color_map.get(int(beta), "#4b5563")
        marker = marker_map.get(int(aet), "o")
        x_values = group["band_index"].to_numpy()
        ax_area.plot(x_values, group["area_improvement"], marker=marker, color=color, linewidth=2, label=label)
        ax_runtime.plot(x_values, group["runtime_improvement"], marker=marker, color=color, linewidth=2, label=label)
        for _, row in group.iterrows():
            ax_area.annotate(
                f"zr{int(row['rank'])}",
                (row["band_index"], row["area_improvement"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
                color=color,
            )
            ax_runtime.annotate(
                f"zr{int(row['rank'])}",
                (row["band_index"], row["runtime_improvement"]),
                xytext=(4, 4),
                textcoords="offset points",
                fontsize=8,
                color=color,
            )

    ax_area.axhline(0.0, color="#6b7280", linewidth=1.2, linestyle="--")
    ax_runtime.axhline(0.0, color="#6b7280", linewidth=1.2, linestyle="--")
    ax_area.set_ylabel("Area improvement vs none")
    ax_area.set_title("How QoR changes as the threshold becomes more aggressive")
    ax_area.grid(alpha=0.3)

    ax_runtime.set_ylabel("Runtime improvement vs none (s)")
    ax_runtime.set_xlabel("Threshold band: highest -> lowest")
    ax_runtime.set_xticks(range(len(THRESHOLD_BANDS)))
    ax_runtime.set_xticklabels(THRESHOLD_BANDS, rotation=20, ha="right")
    ax_runtime.grid(alpha=0.3)

    handles, labels = ax_area.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3)
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    output_path = output_dir / "mul_i8_o8_threshold_band_trends.png"
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path


def write_report(rank_df: pd.DataFrame, output_dir: Path) -> Path:
    def _fmt_rank(value: object) -> str:
        if pd.isna(value):
            return "zr?"
        return f"zr{int(value)}"

    def _fmt_ceiling(value: object) -> str:
        if pd.isna(value):
            return "NA"
        return str(int(value))

    lines = [
        "# Threshold Band Interpretation",
        "",
        "Threshold bands are normalized within each `(AET, beta)` case.",
        "- `highest` means the loosest ceiling, closest to the old `max(thresholds)` rule.",
        "- `lowest` means the most aggressive ceiling, using the smallest tested threshold level.",
        "- Positive area improvement means the ranked trivial run ended with a smaller area than the `none` baseline.",
        "- Positive runtime improvement means the ranked trivial run finished faster than the `none` baseline.",
        "",
        "## Best Safe Threshold Per Case",
        "",
    ]

    summary_rows = []
    for (aet, beta), group in rank_df.groupby(["aet", "beta"]):
        group = group.sort_values(["area_improvement", "runtime_improvement"], ascending=[False, False])
        safe = rank_df[
            (rank_df["aet"] == aet)
            & (rank_df["beta"] == beta)
            & (np.isclose(rank_df["area_improvement"], 0.0))
        ].sort_values(["runtime_improvement", "rank"], ascending=[False, True])
        improving = rank_df[
            (rank_df["aet"] == aet)
            & (rank_df["beta"] == beta)
            & (rank_df["area_improvement"] > 0.0)
        ].sort_values(["area_improvement", "runtime_improvement"], ascending=[False, False])

        if not safe.empty:
            row = safe.iloc[0]
            lines.append(
                f"- `AET={int(aet)}, beta={int(beta)}`: safest useful band is `{row['band']}` / `{_fmt_rank(row['rank'])}` "
                f"(ceiling `{_fmt_ceiling(row['termination_ceiling'])}`, runtime gain `{row['runtime_improvement']:+.0f}s`, area unchanged)"
            )
            summary_rows.append(
                {
                    "aet": int(aet),
                    "beta": int(beta),
                    "recommended_type": "safe_same_area",
                    "band": row["band"],
                    "rank": int(row["rank"]),
                    "termination_ceiling": None if pd.isna(row["termination_ceiling"]) else int(row["termination_ceiling"]),
                    "area_improvement": float(row["area_improvement"]),
                    "runtime_improvement": float(row["runtime_improvement"]),
                }
            )
        elif not improving.empty:
            row = improving.iloc[0]
            lines.append(
                f"- `AET={int(aet)}, beta={int(beta)}`: no same-area rank, but `{row['band']}` / `{_fmt_rank(row['rank'])}` "
                f"improves area by `{row['area_improvement']:+.4f}` with runtime gain `{row['runtime_improvement']:+.0f}s`"
            )
            summary_rows.append(
                {
                    "aet": int(aet),
                    "beta": int(beta),
                    "recommended_type": "better_area",
                    "band": row["band"],
                    "rank": int(row["rank"]),
                    "termination_ceiling": None if pd.isna(row["termination_ceiling"]) else int(row["termination_ceiling"]),
                    "area_improvement": float(row["area_improvement"]),
                    "runtime_improvement": float(row["runtime_improvement"]),
                }
            )
        else:
            row = rank_df[(rank_df["aet"] == aet) & (rank_df["beta"] == beta)].sort_values(
                ["runtime_improvement", "area_improvement"], ascending=[False, False]
            ).iloc[0]
            lines.append(
                f"- `AET={int(aet)}, beta={int(beta)}`: all stronger bands hurt area; least-damaging fast option is "
                f"`{row['band']}` / `{_fmt_rank(row['rank'])}`"
            )
            summary_rows.append(
                {
                    "aet": int(aet),
                    "beta": int(beta),
                    "recommended_type": "least_damaging",
                    "band": row["band"],
                    "rank": int(row["rank"]),
                    "termination_ceiling": None if pd.isna(row["termination_ceiling"]) else int(row["termination_ceiling"]),
                    "area_improvement": float(row["area_improvement"]),
                    "runtime_improvement": float(row["runtime_improvement"]),
                }
            )

    report_path = output_dir / "threshold_band_report.md"
    report_path.write_text("\n".join(lines))
    pd.DataFrame(summary_rows).to_csv(output_dir / "threshold_band_recommendations.tsv", sep="\t", index=False)
    return report_path


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runs_df = load_rank_runs(args.runs_csv)
    rank_df = build_rank_delta_table(runs_df)
    if rank_df.empty:
        raise SystemExit("No rank-sweep data found in the provided runs CSV.")

    rank_df.to_csv(args.output_dir / "threshold_band_deltas.tsv", sep="\t", index=False)
    heatmap_path = plot_heatmaps(rank_df, args.output_dir)
    trend_path = plot_case_lines(rank_df, args.output_dir)
    report_path = write_report(rank_df, args.output_dir)

    print(f"Wrote threshold-band deltas to {args.output_dir / 'threshold_band_deltas.tsv'}")
    print(f"Wrote threshold-band heatmaps to {heatmap_path}")
    print(f"Wrote threshold-band trend plot to {trend_path}")
    print(f"Wrote threshold-band report to {report_path}")


if __name__ == "__main__":
    main()
