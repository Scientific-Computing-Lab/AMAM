from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = REPO_ROOT / "repro/benchmark"
sys.path.insert(0, str(BENCHMARK_DIR))

from canonical_predictions import CanonicalPredictionWriter


STATUS_SCRIPT = REPO_ROOT / "repro/benchmark/deep_seed_status.py"
EXPECTED_DEEP = [
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
]
CANONICAL_MODELS = {"dl_unet_effb0", "metal_unetpp_clahe_effb0"}
SUMMARY_FIELDS = [
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
]
PER_SUBSET_FIELDS = [
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
]
PROTOCOL_METADATA = {
    "gt_decoder_version": "gt-source-rgb-v1",
    "gt_palette_sha256": "bd9e45cc659f06fa5cf0a45004592c7c8b67691d2880f35d39a2e88ca5b56e6f",
    "gt_decode_order": "source_rgb_to_labels_then_nearest_resize",
    "segmentation_metric_version": "present-classes-per-image-v1",
    "absent_class_policy": "exclude_if_absent_in_gt_and_prediction",
    "metric_aggregation": "per_image_present_class_macro_then_subset_macro",
}


def write_model_csv(
    path: Path,
    model_ids: list[str],
    *,
    fieldnames: list[str] = SUMMARY_FIELDS,
    rows_per_model: int = 1,
) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for model_id in model_ids:
            for row_index in range(rows_per_model):
                row = {field: 0 for field in fieldnames}
                row["model_id"] = model_id
                if "subset" in row:
                    row["subset"] = f"subset-{row_index}"
                writer.writerow(row)


def write_seed_fixture(
    seed_dir: Path,
    *,
    seed: int,
    model_ids: list[str] | None = None,
    rows_per_model: int = 128,
    resume_enabled: bool = False,
    canonical_manifest: bool = False,
    img_size: int = 192,
    gt_decoder_version: str = "gt-source-rgb-v1",
    gt_palette_sha256: str = "bd9e45cc659f06fa5cf0a45004592c7c8b67691d2880f35d39a2e88ca5b56e6f",
) -> None:
    selected = list(EXPECTED_DEEP if model_ids is None else model_ids)
    seed_dir.mkdir(parents=True, exist_ok=True)
    with (seed_dir / "deep_per_image.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model_id", "image"])
        writer.writeheader()
        for model_id in selected:
            for image_index in range(rows_per_model):
                writer.writerow({"model_id": model_id, "image": f"image-{image_index}.jpg"})
    (seed_dir / "deep_model_meta.json").write_text(
        json.dumps({model_id: {"model_id": model_id} for model_id in selected})
    )
    write_model_csv(seed_dir / "deep_macro_over_subsets.csv", selected)
    write_model_csv(
        seed_dir / "deep_per_subset.csv",
        selected,
        fieldnames=PER_SUBSET_FIELDS,
        rows_per_model=6,
    )
    write_model_csv(seed_dir / "deep_general_summary.csv", selected[:14])
    write_model_csv(seed_dir / "deep_metallography_summary.csv", selected[14:])
    (seed_dir / "deep_general_table.md").write_text("fixture\n")
    (seed_dir / "deep_metallography_table.md").write_text("fixture\n")
    (seed_dir / "deep_protocol.json").write_text(
        json.dumps(
            {
                "seed": seed,
                "img_size": img_size,
                "epochs": 5,
                "batch_size": 4,
                "lr": 0.001,
                "weight_decay": 0.0001,
                "split_mode": "fullset_no_holdout",
                "n_pairs": 128,
                "train_images": 128,
                "test_images": 128,
                "num_global_classes": 13,
                "models": EXPECTED_DEEP,
                "selected_models": EXPECTED_DEEP,
                "completed_models": selected,
                "resume_enabled": resume_enabled,
                "canonical_prediction_export_enabled": canonical_manifest,
                "canonical_prediction_models": (
                    sorted(CANONICAL_MODELS) if canonical_manifest else []
                ),
                "gt_decoder_version": gt_decoder_version,
                "gt_palette_sha256": gt_palette_sha256,
                "gt_decode_order": "source_rgb_to_labels_then_nearest_resize",
                "segmentation_metric_version": "present-classes-per-image-v1",
                "absent_class_policy": "exclude_if_absent_in_gt_and_prediction",
                "metric_aggregation": "per_image_present_class_macro_then_subset_macro",
            }
        )
    )
    if canonical_manifest:
        canonical = seed_dir / "canonical_predictions"
        writer = CanonicalPredictionWriter(
            root=canonical,
            track="deep",
            seed=seed,
            image_size=(img_size, img_size),
            split_mode="fullset_no_holdout",
            protocol_metadata={
                **PROTOCOL_METADATA,
                "gt_decoder_version": gt_decoder_version,
                "gt_palette_sha256": gt_palette_sha256,
            },
            model_ids=CANONICAL_MODELS,
        )
        labels = np.zeros((1, 1), dtype=np.uint8)
        for model_id in sorted(CANONICAL_MODELS):
            for image_index in range(128):
                writer.save(
                    model_id,
                    "subset-a",
                    f"image-{image_index}.jpg",
                    labels,
                )
        writer.finalize()


