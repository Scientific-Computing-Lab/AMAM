#!/usr/bin/env python3
"""Report whether a deep seed bundle is safe to reuse in a release run."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from benchmark_contract import (
    CANONICAL_DEEP_PREDICTION_MODELS,
    EXPECTED_DEEP_MODEL_IDS,
    EXPECTED_DEEP_MODEL_ORDER,
    EXPECTED_PAIRS,
)
from canonical_predictions import load_canonical_manifest
from gt_mask_decoder import ground_truth_protocol_metadata
from promote_deep_seed import DEEP_DETAIL_FILES
from segmentation_metrics import segmentation_metric_protocol_metadata


EXPECTED_DEEP = EXPECTED_DEEP_MODEL_IDS
EXPECTED_PROTOCOL = {
    **ground_truth_protocol_metadata(),
    **segmentation_metric_protocol_metadata(),
}
EXPECTED_GENERAL = frozenset(
    model_id for model_id in EXPECTED_DEEP if model_id.startswith("dl_")
)
EXPECTED_METALLOGRAPHY = EXPECTED_DEEP - EXPECTED_GENERAL
SUMMARY_COLUMNS = {
    "model_id",
    "display_name",
    "group",
    "category",
    "architecture",
    "encoder",
    "input_mode",
    "miou",
    "dice",
    "pixel_acc",
    "params_m",
    "train_seconds",
    "train_minutes",
}
PER_SUBSET_COLUMNS = {
    "model_id",
    "display_name",
    "group",
    "category",
    "architecture",
    "encoder",
    "input_mode",
    "subset",
    "miou",
    "dice",
    "pixel_acc",
}
EXPECTED_EXECUTION = {
    "epochs": 5,
    "batch_size": 4,
    "lr": 0.001,
    "weight_decay": 0.0001,
    "split_mode": "fullset_no_holdout",
    "n_pairs": EXPECTED_PAIRS,
    "train_images": EXPECTED_PAIRS,
    "test_images": EXPECTED_PAIRS,
    "num_global_classes": 13,
}
EXPECTED_SUBSETS = 6


def _csv_rows(
    path: Path,
    errors: list[str],
    required_columns: set[str] | frozenset[str] = frozenset({"model_id"}),
) -> list[dict[str, str]]:
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            missing = sorted(set(required_columns) - set(reader.fieldnames or []))
            if missing:
                errors.append(f"{path.name} is missing columns: {', '.join(missing)}")
                return []
            return [dict(row) for row in reader]
    except (OSError, csv.Error) as exc:
        errors.append(f"invalid {path.name}: {exc}")
        return []


def _validate_model_rows(
    path: Path,
    expected_models: frozenset[str],
    expected_rows_per_model: int,
    required_columns: set[str] | frozenset[str],
    errors: list[str],
) -> list[dict[str, str]]:
    rows = _csv_rows(path, errors, required_columns)
    counts = Counter(str(row["model_id"]) for row in rows)
    if set(counts) != expected_models or any(
        counts[model_id] != expected_rows_per_model for model_id in expected_models
    ):
        errors.append(
            f"{path.name} does not contain exactly {expected_rows_per_model} "
            f"row(s) for each expected model"
        )
    return rows


def validate_seed(
    seed_dir: Path,
    seed: int,
    expected_img_size: int,
    require_canonical_manifest: bool,
) -> list[str]:
    errors: list[str] = []
    per_image_path = seed_dir / "deep_per_image.csv"
    meta_path = seed_dir / "deep_model_meta.json"
    protocol_path = seed_dir / "deep_protocol.json"
    for filename in DEEP_DETAIL_FILES:
        path = seed_dir / filename
        if not path.is_file():
            errors.append(f"missing {path.name}")
    if errors:
        return errors

    try:
        protocol = json.loads(protocol_path.read_text())
        metadata = json.loads(meta_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid JSON metadata: {exc}"]

    if not isinstance(protocol, dict) or not isinstance(metadata, dict):
        return ["deep protocol and model metadata must be JSON objects"]

    if protocol.get("seed") != seed:
        errors.append(f"protocol seed is {protocol.get('seed')!r}, expected {seed}")
    if protocol.get("resume_enabled") is not False:
        errors.append("protocol is resumed rather than clean")
    expected_execution = {"img_size": expected_img_size, **EXPECTED_EXECUTION}
    for field, expected in expected_execution.items():
        if protocol.get(field) != expected:
            errors.append(f"protocol {field} is {protocol.get(field)!r}, expected {expected!r}")
    for field, expected in EXPECTED_PROTOCOL.items():
        if protocol.get(field) != expected:
            errors.append(f"protocol {field} is not {expected}")
    for field in ("models", "selected_models"):
        model_ids = protocol.get(field)
        if not isinstance(model_ids, list) or tuple(map(str, model_ids)) != EXPECTED_DEEP_MODEL_ORDER:
            errors.append(f"protocol {field} is not the canonical 29-model order")
    completed_models = protocol.get("completed_models")
    if not isinstance(completed_models, list) or set(map(str, completed_models)) != EXPECTED_DEEP:
        errors.append("protocol completed_models does not contain the 29 expected models")
    if set(metadata) != EXPECTED_DEEP:
        errors.append("deep_model_meta.json does not contain the 29 expected models")

    counts: Counter[str] = Counter()
    counts.update(str(row["model_id"]) for row in _csv_rows(per_image_path, errors))

    if set(counts) != EXPECTED_DEEP:
        errors.append("deep_per_image.csv does not contain the 29 expected models")
    bad_counts = {model_id: count for model_id, count in counts.items() if count != EXPECTED_PAIRS}
    if bad_counts:
        errors.append("deep_per_image.csv does not contain 128 rows per model")

    _validate_model_rows(
        seed_dir / "deep_macro_over_subsets.csv",
        EXPECTED_DEEP,
        1,
        SUMMARY_COLUMNS,
        errors,
    )
    _validate_model_rows(
        seed_dir / "deep_general_summary.csv",
        EXPECTED_GENERAL,
        1,
        SUMMARY_COLUMNS,
        errors,
    )
    _validate_model_rows(
        seed_dir / "deep_metallography_summary.csv",
        EXPECTED_METALLOGRAPHY,
        1,
        SUMMARY_COLUMNS,
        errors,
    )
    subset_rows = _validate_model_rows(
        seed_dir / "deep_per_subset.csv",
        EXPECTED_DEEP,
        EXPECTED_SUBSETS,
        PER_SUBSET_COLUMNS,
        errors,
    )
    subset_ids: dict[str, set[str]] = {model_id: set() for model_id in EXPECTED_DEEP}
    for row in subset_rows:
        model_id = str(row["model_id"])
        if model_id in subset_ids:
            subset_ids[model_id].add(str(row["subset"]))
    if any(len(values) != EXPECTED_SUBSETS for values in subset_ids.values()):
        errors.append("deep_per_subset.csv does not contain six unique subsets per model")

    if require_canonical_manifest:
        if protocol.get("canonical_prediction_export_enabled") is not True:
            errors.append("protocol canonical prediction export state is incompatible")
        canonical_models = protocol.get("canonical_prediction_models")
        if not isinstance(canonical_models, list) or set(map(str, canonical_models)) != set(
            CANONICAL_DEEP_PREDICTION_MODELS
        ):
            errors.append("protocol canonical prediction model set is incompatible")
        try:
            load_canonical_manifest(
                root=seed_dir / "canonical_predictions",
                expected_track="deep",
                expected_seed=seed,
                expected_models=CANONICAL_DEEP_PREDICTION_MODELS,
                expected_protocol=EXPECTED_PROTOCOL,
                expected_count=EXPECTED_PAIRS * len(CANONICAL_DEEP_PREDICTION_MODELS),
                expected_image_size=(expected_img_size, expected_img_size),
                expected_split_mode="fullset_no_holdout",
            )
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"invalid canonical predictions: {exc}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--expected-img-size", type=int, required=True)
    parser.add_argument("--require-canonical-manifest", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = validate_seed(
        args.seed_dir,
        args.seed,
        args.expected_img_size,
        args.require_canonical_manifest,
    )
    if errors:
        print(f"[resume] seed {args.seed} not reusable: {'; '.join(errors)}")
        return 1
    print(f"[resume] seed {args.seed} reusable: complete clean 29-model sweep")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
