#!/usr/bin/env python3
"""Run and aggregate the AMAM classical benchmark across several seeds."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT = Path(__file__).with_name("run_benchmark.py")
DEFAULT_RUNS_DIR = REPO_ROOT / "repro/results/classical_multiseed_runs"
DEFAULT_OUTPUT = REPO_ROOT / "repro/results/classical_multiseed_summary.csv"
EXPECTED_METHODS = 10


def parse_seeds(value: str) -> list[int]:
    seeds = [int(item.strip()) for item in value.split(",") if item.strip()]
    if not seeds:
        raise argparse.ArgumentTypeError("At least one seed is required.")
    if len(seeds) != len(set(seeds)):
        raise argparse.ArgumentTypeError("Seeds must be unique.")
    return seeds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run clean classical benchmark repetitions and aggregate seed sensitivity."
    )
    parser.add_argument(
        "--seeds",
        type=parse_seeds,
        default=parse_seeds("17,18,19,20,21"),
        help="Comma-separated seeds (default: 17,18,19,20,21).",
    )
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIR,
        help="Parent directory for isolated per-seed outputs.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Aggregated CSV path.",
    )
    parser.add_argument(
        "--aggregate-only",
        action="store_true",
        help="Aggregate existing per-seed summaries without executing benchmarks.",
    )
    return parser.parse_args()


def run_seed(seed: int, runs_dir: Path) -> None:
    output_dir = runs_dir / f"seed_{seed}"
    command = [
        sys.executable,
        "-u",
        str(BENCHMARK_SCRIPT),
        "--seed",
        str(seed),
        "--output-dir",
        str(output_dir),
        "--no-resume",
    ]
    print(f"[seed {seed}] clean run -> {output_dir.relative_to(REPO_ROOT)}", flush=True)
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def load_runs(seeds: list[int], runs_dir: Path) -> pd.DataFrame:
    frames = []
    expected_methods: set[str] | None = None

    for seed in seeds:
        summary_path = runs_dir / f"seed_{seed}" / "benchmark_summary.csv"
        if not summary_path.exists():
            raise FileNotFoundError(f"Missing seed-{seed} summary: {summary_path}")

        frame = pd.read_csv(summary_path)
        required = {"method", "category", "miou", "dice", "pixel_acc"}
        missing = required.difference(frame.columns)
        if missing:
            raise ValueError(f"{summary_path} is missing columns: {sorted(missing)}")
        if len(frame) != EXPECTED_METHODS or frame["method"].nunique() != EXPECTED_METHODS:
            raise ValueError(
                f"{summary_path} contains {frame['method'].nunique()} unique methods; "
                f"expected {EXPECTED_METHODS}."
            )

        methods = set(frame["method"])
        if expected_methods is None:
            expected_methods = methods
        elif methods != expected_methods:
            raise ValueError(f"Method set differs for seed {seed}.")

        frame = frame.copy()
        frame["seed"] = seed
        frame["rank"] = frame["miou"].rank(method="min", ascending=False).astype(int)
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


def aggregate(all_runs: pd.DataFrame, n_seeds: int) -> pd.DataFrame:
    summary = (
        all_runs.groupby(["method", "category"], as_index=False)
        .agg(
            miou_mean=("miou", "mean"),
            miou_std=("miou", "std"),
            miou_min=("miou", "min"),
            miou_max=("miou", "max"),
            n_seeds=("seed", "nunique"),
            rank_best=("rank", "min"),
            rank_worst=("rank", "max"),
        )
        .sort_values(["miou_mean", "method"], ascending=[False, True])
        .reset_index(drop=True)
    )
    if not (summary["n_seeds"] == n_seeds).all():
        raise ValueError("At least one method is missing a seed result.")
    return summary


def main() -> None:
    args = parse_args()
    args.runs_dir.mkdir(parents=True, exist_ok=True)

    if not args.aggregate_only:
        for seed in args.seeds:
            run_seed(seed, args.runs_dir)

    all_runs = load_runs(args.seeds, args.runs_dir)
    summary = aggregate(all_runs, len(args.seeds))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output, index=False)

    print(f"[saved] {args.output.relative_to(REPO_ROOT)}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
