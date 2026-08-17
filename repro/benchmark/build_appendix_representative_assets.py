#!/usr/bin/env python3
"""Build appendix panels only from validated canonical prediction artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
from PIL import Image

from canonical_predictions import (
    load_canonical_manifest,
    load_canonical_prediction,
    sha256_file,
)
from gt_mask_decoder import (
    decode_ground_truth,
    get_subset_prototypes,
    ground_truth_protocol_metadata,
)
from segmentation_metrics import segmentation_metric_protocol_metadata


REPO_ROOT = Path(__file__).resolve().parents[2]
REPRO_ROOT = REPO_ROOT / "repro"
DATA_ROOT = REPO_ROOT / "data" / "local"
DATA_JSON = REPO_ROOT / "assets" / "data" / "amam-dataset.json"
OUT_DIR = REPRO_ROOT / "figures" / "appendix_preds"
CLASSICAL_PREDICTION_ROOT = REPRO_ROOT / "results" / "classical" / "canonical_predictions"
DEEP_PREDICTION_ROOT = REPRO_ROOT / "results" / "deep_survey_seed17" / "canonical_predictions"
PANEL_SIZE = (192, 192)
CANONICAL_SEED = 17
CLASSICAL_MODEL = "rf_pixel"
GENERAL_DEEP_MODEL = "dl_unet_effb0"
METAL_DEEP_MODEL = "metal_unetpp_clahe_effb0"


@dataclass(frozen=True)
class RepSample:
    slug: str
    subset_id: str
    original: Path
    mask: Path


REP_SAMPLES: List[RepSample] = [
    RepSample(
        slug="4130-steel",
        subset_id="4130-steel",
        original=DATA_ROOT / "4130-steel" / "images" / "4130 x 10 (1).jpg",
        mask=DATA_ROOT / "4130-steel" / "labels" / "4130 x 10 (1).png",
    ),
    RepSample(
        slug="6280-cast-iron-low",
        subset_id="6280-cast-iron-low",
        original=DATA_ROOT / "6280-cast-iron-low" / "images" / "6280 x 10 (1).jpg",
        mask=DATA_ROOT / "6280-cast-iron-low" / "labels" / "6280 x 10 (1).png",
    ),
    RepSample(
        slug="6280-cast-iron-high",
        subset_id="6280-cast-iron-high",
        original=DATA_ROOT / "6280-cast-iron-high" / "images" / "6280 x 20 (1).jpg",
        mask=DATA_ROOT / "6280-cast-iron-high" / "labels" / "6280 x 20 (1).png",
    ),
    RepSample(
        slug="5884-armor-steel",
        subset_id="5884-armor-steel",
        original=DATA_ROOT / "5884-armor-steel" / "images" / "5884 x 5 (3).jpg",
        mask=DATA_ROOT / "5884-armor-steel" / "labels" / "5884 x 5 (3).png",
    ),
    RepSample(
        slug="418-17-4ph-x5",
        subset_id="418-17-4ph-x5",
        original=DATA_ROOT / "418-17-4ph-x5" / "images" / "x5 (1).jpg",
        mask=DATA_ROOT / "418-17-4ph-x5" / "labels" / "x5 (1).png",
    ),
    RepSample(
        slug="418-17-4ph-x20",
        subset_id="418-17-4ph-x20",
        original=DATA_ROOT / "418-17-4ph-x20" / "images" / "x20 (1).jpg",
        mask=DATA_ROOT / "418-17-4ph-x20" / "labels" / "x20 (1).png",
    ),
]


def phase_counts() -> Dict[str, int]:
    data = json.loads(DATA_JSON.read_text())
    return {
        subset["id"]: len(subset.get("phases", []))
        for subset in data["subsets"]
        if len(subset.get("phases", [])) >= 2
    }


def labels_to_rgb(labels: np.ndarray, prototypes: np.ndarray) -> np.ndarray:
    labels = np.asarray(labels)
    if labels.ndim != 2:
        raise ValueError("Panel labels must be two-dimensional")
    if labels.size and int(labels.max()) >= len(prototypes):
        raise ValueError("Panel labels contain an out-of-range class id")
    palette = np.clip(np.round(prototypes), 0, 255).astype(np.uint8)
    return palette[labels]


def resize_labels_nearest(labels: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Resize a discrete label map without introducing intermediate labels."""
    return np.asarray(
        Image.fromarray(np.asarray(labels, dtype=np.uint8), mode="L").resize(
            size, Image.Resampling.NEAREST
        ),
        dtype=np.uint8,
    )


def read_resized_rgb(path: Path, size: tuple[int, int]) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB").resize(size, Image.Resampling.BILINEAR))


