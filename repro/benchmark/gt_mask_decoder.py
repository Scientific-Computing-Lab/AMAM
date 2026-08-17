from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image

DECODER_VERSION = "gt-source-rgb-v1"
DECODE_ORDER = "source_rgb_to_labels_then_nearest_resize"
DEFAULT_PALETTE_PATH = Path(__file__).with_name("gt_mask_palettes.json")


@lru_cache(maxsize=None)
def _load_palette_artifact_cached(path: str) -> dict:
    artifact = json.loads(Path(path).read_text())
    if artifact.get("decoder_version") != DECODER_VERSION:
        raise ValueError(f"unsupported GT decoder version: {artifact.get('decoder_version')!r}")
    if not isinstance(artifact.get("subsets"), dict):
        raise ValueError("GT palette artifact has no subsets mapping")
    return artifact


def load_palette_artifact(palette_path: Path = DEFAULT_PALETTE_PATH) -> dict:
    return _load_palette_artifact_cached(str(Path(palette_path).resolve()))


def get_subset_prototypes(
    subset_id: str,
    expected_phase_count: int,
    palette_path: Path = DEFAULT_PALETTE_PATH,
) -> np.ndarray:
    artifact = load_palette_artifact(palette_path)
    if subset_id not in artifact["subsets"]:
        raise KeyError(f"no frozen GT palette for subset {subset_id!r}")
    entry = artifact["subsets"][subset_id]
    prototypes = np.asarray(entry.get("prototypes_rgb"), dtype=np.float32)
    if entry.get("phase_count") != expected_phase_count or prototypes.shape != (expected_phase_count, 3):
        raise ValueError(f"GT palette phase-count mismatch for {subset_id}")
    if not np.isfinite(prototypes).all() or np.any((prototypes < 0) | (prototypes > 255)):
        raise ValueError(f"invalid GT RGB prototypes for {subset_id}")
    return prototypes.copy()


def decode_ground_truth(
    mask_path: Path,
    subset_id: str,
    output_size: tuple[int, int],
    expected_phase_count: int,
    palette_path: Path = DEFAULT_PALETTE_PATH,
) -> np.ndarray:
    prototypes = get_subset_prototypes(subset_id, expected_phase_count, palette_path)
    with Image.open(mask_path) as image:
        source_rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    flat = source_rgb.reshape(-1, 3)
    squared_distances = np.sum((flat[:, None, :] - prototypes[None, :, :]) ** 2, axis=2)
    source_labels = np.argmin(squared_distances, axis=1).reshape(source_rgb.shape[:2]).astype(np.uint8)
    resized = Image.fromarray(source_labels, mode="L").resize(output_size, Image.Resampling.NEAREST)
    labels = np.asarray(resized, dtype=np.int64)
    if labels.size == 0 or labels.min() < 0 or labels.max() >= expected_phase_count:
        raise ValueError(f"decoded GT labels out of range for {subset_id}")
    return labels


def ground_truth_protocol_metadata(palette_path: Path = DEFAULT_PALETTE_PATH) -> dict[str, str]:
    artifact_path = Path(palette_path).resolve()
    artifact = load_palette_artifact(artifact_path)
    return {
        "gt_decoder_version": artifact["decoder_version"],
        "gt_palette_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        "gt_decode_order": DECODE_ORDER,
    }
