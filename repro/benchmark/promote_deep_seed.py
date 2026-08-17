#!/usr/bin/env python3
"""Promote validated seed-specific deep details for legacy consumers."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "repro/results/deep_survey_seed17"
DEFAULT_TARGET = REPO_ROOT / "repro/results/deep_survey"
EXPECTED_MODEL_COUNT = 29

DEEP_DETAIL_FILES = (
    "deep_general_summary.csv",
    "deep_general_table.md",
    "deep_macro_over_subsets.csv",
    "deep_metallography_summary.csv",
    "deep_metallography_table.md",
    "deep_model_meta.json",
    "deep_per_image.csv",
    "deep_per_subset.csv",
    "deep_protocol.json",
)


def _validate_source(source: Path, expected_seed: int) -> None:
    missing = [filename for filename in DEEP_DETAIL_FILES if not (source / filename).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required deep detail files: {', '.join(missing)}")

    protocol = json.loads((source / "deep_protocol.json").read_text(encoding="utf-8"))
    actual_seed = protocol.get("seed")
    if actual_seed != expected_seed:
        raise ValueError(f"Expected protocol seed {expected_seed}, found {actual_seed!r}")

    with (source / "deep_macro_over_subsets.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    model_ids = [row.get("model_id", "") for row in rows]
    if len(rows) != EXPECTED_MODEL_COUNT or len(set(model_ids)) != EXPECTED_MODEL_COUNT or "" in model_ids:
        raise ValueError(
            f"Expected {EXPECTED_MODEL_COUNT} rows with unique model_id values, "
            f"found {len(rows)} rows and {len(set(model_ids))} unique IDs"
        )


def promote_seed_run(source: Path, target: Path, expected_seed: int = 17) -> None:
    """Validate a completed seed run and atomically promote its detail files."""
    source = Path(source)
    target = Path(target)
    _validate_source(source, expected_seed)
    target.mkdir(parents=True, exist_ok=True)

    for filename in DEEP_DETAIL_FILES:
        destination = target / filename
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{filename}.", suffix=".tmp", dir=target
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            shutil.copy2(source / filename, temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--expected-seed", type=int, default=17)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    promote_seed_run(args.source, args.target, args.expected_seed)
    print(f"[promoted] {args.source} -> {args.target}")


if __name__ == "__main__":
    main()
