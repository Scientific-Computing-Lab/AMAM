from __future__ import annotations

import ast
import unittest
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parents[1]


class GroundTruthConsumerTests(unittest.TestCase):
    def test_consumers_use_shared_decoder_without_runtime_gt_clustering(self) -> None:
        minimum_decode_calls = {
            "run_benchmark.py": 2,
            "run_deep_survey.py": 1,
            "run_foundation_edge_addons.py": 1,
            "build_appendix_representative_assets.py": 1,
        }
        forbidden_definitions = {"estimate_mask_centroids", "mask_to_labels", "mask_to_local_labels"}

        for filename, minimum_calls in minimum_decode_calls.items():
            source = (BENCHMARK_DIR / filename).read_text()
            tree = ast.parse(source, filename=filename)
            definitions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
            calls = [
                node
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "decode_ground_truth"
            ]
            self.assertTrue(forbidden_definitions.isdisjoint(definitions), filename)
            self.assertGreaterEqual(len(calls), minimum_calls, filename)

    def test_runners_record_decoder_protocol_metadata(self) -> None:
        for filename in ("run_benchmark.py", "run_deep_survey.py", "run_foundation_edge_addons.py"):
            source = (BENCHMARK_DIR / filename).read_text()
            self.assertIn("ground_truth_protocol_metadata()", source, filename)


if __name__ == "__main__":
    unittest.main()
