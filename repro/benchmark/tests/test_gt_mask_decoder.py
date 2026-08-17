from __future__ import annotations

import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BENCHMARK_DIR))

from gt_mask_decoder import (
    decode_ground_truth,
    get_subset_prototypes,
    ground_truth_protocol_metadata,
    load_palette_artifact,
)


class GroundTruthDecoderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.mask_path = self.root / "mask.png"
        Image.new("RGB", (2, 2), (0, 0, 255)).save(self.mask_path)
        self.palette_path = self.root / "palettes.json"
        self.palette_path.write_text(
            json.dumps(
                {
                    "decoder_version": "gt-source-rgb-v1",
                    "subsets": {
                        "toy": {
                            "phase_count": 2,
                            "phase_names": ["blue", "red"],
                            "source_mask_sha256": "0" * 64,
                            "prototypes_rgb": [
                                [0.0, 0.0, 255.0],
                                [255.0, 0.0, 0.0],
                            ],
                        }
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_decodes_before_nearest_resize(self) -> None:
        source = np.asarray(
            [
                [[0, 0, 255], [255, 0, 0]],
                [[255, 0, 0], [0, 0, 255]],
            ],
            dtype=np.uint8,
        )
        Image.fromarray(source).save(self.mask_path)
        decoded = decode_ground_truth(
            self.mask_path,
            subset_id="toy",
            output_size=(4, 4),
            expected_phase_count=2,
            palette_path=self.palette_path,
        )
        expected = np.repeat(np.repeat(np.asarray([[0, 1], [1, 0]]), 2, axis=0), 2, axis=1)
        np.testing.assert_array_equal(decoded, expected)
        self.assertEqual(decoded.dtype, np.int64)

    def test_decoding_is_independent_of_random_seeds(self) -> None:
        random.seed(1)
        np.random.seed(1)
        first = decode_ground_truth(
            self.mask_path,
            "toy",
            (4, 4),
            2,
            self.palette_path,
        )
        random.seed(999)
        np.random.seed(999)
        second = decode_ground_truth(
            self.mask_path,
            "toy",
            (4, 4),
            2,
            self.palette_path,
        )
        np.testing.assert_array_equal(first, second)

    def test_rejects_phase_count_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "phase-count mismatch for toy"):
            decode_ground_truth(self.mask_path, "toy", (4, 4), 3, self.palette_path)

    def test_reports_ground_truth_protocol_metadata(self) -> None:
        metadata = ground_truth_protocol_metadata(self.palette_path)
        self.assertEqual(metadata["gt_decoder_version"], "gt-source-rgb-v1")
        self.assertEqual(len(metadata["gt_palette_sha256"]), 64)
        self.assertEqual(metadata["gt_decode_order"], "source_rgb_to_labels_then_nearest_resize")

    def test_checked_in_palettes_cover_and_decode_all_eligible_subsets(self) -> None:
        dataset = json.loads((REPO_ROOT / "assets/data/amam-dataset.json").read_text())
        eligible = [subset for subset in dataset["subsets"] if len(subset["phases"]) >= 2]

        artifact = load_palette_artifact()
        self.assertEqual(set(artifact["subsets"]), {subset["id"] for subset in eligible})
        for subset in eligible:
            phase_count = len(subset["phases"])
            prototypes = get_subset_prototypes(subset["id"], phase_count)
            self.assertEqual(prototypes.shape, (phase_count, 3))
            mask_path = REPO_ROOT / subset["gallery"]["masks"][0]["path"]
            decoded = decode_ground_truth(mask_path, subset["id"], (17, 13), phase_count)
            self.assertEqual(decoded.shape, (13, 17))
            self.assertEqual(decoded.dtype, np.int64)
            self.assertGreaterEqual(int(decoded.min()), 0)
            self.assertLess(int(decoded.max()), phase_count)


if __name__ == "__main__":
    unittest.main()
