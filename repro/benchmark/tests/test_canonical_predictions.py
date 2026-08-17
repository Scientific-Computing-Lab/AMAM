from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from canonical_predictions import (
    CanonicalPredictionWriter,
    load_canonical_manifest,
    load_canonical_prediction,
)


PROTOCOL = {
    "gt_decoder_version": "fixed-subset-palettes-v1",
    "segmentation_metric_version": "present-classes-per-image-v1",
}


class CanonicalPredictionArtifactTests(unittest.TestCase):
    def make_writer(self, root: Path) -> CanonicalPredictionWriter:
        return CanonicalPredictionWriter(
            root=root,
            track="deep",
            seed=17,
            image_size=(2, 2),
            split_mode="fullset_no_holdout",
            protocol_metadata=PROTOCOL,
            model_ids={"model-a"},
        )

    def test_round_trip_preserves_labels_and_records_stable_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            labels = np.array([[0, 1], [2, 1]], dtype=np.int64)
            writer = self.make_writer(root)
            writer.save("model-a", "subset-a", "sample.jpg", labels)
            written = writer.finalize()

            manifest = load_canonical_manifest(
                root=root,
                expected_track="deep",
                expected_seed=17,
                expected_models={"model-a"},
                expected_protocol=PROTOCOL,
                expected_count=1,
            )
            loaded = load_canonical_prediction(
                root=root,
                manifest=manifest,
                model_id="model-a",
                subset_id="subset-a",
                image_name="sample.jpg",
                expected_classes=3,
            )

            np.testing.assert_array_equal(loaded, labels)
            self.assertEqual(written, manifest)
            self.assertEqual(manifest["schema_version"], "canonical-predictions-v1")
            self.assertEqual(manifest["model_ids"], ["model-a"])
            self.assertEqual(manifest["files"][0]["shape"], [2, 2])
            self.assertEqual(len(manifest["files"][0]["sha256"]), 64)
            self.assertFalse((root / "manifest.json.tmp").exists())

    def test_duplicate_prediction_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writer = self.make_writer(Path(tmp))
            labels = np.zeros((2, 2), dtype=np.uint8)
            writer.save("model-a", "subset-a", "sample.jpg", labels)

            with self.assertRaisesRegex(ValueError, "Duplicate canonical prediction"):
                writer.save("model-a", "subset-a", "sample.jpg", labels)

    def test_invalid_label_array_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writer = self.make_writer(Path(tmp))

            with self.assertRaisesRegex(ValueError, "two-dimensional"):
                writer.save("model-a", "subset-a", "sample.jpg", np.zeros((2, 2, 1)))
            with self.assertRaisesRegex(ValueError, "uint8"):
                writer.save("model-a", "subset-a", "negative.jpg", np.array([[-1]]))
            with self.assertRaisesRegex(ValueError, "uint8"):
                writer.save("model-a", "subset-a", "large.jpg", np.array([[256]]))

    def test_unknown_model_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writer = self.make_writer(Path(tmp))

            with self.assertRaisesRegex(ValueError, "not configured"):
                writer.save("model-b", "subset-a", "sample.jpg", np.zeros((2, 2)))

    def test_manifest_protocol_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = self.make_writer(root)
            writer.save("model-a", "subset-a", "sample.jpg", np.zeros((2, 2)))
            writer.finalize()

            with self.assertRaisesRegex(ValueError, "protocol metadata"):
                load_canonical_manifest(
                    root=root,
                    expected_track="deep",
                    expected_seed=17,
                    expected_models={"model-a"},
                    expected_protocol={**PROTOCOL, "gt_decoder_version": "wrong"},
                    expected_count=1,
                )

    def test_tampered_png_is_rejected_by_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = self.make_writer(root)
            writer.save("model-a", "subset-a", "sample.jpg", np.zeros((2, 2)))
            manifest = writer.finalize()
            prediction_path = root / manifest["files"][0]["path"]
            prediction_path.write_bytes(b"tampered")

            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_canonical_prediction(
                    root=root,
                    manifest=manifest,
                    model_id="model-a",
                    subset_id="subset-a",
                    image_name="sample.jpg",
                    expected_classes=3,
                )

    def test_manifest_file_count_and_duplicate_entries_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = self.make_writer(root)
            writer.save("model-a", "subset-a", "sample.jpg", np.zeros((2, 2)))
            manifest = writer.finalize()

            with self.assertRaisesRegex(ValueError, "file count"):
                load_canonical_manifest(
                    root, "deep", 17, {"model-a"}, PROTOCOL, expected_count=2
                )

            manifest["files"].append(dict(manifest["files"][0]))
            manifest["file_count"] = 2
            (root / "manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_canonical_manifest(
                    root, "deep", 17, {"model-a"}, PROTOCOL, expected_count=2
                )


if __name__ == "__main__":
    unittest.main()
