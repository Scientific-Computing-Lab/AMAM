#!/usr/bin/env python3
"""
Artifact-consistency verification for the AMAM-128 45-method result bundle.

Checks:
1) Expected model counts per family (10/29/6) and total 45.
2) Model-id set consistency across summary/per-image/per-subset CSVs.
3) Manifest consistency (same 45 ids + checkpoint/source fields present).
4) Script/file existence for every manifest row.
5) Completeness, protocol identity, and aggregate consistency of all five-run deep metrics.
6) Writes an auditable report with SHA256 hashes of key artifacts.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "repro/results"

CLASSICAL_SUMMARY = RESULTS / "classical/benchmark_summary.csv"
CLASSICAL_PER_IMAGE = RESULTS / "classical/benchmark_raw_per_image.csv"
CLASSICAL_PER_SUBSET = RESULTS / "classical/benchmark_per_subset.csv"

DEEP_GENERAL_SUMMARY = RESULTS / "deep_survey/deep_general_summary.csv"
DEEP_METAL_SUMMARY = RESULTS / "deep_survey/deep_metallography_summary.csv"
DEEP_PER_IMAGE = RESULTS / "deep_survey/deep_per_image.csv"
DEEP_PER_SUBSET = RESULTS / "deep_survey/deep_per_subset.csv"
DEEP_MULTISEED_RUNS = RESULTS / "deep_survey_multiseed_runs.csv"
DEEP_MULTISEED_SUMMARY = RESULTS / "deep_survey_multiseed_summary.csv"

FOUNDATION_SUMMARY = RESULTS / "foundation_edge/foundation_edge_summary.csv"
FOUNDATION_PER_IMAGE = RESULTS / "foundation_edge/foundation_edge_per_image.csv"
FOUNDATION_PER_SUBSET = RESULTS / "foundation_edge/foundation_edge_per_subset.csv"

CLASSICAL_PROTOCOL = RESULTS / "classical/benchmark_protocol.json"
DEEP_PROTOCOL = RESULTS / "deep_survey/deep_protocol.json"
FOUNDATION_PROTOCOL = RESULTS / "foundation_edge/foundation_edge_protocol.json"

MANIFEST = RESULTS / "model_provenance_manifest.csv"
DATASET_MANIFEST = REPO_ROOT / "assets/data/amam-dataset.json"
CODE_ARTIFACTS = [
    REPO_ROOT / "repro/benchmark/run_deep_survey.py",
    REPO_ROOT / "repro/benchmark/aggregate_deep_multiseed.py",
    REPO_ROOT / "repro/benchmark/plot_benchmark_gap_figure.py",
    REPO_ROOT / "repro/requirements.txt",
    REPO_ROOT / "assets/js/report.js",
]

OUT_JSON = RESULTS / "reproducibility_audit_45_models.json"
OUT_MD = RESULTS / "reproducibility_audit_45_models.md"


EXPECTED_CLASSICAL = {
    "kmeans_rgb",
    "gmm_rgb",
    "canny_watershed",
    "sobel_watershed",
    "slic_cluster",
    "felzenszwalb_cluster",
    "lbp_kmeans",
    "gabor_kmeans",
    "rf_pixel",
    "svm_pixel",
}

EXPECTED_FOUNDATION = {
    "sam_vit_base",
    "slimsam_50",
    "slimsam_77",
    "texturesam_03",
    "hed_watershed",
    "pidi_watershed",
}

EXPECTED_DEEP = {
    "dl_unet_r34",
    "dl_unetpp_r34",
    "dl_deeplabv3_r34",
    "dl_deeplabv3p_r34",
    "dl_fpn_r34",
    "dl_pspnet_r34",
    "dl_linknet_r34",
    "dl_manet_r34",
    "dl_segformer_b0",
    "dl_upernet_b0",
    "dl_segformer_b2",
    "dl_upernet_b2",
    "dl_unet_effb0",
    "dl_deeplabv3p_effb0",
    "metal_unet_gray_r34",
    "metal_unet_clahe_r34",
    "metal_unet_edge4_r34",
    "metal_unet_gabor_r34",
    "metal_unet_lbp_r34",
    "metal_unetpp_gray_r34",
    "metal_deeplabv3p_clahe_r34",
    "metal_fpn_gabor_r34",
    "metal_linknet_edge4_r34",
    "metal_segformer_clahe_b0",
    "metal_upernet_clahe_b2",
    "metal_segformer_gray_b2",
    "metal_manet_edge4_effb0",
    "metal_unetpp_clahe_effb0",
    "metal_mlography_unet_vgg16_gray",
}

EXPECTED_PAIRS = 128


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_files(paths: Iterable[Path]) -> None:
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise RuntimeError("Missing required files:\n- " + "\n- ".join(missing))


def unique_ids(csv_path: Path, col: str) -> Set[str]:
    df = pd.read_csv(csv_path)
    if col not in df.columns:
        raise RuntimeError(f"{csv_path} missing column `{col}`")
    return set(df[col].astype(str).tolist())


def get_git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except Exception:
        return "unknown"


def main() -> None:
    required_files = [
        CLASSICAL_SUMMARY,
        CLASSICAL_PER_IMAGE,
        CLASSICAL_PER_SUBSET,
        DEEP_GENERAL_SUMMARY,
        DEEP_METAL_SUMMARY,
        DEEP_PER_IMAGE,
        DEEP_PER_SUBSET,
        DEEP_MULTISEED_RUNS,
        DEEP_MULTISEED_SUMMARY,
        FOUNDATION_SUMMARY,
        FOUNDATION_PER_IMAGE,
        FOUNDATION_PER_SUBSET,
        CLASSICAL_PROTOCOL,
        DEEP_PROTOCOL,
        FOUNDATION_PROTOCOL,
        MANIFEST,
        DATASET_MANIFEST,
        *CODE_ARTIFACTS,
    ]
    require_files(required_files)

    c_summary = unique_ids(CLASSICAL_SUMMARY, "method")
    c_img = unique_ids(CLASSICAL_PER_IMAGE, "method")
    c_subset = unique_ids(CLASSICAL_PER_SUBSET, "method")

    d_general = unique_ids(DEEP_GENERAL_SUMMARY, "model_id")
    d_metal = unique_ids(DEEP_METAL_SUMMARY, "model_id")
    d_summary = d_general | d_metal
    d_img = unique_ids(DEEP_PER_IMAGE, "model_id")
    d_subset = unique_ids(DEEP_PER_SUBSET, "model_id")

    f_summary = unique_ids(FOUNDATION_SUMMARY, "model_id")
    f_img = unique_ids(FOUNDATION_PER_IMAGE, "model_id")
    f_subset = unique_ids(FOUNDATION_PER_SUBSET, "model_id")

    if c_summary != EXPECTED_CLASSICAL:
        raise RuntimeError(f"classical summary ids mismatch: got {len(c_summary)} expected {len(EXPECTED_CLASSICAL)}")
    if d_summary != EXPECTED_DEEP:
        raise RuntimeError(f"deep summary ids mismatch: got {len(d_summary)} expected {len(EXPECTED_DEEP)}")
    if f_summary != EXPECTED_FOUNDATION:
        raise RuntimeError(f"foundation summary ids mismatch: got {len(f_summary)} expected {len(EXPECTED_FOUNDATION)}")

    if not (c_summary == c_img == c_subset):
        raise RuntimeError("classical ids inconsistent across summary/per_image/per_subset")
    if not (d_summary == d_img == d_subset):
        raise RuntimeError("deep ids inconsistent across summary/per_image/per_subset")
    if not (f_summary == f_img == f_subset):
        raise RuntimeError("foundation ids inconsistent across summary/per_image/per_subset")

    all_ids = c_summary | d_summary | f_summary
    if len(all_ids) != 45:
        raise RuntimeError(f"expected 45 unique models, got {len(all_ids)}")

    deep_runs = pd.read_csv(DEEP_MULTISEED_RUNS)
    deep_multiseed = pd.read_csv(DEEP_MULTISEED_SUMMARY)
    required_run_cols = {"seed", "model_id", "miou", "dice", "pixel_acc", "rank"}
    if not required_run_cols.issubset(deep_runs.columns):
        raise RuntimeError(
            f"deep multi-seed runs missing columns: {sorted(required_run_cols - set(deep_runs.columns))}"
        )
    if set(deep_runs["seed"].astype(int)) != {17, 18, 19, 20, 21}:
        raise RuntimeError("deep multi-seed runs must contain seeds 17--21")
    if len(deep_runs) != 29 * 5:
        raise RuntimeError(f"expected 145 deep seed/model rows, got {len(deep_runs)}")
    per_seed_counts = deep_runs.groupby("seed")["model_id"].nunique()
    if not (per_seed_counts == 29).all():
        raise RuntimeError(f"deep per-seed model counts are incomplete: {per_seed_counts.to_dict()}")
    if set(deep_runs["model_id"].astype(str)) != EXPECTED_DEEP:
        raise RuntimeError("deep multi-seed run IDs do not match the expected deep model set")
    if set(deep_multiseed["model_id"].astype(str)) != EXPECTED_DEEP:
        raise RuntimeError("deep multi-seed summary IDs do not match the expected deep model set")
    if not (deep_multiseed["n_seeds"].astype(int) == 5).all():
        raise RuntimeError("deep multi-seed summary must report five seeds per model")

    recomputed = (
        deep_runs.groupby("model_id", as_index=False)
        .agg(
            miou_mean=("miou", "mean"),
            miou_std=("miou", "std"),
            miou_min=("miou", "min"),
            miou_max=("miou", "max"),
            dice_mean=("dice", "mean"),
            dice_std=("dice", "std"),
            dice_min=("dice", "min"),
            dice_max=("dice", "max"),
            pixel_acc_mean=("pixel_acc", "mean"),
            pixel_acc_std=("pixel_acc", "std"),
            pixel_acc_min=("pixel_acc", "min"),
            pixel_acc_max=("pixel_acc", "max"),
            n_seeds=("seed", "nunique"),
            rank_best=("rank", "min"),
            rank_worst=("rank", "max"),
        )
        .sort_values("model_id")
        .reset_index(drop=True)
    )
    published = deep_multiseed.sort_values("model_id").reset_index(drop=True)
    for metric in ("miou", "dice", "pixel_acc"):
        for statistic in ("mean", "std", "min", "max"):
            column = f"{metric}_{statistic}"
            if column not in published.columns:
                raise RuntimeError(f"deep multi-seed summary missing column `{column}`")
            difference = (recomputed[column] - published[column]).abs()
            if (difference > 1e-6).any():
                raise RuntimeError(f"deep multi-seed summary column `{column}` does not match per-seed values")
    for column in ["n_seeds", "rank_best", "rank_worst"]:
        if not (recomputed[column].astype(int) == published[column].astype(int)).all():
            raise RuntimeError(f"deep multi-seed summary column `{column}` does not match per-seed values")

    canonical_deep_protocol = json.loads(DEEP_PROTOCOL.read_text())
    protocol_identity_fields = (
        "gt_decoder_version",
        "gt_palette_sha256",
        "gt_decode_order",
        "segmentation_metric_version",
        "absent_class_policy",
        "metric_aggregation",
    )
    for seed in (17, 18, 19, 20, 21):
        protocol_path = RESULTS / f"deep_survey_seed{seed}/deep_protocol.json"
        if not protocol_path.exists():
            raise RuntimeError(f"missing deep seed-{seed} protocol: {protocol_path}")
        protocol = json.loads(protocol_path.read_text())
        if int(protocol.get("seed", -1)) != seed:
            raise RuntimeError(f"deep seed-{seed} protocol records the wrong seed")
        if protocol.get("resume_enabled") is not False:
            raise RuntimeError(f"deep seed-{seed} must be a clean non-resumed run")
        for field in protocol_identity_fields:
            if protocol.get(field) != canonical_deep_protocol.get(field):
                raise RuntimeError(f"deep seed-{seed} protocol field `{field}` differs from canonical")

    # Full-set protocol checks: each model must have 128 per-image rows.
    c_img_df = pd.read_csv(CLASSICAL_PER_IMAGE)
    d_img_df = pd.read_csv(DEEP_PER_IMAGE)
    f_img_df = pd.read_csv(FOUNDATION_PER_IMAGE)
    c_counts = c_img_df.groupby("method").size()
    d_counts = d_img_df.groupby("model_id").size()
    f_counts = f_img_df.groupby("model_id").size()
    if not (c_counts == EXPECTED_PAIRS).all():
        bad = c_counts[c_counts != EXPECTED_PAIRS].to_dict()
        raise RuntimeError(f"classical per-image row count mismatch (expected {EXPECTED_PAIRS} each): {bad}")
    if not (d_counts == EXPECTED_PAIRS).all():
        bad = d_counts[d_counts != EXPECTED_PAIRS].to_dict()
        raise RuntimeError(f"deep per-image row count mismatch (expected {EXPECTED_PAIRS} each): {bad}")
    if not (f_counts == EXPECTED_PAIRS).all():
        bad = f_counts[f_counts != EXPECTED_PAIRS].to_dict()
        raise RuntimeError(f"foundation per-image row count mismatch (expected {EXPECTED_PAIRS} each): {bad}")

    manifest = pd.read_csv(MANIFEST)
    if len(manifest) != 45:
        raise RuntimeError(f"manifest row count mismatch: {len(manifest)} != 45")
    m_ids = set(manifest["model_id"].astype(str).tolist())
    if m_ids != all_ids:
        missing = sorted(all_ids - m_ids)
        extra = sorted(m_ids - all_ids)
        raise RuntimeError(f"manifest model set mismatch. missing={missing} extra={extra}")

    required_cols = [
        "model_group",
        "model_id",
        "display_name",
        "checkpoint_kind",
        "checkpoint_identifier",
        "checkpoint_loader",
        "checkpoint_source_location",
        "checkpoint_source_url",
        "repro_script",
        "result_source_csv",
    ]
    for col in required_cols:
        if col not in manifest.columns:
            raise RuntimeError(f"manifest missing column `{col}`")
        if manifest[col].astype(str).str.len().min() == 0:
            raise RuntimeError(f"manifest column `{col}` has empty values")

    for row in manifest.itertuples(index=False):
        script_path = REPO_ROOT / str(row.repro_script)
        result_csv_path = REPO_ROOT / str(row.result_source_csv)
        if not script_path.exists():
            raise RuntimeError(f"missing repro script referenced by manifest: {script_path}")
        if not result_csv_path.exists():
            raise RuntimeError(f"missing result csv referenced by manifest: {result_csv_path}")

    c_protocol = json.loads(CLASSICAL_PROTOCOL.read_text())
    d_protocol = json.loads(DEEP_PROTOCOL.read_text())
    f_protocol = json.loads(FOUNDATION_PROTOCOL.read_text())

    if int(c_protocol.get("n_pairs", -1)) != EXPECTED_PAIRS:
        raise RuntimeError(f"classical protocol n_pairs != {EXPECTED_PAIRS}")
    if int(d_protocol.get("n_pairs", -1)) != EXPECTED_PAIRS:
        raise RuntimeError(f"deep protocol n_pairs != {EXPECTED_PAIRS}")
    if int(f_protocol.get("n_pairs", -1)) != EXPECTED_PAIRS:
        raise RuntimeError(f"foundation protocol n_pairs != {EXPECTED_PAIRS}")
    if c_protocol.get("split_mode") != "fullset_no_holdout":
        raise RuntimeError("classical protocol split_mode is not fullset_no_holdout")
    if d_protocol.get("split_mode") != "fullset_no_holdout":
        raise RuntimeError("deep protocol split_mode is not fullset_no_holdout")
    if f_protocol.get("split_mode") != "fullset_no_holdout":
        raise RuntimeError("foundation protocol split_mode is not fullset_no_holdout")

    audit = {
        "status": "PASS",
        "git_commit": get_git_commit(),
        "counts": {
            "classical": len(c_summary),
            "deep_general": len(d_general),
            "deep_metallography": len(d_metal),
            "foundation_edge": len(f_summary),
            "total_unique_models": len(all_ids),
        },
        "consistency": {
            "classical_consistent": c_summary == c_img == c_subset,
            "deep_consistent": d_summary == d_img == d_subset,
            "foundation_consistent": f_summary == f_img == f_subset,
            "manifest_matches_results": m_ids == all_ids,
            "deep_multiseed_complete": len(deep_runs) == 29 * 5,
            "deep_multiseed_summary_matches_runs": True,
        },
        "artifact_sha256": {str(p.relative_to(REPO_ROOT)): sha256(p) for p in required_files + [MANIFEST]},
    }

    OUT_JSON.write_text(json.dumps(audit, indent=2))

    md_lines: List[str] = [
        "# AMAM-128 Artifact Consistency Audit (45 Methods)",
        "",
        f"- Status: **{audit['status']}**",
        f"- Git commit: `{audit['git_commit']}`",
        "- Model counts:",
        f"  - Classical: {audit['counts']['classical']}",
        f"  - Deep general: {audit['counts']['deep_general']}",
        f"  - Deep metallography: {audit['counts']['deep_metallography']}",
        f"  - Foundation/edge: {audit['counts']['foundation_edge']}",
        f"  - Total: {audit['counts']['total_unique_models']}",
        "",
        "## Consistency Checks",
        f"- Classical summary/per-image/per-subset IDs match: `{audit['consistency']['classical_consistent']}`",
        f"- Deep summary/per-image/per-subset IDs match: `{audit['consistency']['deep_consistent']}`",
        f"- Foundation summary/per-image/per-subset IDs match: `{audit['consistency']['foundation_consistent']}`",
        f"- Provenance manifest matches results IDs: `{audit['consistency']['manifest_matches_results']}`",
        f"- Deep five-run values are complete (29 x 5): `{audit['consistency']['deep_multiseed_complete']}`",
        f"- Deep aggregate matches the per-seed values: `{audit['consistency']['deep_multiseed_summary_matches_runs']}`",
        "",
        "## Key Artifacts (SHA256)",
    ]
    for rel, h in audit["artifact_sha256"].items():
        md_lines.append(f"- `{rel}`: `{h}`")

    OUT_MD.write_text("\n".join(md_lines) + "\n")

    print("[PASS] 45-method artifact consistency audit")
    print(" -", OUT_JSON)
    print(" -", OUT_MD)


if __name__ == "__main__":
    main()