class DeepSeedStatusTests(unittest.TestCase):
    def run_status(self, seed_dir: Path, seed: int, require_canonical: bool = False):
        command = [
            sys.executable,
            str(STATUS_SCRIPT),
            "--seed-dir",
            str(seed_dir),
            "--seed",
            str(seed),
            "--expected-img-size",
            "192",
        ]
        if require_canonical:
            command.append("--require-canonical-manifest")
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def test_accepts_complete_clean_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "seed17"
            write_seed_fixture(seed_dir, seed=17, canonical_manifest=True)

            completed = self.run_status(seed_dir, 17, require_canonical=True)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertIn("reusable", completed.stdout)

    def test_rejects_artifacts_that_cannot_preserve_a_clean_sweep(self) -> None:
        cases = {
            "resumed": {"resume_enabled": True},
            "partial-model-set": {"model_ids": EXPECTED_DEEP[:-1]},
            "wrong-row-count": {"rows_per_model": 127},
            "wrong-protocol": {"gt_decoder_version": "old-decoder"},
            "wrong-palette": {"gt_palette_sha256": "stale-palette"},
            "wrong-run-configuration": {"img_size": 256},
        }
        for name, overrides in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                seed_dir = Path(tmp) / "seed18"
                write_seed_fixture(seed_dir, seed=18, **overrides)

                completed = self.run_status(seed_dir, 18)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("not reusable", completed.stdout)

    def test_rejects_wrong_seed_and_missing_seed17_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wrong_seed = Path(tmp) / "wrong-seed"
            write_seed_fixture(wrong_seed, seed=18)
            wrong = self.run_status(wrong_seed, 17)
            self.assertNotEqual(wrong.returncode, 0)

            missing_manifest = Path(tmp) / "missing-manifest"
            write_seed_fixture(missing_manifest, seed=17)
            missing = self.run_status(missing_manifest, 17, require_canonical=True)
            self.assertNotEqual(missing.returncode, 0)

    def test_rejects_missing_or_model_incomplete_downstream_detail_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing_detail = Path(tmp) / "missing-detail"
            write_seed_fixture(missing_detail, seed=18)
            (missing_detail / "deep_macro_over_subsets.csv").unlink()

            missing = self.run_status(missing_detail, 18)

            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("not reusable", missing.stdout)

            incomplete_detail = Path(tmp) / "incomplete-detail"
            write_seed_fixture(incomplete_detail, seed=18)
            write_model_csv(
                incomplete_detail / "deep_per_subset.csv",
                EXPECTED_DEEP[:-1],
                fieldnames=PER_SUBSET_FIELDS,
                rows_per_model=6,
            )

            incomplete = self.run_status(incomplete_detail, 18)

            self.assertNotEqual(incomplete.returncode, 0)
            self.assertIn("not reusable", incomplete.stdout)

    def test_rejects_duplicate_or_malformed_summary_rows(self) -> None:
        cases = {
            "duplicate-macro": (
                "deep_macro_over_subsets.csv",
                EXPECTED_DEEP + [EXPECTED_DEEP[0]],
                SUMMARY_FIELDS,
                1,
            ),
            "wrong-general-model": (
                "deep_general_summary.csv",
                EXPECTED_DEEP[:13] + [EXPECTED_DEEP[14]],
                SUMMARY_FIELDS,
                1,
            ),
            "wrong-subset-row-count": (
                "deep_per_subset.csv",
                EXPECTED_DEEP,
                PER_SUBSET_FIELDS,
                5,
            ),
        }
        for name, (filename, model_ids, fieldnames, rows_per_model) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                seed_dir = Path(tmp) / name
                write_seed_fixture(seed_dir, seed=18)
                write_model_csv(
                    seed_dir / filename,
                    model_ids,
                    fieldnames=fieldnames,
                    rows_per_model=rows_per_model,
                )

                completed = self.run_status(seed_dir, 18)

                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("not reusable", completed.stdout)

    def test_rejects_noncanonical_model_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "wrong-model-order"
            write_seed_fixture(seed_dir, seed=18)
            protocol_path = seed_dir / "deep_protocol.json"
            protocol = json.loads(protocol_path.read_text())
            protocol["models"] = list(reversed(EXPECTED_DEEP))
            protocol["selected_models"] = list(reversed(EXPECTED_DEEP))
            protocol_path.write_text(json.dumps(protocol))

            completed = self.run_status(seed_dir, 18)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("not reusable", completed.stdout)

    def test_rejects_invalid_or_hash_mismatched_seed17_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            invalid_manifest = Path(tmp) / "invalid-manifest"
            write_seed_fixture(invalid_manifest, seed=17, canonical_manifest=True)
            (invalid_manifest / "canonical_predictions/manifest.json").write_text("{}")

            invalid = self.run_status(invalid_manifest, 17, require_canonical=True)

            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("not reusable", invalid.stdout)

            mismatched_hash = Path(tmp) / "mismatched-hash"
            write_seed_fixture(mismatched_hash, seed=17, canonical_manifest=True)
            prediction = next(
                (mismatched_hash / "canonical_predictions").glob("*/*/*.png")
            )
            prediction.write_bytes(b"tampered")

            mismatched = self.run_status(mismatched_hash, 17, require_canonical=True)

            self.assertNotEqual(mismatched.returncode, 0)
            self.assertIn("not reusable", mismatched.stdout)

            wrong_distribution = Path(tmp) / "wrong-distribution"
            write_seed_fixture(wrong_distribution, seed=17, canonical_manifest=True)
            manifest_path = wrong_distribution / "canonical_predictions/manifest.json"
            manifest = json.loads(manifest_path.read_text())
            first_model, second_model = sorted(CANONICAL_MODELS)
            entry = next(item for item in manifest["files"] if item["model_id"] == first_model)
            entry["model_id"] = second_model
            entry["subset_id"] = "shifted-subset"
            manifest_path.write_text(json.dumps(manifest))

            distribution = self.run_status(wrong_distribution, 17, require_canonical=True)

            self.assertNotEqual(distribution.returncode, 0)
            self.assertIn("not reusable", distribution.stdout)

            wrong_canvas = Path(tmp) / "wrong-canvas"
            write_seed_fixture(wrong_canvas, seed=17, canonical_manifest=True)
            canvas_manifest_path = wrong_canvas / "canonical_predictions/manifest.json"
            canvas_manifest = json.loads(canvas_manifest_path.read_text())
            canvas_manifest["image_size"] = [256, 256]
            canvas_manifest_path.write_text(json.dumps(canvas_manifest))

            canvas = self.run_status(wrong_canvas, 17, require_canonical=True)

            self.assertNotEqual(canvas.returncode, 0)
            self.assertIn("not reusable", canvas.stdout)

    def test_rejects_non_object_protocol_metadata_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            seed_dir = Path(tmp) / "malformed-metadata"
            write_seed_fixture(seed_dir, seed=18)
            (seed_dir / "deep_protocol.json").write_text("[]")

            completed = self.run_status(seed_dir, 18)

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("not reusable", completed.stdout)
            self.assertNotIn("Traceback", completed.stderr)

            malformed_field = Path(tmp) / "malformed-field"
            write_seed_fixture(malformed_field, seed=18)
            protocol_path = malformed_field / "deep_protocol.json"
            protocol = json.loads(protocol_path.read_text())
            protocol["models"] = 17
            protocol_path.write_text(json.dumps(protocol))

            field_result = self.run_status(malformed_field, 18)

            self.assertNotEqual(field_result.returncode, 0)
            self.assertIn("not reusable", field_result.stdout)
            self.assertNotIn("Traceback", field_result.stderr)


if __name__ == "__main__":
    unittest.main()
