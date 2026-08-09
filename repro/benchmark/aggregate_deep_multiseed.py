#!/usr/bin/env python3
"""Aggregate isolated deep-survey runs into auditable multi-seed artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "repro/results"
DEFAULT_RUNS_OUTPUT = RESULTS / "deep_survey_multiseed_runs.csv"
DEFAULT_SUMMARY_OUTPUT = RESULTS / "deep_survey_multiseed_summary.csv"
EXPECTED_MODELS = 29


def parse_seeds(value: str) -> list[int]:
    seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    if len(seeds) != len(set(seeds)):
        raise argparse.ArgumentTypeError("Seeds must be unique.")
    return seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--seeds",
        type=parse_seeds,
        default=parse_seeds("17,18,19,20,21"),
        help="Comma-separated seeds (default: 17,18,19,20,21).",
    )
    parser.add_argument(
        "--runs-output",
        type=Path,
        default=DEFAULT_RUNS_OUTPUT,
        help="Output CSV containing one row per seed and model.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=DEFAULT_SUMMARY_OUTPUT,
        help="Output CSV containing per-model mIoU summary statistics.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def load_runs(seeds: list[int]) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    expected_ids: set[str] | None = None
    required = {
        "model_id",
        "display_name",
        "group",
        "category",
        "miou",
        "dice",
        "pixel_acc",
    }

    for seed in seeds:
        path = RESULTS / f"deep_survey_seed{seed}" / "deep_macro_over_subsets.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing seed {seed} summary: {path}")
        frame = pd.read_csv(path)
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{path} is missing columns: {missing}")
        if len(frame) != EXPECTED_MODELS or frame["model_id"].nunique() != EXPECTED_MODELS:
            raise ValueError(f"{path} must contain {EXPECTED_MODELS} unique models")

        model_ids = set(frame["model_id"].astype(str))
        if expected_ids is None:
            expected_ids = model_ids
        elif model_ids != expected_ids:
            raise ValueError(f"Seed {seed} model IDs do not match the other runs")

        frame = frame.copy()
        frame.insert(0, "seed", seed)
        frame["rank"] = frame["miou"].rank(method="min", ascending=False).astype(int)
        frames.append(
            frame[
                [
                    "seed",
                    "model_id",
                    "display_name",
                    "group",
                    "category",
                    "miou",
                    "dice",
                    "pixel_acc",
                    "rank",
                ]
            ]
        )

    return pd.concat(frames, ignore_index=True).sort_values(
        ["seed", "rank", "model_id"]
    )


def aggregate(runs: pd.DataFrame, n_seeds: int) -> pd.DataFrame:
    summary = (
        runs.groupby("model_id", as_index=False)
        .agg(
            miou_mean=("miou", "mean"),
            miou_std=("miou", "std"),
            miou_min=("miou", "min"),
            miou_max=("miou", "max"),
            n_seeds=("seed", "nunique"),
            rank_best=("rank", "min"),
            rank_worst=("rank", "max"),
        )
        .sort_values(["miou_mean", "model_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if not (summary["n_seeds"] == n_seeds).all():
        raise ValueError("At least one model is missing a seed result")
    for column in ["miou_mean", "miou_std", "miou_min", "miou_max"]:
        summary[column] = summary[column].round(6)
    return summary


def main() -> None:
    args = parse_args()
    runs = load_runs(args.seeds)
    summary = aggregate(runs, len(args.seeds))

    args.runs_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    runs.to_csv(args.runs_output, index=False)
    summary.to_csv(
        args.summary_output,
        index=False,
        float_format="%.6f",
        lineterminator="\r\n",
    )

    ranked = summary.sort_values("miou_mean", ascending=False)
    adjacent_gaps = ranked["miou_mean"].diff().abs().dropna()
    median_std = float(summary["miou_std"].median())
    median_gap = float(adjacent_gaps.median())

    print(f"[saved] {display_path(args.runs_output)}")
    print(f"[saved] {display_path(args.summary_output)}")
    print(f"[summary] models={len(summary)} seeds={len(args.seeds)}")
    print(f"[summary] median model SD={median_std:.6f}")
    print(f"[summary] median adjacent mean gap={median_gap:.6f}")


if __name__ == "__main__":
    main()