def save_png(path: Path, array: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.asarray(array, dtype=np.uint8)).save(path, format="PNG")


def _validate_manifest_dimensions(manifest: dict, expected: list[int], track: str) -> None:
    if manifest.get("image_size") != expected:
        raise ValueError(
            f"Canonical {track} prediction image size mismatch: "
            f"got {manifest.get('image_size')}, expected {expected}"
        )
    if manifest.get("split_mode") != "fullset_no_holdout":
        raise ValueError(f"Canonical {track} prediction split mode mismatch")


def build_assets(
    classical_root: Path = CLASSICAL_PREDICTION_ROOT,
    deep_root: Path = DEEP_PREDICTION_ROOT,
    out_dir: Path = OUT_DIR,
) -> dict:
    protocol_metadata = {
        **ground_truth_protocol_metadata(),
        **segmentation_metric_protocol_metadata(),
    }
    classical_manifest = load_canonical_manifest(
        root=classical_root,
        expected_track="classical",
        expected_seed=CANONICAL_SEED,
        expected_models={CLASSICAL_MODEL},
        expected_protocol=protocol_metadata,
        expected_count=128,
    )
    deep_manifest = load_canonical_manifest(
        root=deep_root,
        expected_track="deep",
        expected_seed=CANONICAL_SEED,
        expected_models={GENERAL_DEEP_MODEL, METAL_DEEP_MODEL},
        expected_protocol=protocol_metadata,
        expected_count=256,
    )
    _validate_manifest_dimensions(classical_manifest, [256, 256], "classical")
    _validate_manifest_dimensions(deep_manifest, [192, 192], "deep")

    counts = phase_counts()
    generated: list[str] = []
    for sample in REP_SAMPLES:
        print(f"[sample] {sample.slug}")
        phase_count = counts[sample.subset_id]
        prototypes = get_subset_prototypes(sample.subset_id, phase_count)
        original = read_resized_rgb(sample.original, PANEL_SIZE)
        gt = decode_ground_truth(
            sample.mask,
            subset_id=sample.subset_id,
            output_size=PANEL_SIZE,
            expected_phase_count=phase_count,
        )
        classical = load_canonical_prediction(
            classical_root,
            classical_manifest,
            CLASSICAL_MODEL,
            sample.subset_id,
            sample.original.name,
            expected_classes=phase_count,
        )
        general = load_canonical_prediction(
            deep_root,
            deep_manifest,
            GENERAL_DEEP_MODEL,
            sample.subset_id,
            sample.original.name,
            expected_classes=phase_count,
        )
        metal = load_canonical_prediction(
            deep_root,
            deep_manifest,
            METAL_DEEP_MODEL,
            sample.subset_id,
            sample.original.name,
            expected_classes=phase_count,
        )

        if classical.shape != PANEL_SIZE:
            classical = resize_labels_nearest(classical, PANEL_SIZE)
        if general.shape != PANEL_SIZE or metal.shape != PANEL_SIZE:
            raise ValueError(f"Deep canonical panel shape mismatch for {sample.slug}")

        outputs = {
            f"{sample.slug}-viz-original.png": original,
            f"{sample.slug}-viz-mask.png": labels_to_rgb(gt, prototypes),
            f"{sample.slug}-pred-classic-rf.png": labels_to_rgb(classical, prototypes),
            f"{sample.slug}-pred-deep-unet-effb0.png": labels_to_rgb(general, prototypes),
            f"{sample.slug}-pred-metal-unetpp-clahe-effb0.png": labels_to_rgb(metal, prototypes),
        }
        for filename, array in outputs.items():
            save_png(out_dir / filename, array)
            generated.append(filename)

    metadata = {
        "schema_version": "canonical-qualitative-panels-v1",
        "deep_seed": CANONICAL_SEED,
        "classical_seed": CANONICAL_SEED,
        "panel_size": list(PANEL_SIZE),
        "models": [CLASSICAL_MODEL, GENERAL_DEEP_MODEL, METAL_DEEP_MODEL],
        "classical_display_transform": "nearest-neighbor label resize 256x256 -> 192x192",
        "deep_display_transform": "none",
        "ground_truth_display_transform": "decode source RGB then nearest-neighbor label resize",
        "classical_manifest_sha256": sha256_file(classical_root / "manifest.json"),
        "deep_manifest_sha256": sha256_file(deep_root / "manifest.json"),
        "generated_files": sorted(generated),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "panel_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"[done] wrote canonical prediction assets to {out_dir}")
    return metadata


def main() -> None:
    build_assets()


if __name__ == "__main__":
    main()
