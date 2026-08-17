#!/usr/bin/env python3
"""Lossless, auditable prediction artifacts for canonical benchmark runs."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
from PIL import Image


SCHEMA_VERSION = "canonical-predictions-v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_component(value: str, field: str) -> str:
    value = str(value)
    if not value or Path(value).name != value or value in {".", ".."}:
        raise ValueError(f"Invalid {field}: {value!r}")
    return value


def _prediction_key(model_id: str, subset_id: str, image_name: str) -> tuple[str, str, str]:
    return (str(model_id), str(subset_id), str(image_name))


class CanonicalPredictionWriter:
    """Write exact metric-input label maps and an atomic manifest."""

    def __init__(
        self,
        root: Path,
        track: str,
        seed: int,
        image_size: tuple[int, int] | list[int],
        split_mode: str,
        protocol_metadata: Mapping[str, object],
        model_ids: Iterable[str],
    ) -> None:
        self.root = Path(root)
        self.track = _safe_component(track, "track")
        self.seed = int(seed)
        self.image_size = [int(v) for v in image_size]
        if len(self.image_size) != 2 or min(self.image_size) <= 0:
            raise ValueError("image_size must contain two positive dimensions")
        self.split_mode = str(split_mode)
        self.protocol_metadata = dict(protocol_metadata)
        self.model_ids = {_safe_component(value, "model_id") for value in model_ids}
        if not self.model_ids:
            raise ValueError("At least one canonical prediction model is required")
        self._entries: list[dict[str, object]] = []
        self._keys: set[tuple[str, str, str]] = set()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        model_id: str,
        subset_id: str,
        image_name: str,
        labels: np.ndarray,
    ) -> Path:
        model_id = _safe_component(model_id, "model_id")
        subset_id = _safe_component(subset_id, "subset_id")
        image_name = _safe_component(image_name, "image_name")
        if model_id not in self.model_ids:
            raise ValueError(f"Model {model_id!r} is not configured for canonical prediction export")

        key = _prediction_key(model_id, subset_id, image_name)
        if key in self._keys:
            raise ValueError(f"Duplicate canonical prediction: {key}")

        array = np.asarray(labels)
        if array.ndim != 2:
            raise ValueError("Canonical prediction labels must be two-dimensional")
        if array.size and (int(array.min()) < 0 or int(array.max()) > 255):
            raise ValueError("Canonical prediction labels must fit in uint8")
        array_u8 = array.astype(np.uint8, copy=False)

        relative = Path(model_id) / subset_id / f"{Path(image_name).stem}.png"
        output_path = self.root / relative
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(array_u8, mode="L").save(output_path, format="PNG")

        self._keys.add(key)
        self._entries.append(
            {
                "model_id": model_id,
                "subset_id": subset_id,
                "image_name": image_name,
                "path": relative.as_posix(),
                "shape": [int(array.shape[0]), int(array.shape[1])],
                "sha256": sha256_file(output_path),
            }
        )
        return output_path

    def finalize(self) -> dict[str, object]:
        manifest: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "track": self.track,
            "seed": self.seed,
            "image_size": self.image_size,
            "split_mode": self.split_mode,
            "protocol_metadata": self.protocol_metadata,
            "model_ids": sorted(self.model_ids),
            "file_count": len(self._entries),
            "files": sorted(
                self._entries,
                key=lambda entry: (
                    str(entry["model_id"]),
                    str(entry["subset_id"]),
                    str(entry["image_name"]),
                ),
            ),
        }
        temporary_path = self.root / "manifest.json.tmp"
        manifest_path = self.root / "manifest.json"
        temporary_path.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary_path.replace(manifest_path)
        return manifest


def load_canonical_manifest(
    root: Path,
    expected_track: str,
    expected_seed: int,
    expected_models: Iterable[str],
    expected_protocol: Mapping[str, object],
    expected_count: int,
    expected_image_size: tuple[int, int] | list[int] | None = None,
    expected_split_mode: str | None = None,
) -> dict[str, object]:
    root = Path(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing canonical prediction manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())

    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Canonical prediction manifest schema version mismatch")
    if manifest.get("track") != expected_track:
        raise ValueError("Canonical prediction manifest track mismatch")
    if int(manifest.get("seed", -1)) != int(expected_seed):
        raise ValueError("Canonical prediction manifest seed mismatch")
    expected_model_ids = {str(value) for value in expected_models}
    if set(manifest.get("model_ids", [])) != expected_model_ids:
        raise ValueError("Canonical prediction manifest model set mismatch")
    if manifest.get("protocol_metadata") != dict(expected_protocol):
        raise ValueError("Canonical prediction manifest protocol metadata mismatch")
    if expected_image_size is not None and manifest.get("image_size") != [
        int(value) for value in expected_image_size
    ]:
        raise ValueError("Canonical prediction manifest image size mismatch")
    if expected_split_mode is not None and manifest.get("split_mode") != expected_split_mode:
        raise ValueError("Canonical prediction manifest split mode mismatch")

    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("Canonical prediction manifest files must be a list")
    if int(manifest.get("file_count", -1)) != len(entries) or len(entries) != int(expected_count):
        raise ValueError(
            f"Canonical prediction manifest file count mismatch: got {len(entries)}, expected {expected_count}"
        )

    keys: set[tuple[str, str, str]] = set()
    paths: set[str] = set()
    model_counts: Counter[str] = Counter()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Canonical prediction manifest file entry must be an object")
        key = _prediction_key(
            str(entry.get("model_id", "")),
            str(entry.get("subset_id", "")),
            str(entry.get("image_name", "")),
        )
        if key in keys:
            raise ValueError(f"Canonical prediction manifest contains duplicate key: {key}")
        keys.add(key)
        if key[0] not in expected_model_ids:
            raise ValueError(
                f"Canonical prediction manifest contains unexpected model: {key[0]!r}"
            )
        model_counts[key[0]] += 1
        relative = str(entry.get("path", ""))
        if not relative or relative in paths:
            raise ValueError(f"Canonical prediction manifest contains duplicate or empty path: {relative!r}")
        paths.add(relative)
        prediction_path = root / relative
        if not prediction_path.is_file():
            raise FileNotFoundError(f"Missing canonical prediction: {prediction_path}")
        if sha256_file(prediction_path) != entry.get("sha256"):
            raise ValueError(f"Canonical prediction SHA-256 mismatch: {prediction_path}")

    if expected_model_ids:
        expected_per_model, remainder = divmod(int(expected_count), len(expected_model_ids))
        if remainder or any(
            model_counts[model_id] != expected_per_model for model_id in expected_model_ids
        ):
            raise ValueError("Canonical prediction manifest per-model file count mismatch")

    return manifest


def load_canonical_prediction(
    root: Path,
    manifest: Mapping[str, object],
    model_id: str,
    subset_id: str,
    image_name: str,
    expected_classes: int,
) -> np.ndarray:
    root = Path(root)
    key = _prediction_key(model_id, subset_id, image_name)
    entries = manifest.get("files", [])
    matching = [
        entry
        for entry in entries
        if _prediction_key(entry["model_id"], entry["subset_id"], entry["image_name"]) == key
    ]
    if len(matching) != 1:
        raise KeyError(f"Expected exactly one canonical prediction for {key}, found {len(matching)}")

    entry = matching[0]
    prediction_path = root / str(entry["path"])
    if sha256_file(prediction_path) != entry.get("sha256"):
        raise ValueError(f"Canonical prediction SHA-256 mismatch: {prediction_path}")
    labels = np.asarray(Image.open(prediction_path).convert("L"), dtype=np.uint8)
    if list(labels.shape) != list(entry.get("shape", [])):
        raise ValueError(f"Canonical prediction shape mismatch: {prediction_path}")
    if labels.size and int(labels.max()) >= int(expected_classes):
        raise ValueError(
            f"Canonical prediction contains class {int(labels.max())}, expected < {expected_classes}: {prediction_path}"
        )
    return labels
