from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from aggregate_deep_multiseed import aggregate


class DeepMultiseedAggregationTests(unittest.TestCase):
    def test_aggregates_mean_and_sample_sd_for_all_reported_metrics(self) -> None:
        runs = pd.DataFrame(
            [
                {"seed": 17, "model_id": "model-a", "miou": 0.2, "dice": 0.4, "pixel_acc": 0.6, "rank": 2},
                {"seed": 18, "model_id": "model-a", "miou": 0.4, "dice": 0.6, "pixel_acc": 0.8, "rank": 1},
                {"seed": 17, "model_id": "model-b", "miou": 0.5, "dice": 0.7, "pixel_acc": 0.9, "rank": 1},
                {"seed": 18, "model_id": "model-b", "miou": 0.3, "dice": 0.5, "pixel_acc": 0.7, "rank": 2},
            ]
        )

        summary = aggregate(runs, n_seeds=2).set_index("model_id")

        self.assertEqual(summary.loc["model-a", "miou_mean"], 0.3)
        self.assertEqual(summary.loc["model-a", "dice_mean"], 0.5)
        self.assertEqual(summary.loc["model-a", "pixel_acc_mean"], 0.7)
        self.assertAlmostEqual(summary.loc["model-a", "miou_std"], 0.141421)
        self.assertAlmostEqual(summary.loc["model-a", "dice_std"], 0.141421)
        self.assertAlmostEqual(summary.loc["model-a", "pixel_acc_std"], 0.141421)


if __name__ == "__main__":
    unittest.main()
