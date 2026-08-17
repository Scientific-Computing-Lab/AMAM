from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Sequence

import numpy as np
import sklearn
from PIL import Image
from sklearn.cluster import KMeans

REPO_ROOT = Path(__file__).resolve().parents[2]

DECODER_VERSION = "gt-source-rgb-v1"
CALIBRATION = {
    "color_space": "RGB",
    "source_resolution": True,
    "interpolation_before_calibration": False,
    "estimator": "sklearn.cluster.KMeans",
    "init": "k-means++",
    "n_init": 20,
    "max_iter": 300,
    "tol": 1e-4,
    "random_state": 0,
    "algorithm": "lloyd",
}


def source_mask_digest(mask_paths: Sequence[Path], repo_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(mask_paths, key=lambda item: item.relative_to(repo_root).as_posix()):
        relative = path.relative_to(repo_root).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def calibrate_prototypes(mask_paths: Sequence[Path], phase_count: int) -> list[list[float]]:
    histogram: Counter[tuple[int, int, int]] = Counter()
    for mask_path in mask_paths:
        with Image.open(mask_path) as image:
            rgb = image.convert("RGB")
            colors = rgb.getcolors(maxcolors=rgb.width * rgb.height)
        if colors is None:
            raise ValueError(f"could not enumerate RGB colors in {mask_path}")
        histogram.update({color: count for count, color in colors})
    colors = np.asarray(sorted(histogram), dtype=np.float64)
    weights = np.asarray([histogram[tuple(color)] for color in colors.astype(np.uint8)], dtype=np.float64)
    model = KMeans(
        n_clusters=phase_count,
        init="k-means++",
        n_init=20,
        max_iter=300,
        tol=1e-4,
        random_state=0,
        algorithm="lloyd",
    )
    model.fit(colors, sample_weight=weights)
    centers = sorted(model.cluster_centers_.tolist(), key=lambda row: tuple(row))
    return [[round(float(value), 8) for value in row] for row in centers]


def subset_sources(dataset_json: Path, repo_root: Path) -> dict[str, tuple[list[str], list[Path]]]:
    dataset = json.loads(dataset_json.read_text())
    sources = {}
    for subset in sorted(dataset["subsets"], key=lambda row: row["id"]):
        phase_names = list(subset.get("phases", []))
        if len(phase_names) < 2:
            continue
        mask_paths = sorted(
            (repo_root / mask["path"] for mask in subset.get("gallery", {}).get("masks", [])),
            key=lambda path: path.relative_to(repo_root).as_posix(),
        )
        if not mask_paths or any(not path.is_file() for path in mask_paths):
            raise ValueError(f"missing source masks for {subset['id']}")
        sources[subset["id"]] = (phase_names, mask_paths)
    return sources


def build_artifact(dataset_json: Path, repo_root: Path) -> dict:
    subsets = {}
    for subset_id, (phase_names, mask_paths) in subset_sources(dataset_json, repo_root).items():
        subsets[subset_id] = {
            "phase_count": len(phase_names),
            "phase_names": phase_names,
            "source_mask_sha256": source_mask_digest(mask_paths, repo_root),
            "prototypes_rgb": calibrate_prototypes(mask_paths, len(phase_names)),
        }
    return {
        "decoder_version": DECODER_VERSION,
        "calibration": {**CALIBRATION, "sklearn_version": sklearn.__version__},
        "subsets": subsets,
    }


def check_artifact(artifact_path: Path, dataset_json: Path, repo_root: Path) -> None:
    artifact = json.loads(artifact_path.read_text())
    expected = subset_sources(dataset_json, repo_root)
    if artifact.get("decoder_version") != DECODER_VERSION:
        raise ValueError("decoder version mismatch")
    if set(artifact.get("subsets", {})) != set(expected):
        raise ValueError("eligible subset coverage mismatch")
    for subset_id, (phase_names, mask_paths) in expected.items():
        entry = artifact["subsets"][subset_id]
        if entry.get("phase_count") != len(phase_names):
            raise ValueError(f"phase count mismatch for {subset_id}")
        if entry.get("phase_names") != phase_names:
            raise ValueError(f"phase names mismatch for {subset_id}")
        if len(entry.get("prototypes_rgb", [])) != len(phase_names):
            raise ValueError(f"prototype count mismatch for {subset_id}")
        if entry.get("source_mask_sha256") != source_mask_digest(mask_paths, repo_root):
            raise ValueError(f"source mask digest mismatch for {subset_id}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-json", type=Path, default=REPO_ROOT / "assets/data/amam-dataset.json")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("gt_mask_palettes.json"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if args.check:
        check_artifact(args.output, args.dataset_json, args.repo_root)
    else:
        artifact = build_artifact(args.dataset_json, args.repo_root)
        args.output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
