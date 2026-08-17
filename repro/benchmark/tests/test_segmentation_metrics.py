from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from segmentation_metrics import (
    segmentation_metric_protocol_metadata,
    segmentation_metrics,
)


class SegmentationMetricTests(unittest.TestCase):
    def test_excludes_class_absent_from_both_gt_and_prediction(self) -> None:
        gt = np.asarray([[0, 0]], dtype=np.int64)
        pred = np.asarray([[0, 1]], dtype=np.int64)

        result = segmentation_metrics(pred, gt, class_count=3)

        self.assertAlmostEqual(result["miou"], 0.25)
        self.assertAlmostEqual(result["dice"], 1.0 / 3.0)
        self.assertAlmostEqual(result["pixel_acc"], 0.5)

    def test_perfect_present_class_remains_perfect(self) -> None:
        gt = np.zeros((2, 2), dtype=np.int64)
        pred = np.zeros((2, 2), dtype=np.int64)

        result = segmentation_metrics(pred, gt, class_count=2)

        self.assertEqual(result, {"miou": 1.0, "dice": 1.0, "pixel_acc": 1.0})

    def test_reports_explicit_absent_class_policy(self) -> None:
        self.assertEqual(
            segmentation_metric_protocol_metadata(),
            {
                "segmentation_metric_version": "present-classes-per-image-v1",
                "absent_class_policy": "exclude_if_absent_in_gt_and_prediction",
                "metric_aggregation": "per_image_present_class_macro_then_subset_macro",
            },
        )

    def test_rejects_labels_outside_declared_classes(self) -> None:
        gt = np.asarray([[0]], dtype=np.int64)
        pred = np.asarray([[2]], dtype=np.int64)

        with self.assertRaisesRegex(ValueError, "labels must be within class_count"):
            segmentation_metrics(pred, gt, class_count=2)

    def test_all_runners_use_shared_metrics_and_record_policy(self) -> None:
        for filename in (
            "run_benchmark.py",
            "run_deep_survey.py",
            "run_foundation_edge_addons.py",
        ):
            source = (BENCHMARK_DIR / filename).read_text()
            self.assertIn("segmentation_metrics(", source, filename)
            self.assertIn("segmentation_metric_protocol_metadata()", source, filename)
            self.assertNotIn("def metrics(", source, filename)
            self.assertNotIn("def metrics_local(", source, filename)


if __name__ == "__main__":
    unittest.main()
