#!/usr/bin/env python3
"""Rebuild assets/data/amam-dataset.json from the files in data/local.

The manifest mixes two kinds of content:

* file inventory (paths, names, ids, counts) -- regenerated here from disk
* editorial metadata (material, condition, phases, prose) -- preserved verbatim
  from the existing manifest, because it is not derivable from filenames

Image/mask pairing is derived from matching filename stems, e.g.
``images/4130 x 20 (17).jpg`` <-> ``labels/4130 x 20 (17).png``. The previous
manifest relied on opaque Google Drive ``maskId`` links instead, which silently
paired a 20x image with a 10x mask; stem matching makes that class of error
impossible and auditable.

Ids are deterministic (derived from the repo-relative path) so reruns produce
byte-identical output and ``maskId`` links stay stable across regenerations.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data" / "local"
DATA_JSON = REPO_ROOT / "assets" / "data" / "amam-dataset.json"

IMAGE_DIR = "images"
LABEL_DIR = "labels"

# Editorial fields carried over untouched from the existing manifest.
SUBSET_EDITORIAL = (
    "id",
    "material",
    "family",
    "condition",
    "magnification",
    "description",
    "annotationNotes",
    "phases",
    "localOnly",
)
TOP_EDITORIAL = (
    "name",
    "shortName",
    "version",
    "overview",
    "excludedSubsets",
    "materialFamilies",
    "method",
    "localDataNote",
    "downloadAllRepoZip",
)


def stable_id(rel_path: str) -> str:
    """Deterministic opaque id for a file, stable across reruns."""
    return hashlib.sha1(f"amam:{rel_path}".encode("utf-8")).hexdigest()[:24]


def natural_key(name: str) -> Tuple:
    """Sort 'x 10 (2)' before 'x 10 (10)' and group series together."""
    parts = re.split(r"(\d+)", name)
    return tuple(int(p) if p.isdigit() else p.lower() for p in parts)


def asset_entry(rel_path: str) -> Dict[str, str]:
    """One gallery record. All four URL fields are the same local path."""
    name = Path(rel_path).name
    return {
        "id": stable_id(rel_path),
        "name": name,
        "path": rel_path,
        "thumbnailUrl": rel_path,
        "viewUrl": rel_path,
        "downloadUrl": rel_path,
    }


def scan_category(category: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    """Return (originals, masks, warnings) for one category directory."""
    cat_dir = DATA_ROOT / category
    img_dir, lbl_dir = cat_dir / IMAGE_DIR, cat_dir / LABEL_DIR
    warnings: List[str] = []

    images = {p.stem: p for p in img_dir.iterdir() if p.is_file()} if img_dir.is_dir() else {}
    labels = {p.stem: p for p in lbl_dir.iterdir() if p.is_file()} if lbl_dir.is_dir() else {}

    for stem in sorted(set(images) - set(labels), key=natural_key):
        warnings.append(f"{category}: image with no matching label -> {images[stem].name}")
    for stem in sorted(set(labels) - set(images), key=natural_key):
        warnings.append(f"{category}: label with no matching image -> {labels[stem].name}")

    masks: List[Dict] = []
    originals: List[Dict] = []
    for stem in sorted(images, key=natural_key):
        img_rel = images[stem].relative_to(REPO_ROOT).as_posix()
        original = asset_entry(img_rel)

        label = labels.get(stem)
        if label is not None:
            mask = asset_entry(label.relative_to(REPO_ROOT).as_posix())
            masks.append(mask)
            original["maskId"] = mask["id"]
            original["maskName"] = mask["name"]
        originals.append(original)

    return originals, masks, warnings


def build() -> int:
    if not DATA_JSON.is_file():
        sys.exit(f"missing manifest to inherit editorial fields from: {DATA_JSON}")
    if not DATA_ROOT.is_dir():
        sys.exit(f"missing dataset directory: {DATA_ROOT}")

    previous = json.loads(DATA_JSON.read_text())
    prev_subsets = {s["id"]: s for s in previous.get("subsets", [])}
    on_disk = sorted(p.name for p in DATA_ROOT.iterdir() if p.is_dir())

    all_warnings: List[str] = []
    for missing in sorted(set(prev_subsets) - set(on_disk)):
        all_warnings.append(f"subset in manifest but not on disk, dropped -> {missing}")
    for extra in sorted(set(on_disk) - set(prev_subsets)):
        all_warnings.append(f"subset on disk with no editorial metadata -> {extra}")

    subsets: List[Dict] = []
    total_originals = total_masks = total_pairs = 0

    for category in on_disk:
        originals, masks, warnings = scan_category(category)
        all_warnings.extend(warnings)
        if not originals:
            all_warnings.append(f"{category}: no images found, skipped")
            continue

        pair_count = sum(1 for o in originals if o.get("maskId"))
        prev = prev_subsets.get(category, {})

        subset: Dict = {key: prev[key] for key in SUBSET_EDITORIAL if key in prev}
        subset.setdefault("id", category)
        subset["images"] = len(originals)
        subset["download"] = {
            "categoryPath": f"data/local/{category}",
            "imagesPath": f"data/local/{category}/{IMAGE_DIR}",
            "labelsPath": f"data/local/{category}/{LABEL_DIR}",
        }
        subset["gallery"] = {
            "originals": originals,
            "masks": masks,
            "pairCount": pair_count,
            "originalCount": len(originals),
            "maskCount": len(masks),
            "hasMaskPairs": pair_count > 0,
            "notes": prev.get("gallery", {}).get("notes", ""),
        }
        subsets.append(subset)

        total_originals += len(originals)
        total_masks += len(masks)
        total_pairs += pair_count

    manifest: Dict = {key: previous[key] for key in TOP_EDITORIAL if key in previous}
    manifest["totalImages"] = total_originals
    manifest["includedSubsets"] = len(subsets)
    manifest["gallerySummary"] = {
        "totalOriginals": total_originals,
        "totalMasks": total_masks,
        "totalPairs": total_pairs,
    }
    manifest["subsets"] = subsets

    DATA_JSON.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    print(f"[written] {DATA_JSON.relative_to(REPO_ROOT)}")
    for subset in subsets:
        gallery = subset["gallery"]
        print(
            f"  {subset['id']:<22} originals={gallery['originalCount']:>4}"
            f"  masks={gallery['maskCount']:>4}  pairs={gallery['pairCount']:>4}"
        )
    print(f"  {'TOTAL':<22} originals={total_originals:>4}  masks={total_masks:>4}  pairs={total_pairs:>4}")

    if all_warnings:
        print(f"\n[warnings] {len(all_warnings)}")
        for warning in all_warnings:
            print(f"  - {warning}")
    else:
        print("\n[ok] every image has exactly one stem-matched mask")

    return 0 if total_pairs == total_originals == total_masks else 1


if __name__ == "__main__":
    raise SystemExit(build())
