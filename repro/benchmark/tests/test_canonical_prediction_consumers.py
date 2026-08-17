from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from canonical_predictions import CanonicalPredictionWriter, load_canonical_prediction
from run_deep_survey import SampleRecord, eval_model
from verify_45_model_repro import require_representative_predictions


class _FeatureCache:
    def get(self, input_mode: str, index: int) -> np.ndarray:
        del input_mode, index
        return np.zeros((2, 2, 3), dtype=np.float32)


class _FixedPredictionModel(torch.nn.Module):
    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        del inputs
        return torch.tensor(
            [[[[5.0, 0.0], [0.0, 5.0]], [[0.0, 5.0], [5.0, 0.0]]]],
            dtype=torch.float32,
        )


class CanonicalPredictionConsumerTests(unittest.TestCase):
    def test_audit_rejects_missing_representative_prediction(self) -> None:
        manifest = {
            "files": [
                {
                    "model_id": "model-a",
                    "subset_id": "subset-a",
                    "image_name": "present.jpg",
                }
            ]
        }

        with self.assertRaisesRegex(RuntimeError, "missing representative"):
            require_representative_predictions(
                manifest=manifest,
                model_ids={"model-a"},
                representative_images={("subset-a", "present.jpg"), ("subset-b", "missing.jpg")},
                track="deep",
            )

    def test_panel_resize_uses_nearest_neighbor_for_discrete_labels(self) -> None:
        from build_appendix_representative_assets import resize_labels_nearest

        labels = np.array([[0, 1], [2, 3]], dtype=np.uint8)
        resized = resize_labels_nearest(labels, (4, 4))

        self.assertEqual(
            resized.tolist(),
            [
                [0, 0, 1, 1],
                [0, 0, 1, 1],
                [2, 2, 3, 3],
                [2, 2, 3, 3],
            ],
        )

    def test_runner_help_exposes_prediction_export_options(self) -> None:
        for script in ("run_benchmark.py", "run_deep_survey.py"):
            result = subprocess.run(
                [sys.executable, str(BENCHMARK_DIR / script), "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--save-canonical-predictions", result.stdout, script)
            self.assertIn("--prediction-models", result.stdout, script)

    def test_deep_evaluation_exports_the_exact_metric_prediction(self) -> None:
        expected = np.array([[0, 1], [1, 0]], dtype=np.uint8)
        record = SampleRecord(
            subset_id="subset-a",
            subset_name="Subset A",
            family="test",
            image_name="sample.jpg",
            original_path=Path("sample.jpg"),
            image_rgb=np.zeros((2, 2, 3), dtype=np.uint8),
            gt_local=expected.astype(np.int64),
            gt_global=expected.astype(np.int64),
            subset_global_ids=[0, 1],
            phase_count=2,
            split="train_test",
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            writer = CanonicalPredictionWriter(
                root=root,
                track="deep",
                seed=17,
                image_size=(2, 2),
                split_mode="fullset_no_holdout",
                protocol_metadata={"protocol": "test"},
                model_ids={"model-a"},
            )
            rows = eval_model(
                model=_FixedPredictionModel(),
                records=[record],
                test_indices=[0],
                feature_cache=_FeatureCache(),
                input_mode="rgb",
                device=torch.device("cpu"),
                prediction_writer=writer,
                prediction_model_id="model-a",
            )
            manifest = writer.finalize()
            saved = load_canonical_prediction(
                root, manifest, "model-a", "subset-a", "sample.jpg", expected_classes=2
            )

        np.testing.assert_array_equal(saved, expected)
        self.assertEqual(rows[0]["miou"], 1.0)
        self.assertEqual(rows[0]["dice"], 1.0)
        self.assertEqual(rows[0]["pixel_acc"], 1.0)

    def test_appendix_builder_has_no_retraining_or_gt_based_prediction_remapping(self) -> None:
        source = (BENCHMARK_DIR / "build_appendix_representative_assets.py").read_text()
        tree = ast.parse(source)
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        imported_roots = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        self.assertNotIn("torch", imported_roots)
        self.assertTrue(
            {
                "train_best_classical_rf",
                "train_best_deep_models",
                "train_deep_model_return_model",
                "map_hungarian",
            }.isdisjoint(function_names)
        )
        self.assertNotIn("linear_sum_assignment", source)
        self.assertNotIn("hu_map", source)


if __name__ == "__main__":
    unittest.main()
