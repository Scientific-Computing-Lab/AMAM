from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BENCHMARK_DIR.parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from build_gt_mask_palettes import build_artifact, check_artifact


class PaletteArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        mask_dir = self.root / "masks"
        mask_dir.mkdir()
        Image.new("RGB", (2, 2), (0, 0, 255)).save(mask_dir / "a.png")
        Image.new("RGB", (2, 2), (255, 0, 0)).save(mask_dir / "b.png")
        self.dataset_json = self.root / "dataset.json"
        self.dataset_json.write_text(
            json.dumps(
                {
                    "subsets": [
                        {
                            "id": "toy",
                            "phases": ["blue", "red"],
                            "gallery": {
                                "masks": [
                                    {"id": "b", "path": "masks/b.png"},
                                    {"id": "a", "path": "masks/a.png"},
                                ]
                            },
                        }
                    ]
                }
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_builds_sorted_fixed_prototypes_and_validates_sources(self) -> None:
        artifact = build_artifact(self.dataset_json, self.root)
        subset = artifact["subsets"]["toy"]
        self.assertEqual(subset["phase_count"], 2)
        self.assertEqual(subset["phase_names"], ["blue", "red"])
        self.assertEqual(subset["prototypes_rgb"], [[0.0, 0.0, 255.0], [255.0, 0.0, 0.0]])

        artifact_path = self.root / "palettes.json"
        artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
        check_artifact(artifact_path, self.dataset_json, self.root)

    def test_check_detects_changed_source_mask(self) -> None:
        artifact = build_artifact(self.dataset_json, self.root)
        artifact_path = self.root / "palettes.json"
        artifact_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
        Image.new("RGB", (2, 2), (0, 255, 0)).save(self.root / "masks" / "a.png")

        with self.assertRaisesRegex(ValueError, "source mask digest mismatch for toy"):
            check_artifact(artifact_path, self.dataset_json, self.root)

    def test_5884_dendritic_taxonomy_is_propagated_to_palette(self) -> None:
        expected = ["Dendritic Region", "Interdendritic Region"]
        dataset = json.loads((REPO_ROOT / "assets/data/amam-dataset.json").read_text())
        subset = next(row for row in dataset["subsets"] if row["id"] == "5884-armor-steel")
        artifact = json.loads((BENCHMARK_DIR / "gt_mask_palettes.json").read_text())

        self.assertEqual(subset["phases"], expected)
        self.assertEqual(artifact["subsets"]["5884-armor-steel"]["phase_names"], expected)


if __name__ == "__main__":
    unittest.main()
