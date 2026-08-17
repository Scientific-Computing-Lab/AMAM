from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from promote_deep_seed import promote_seed_run


DETAIL_FILES = (
    "deep_general_summary.csv",
    "deep_general_table.md",
    "deep_macro_over_subsets.csv",
    "deep_metallography_summary.csv",
    "deep_metallography_table.md",
    "deep_model_meta.json",
    "deep_per_image.csv",
    "deep_per_subset.csv",
    "deep_protocol.json",
)


def write_seed_bundle(directory: Path, *, seed: int = 17, model_count: int = 29) -> None:
    directory.mkdir(parents=True)
    for filename in DETAIL_FILES:
        (directory / filename).write_text(f"fixture for {filename}\n", encoding="utf-8")

    (directory / "deep_protocol.json").write_text(
        json.dumps({"seed": seed, "models": [f"model-{i}" for i in range(model_count)]}),
        encoding="utf-8",
    )
    macro_rows = ["model_id,miou,dice,pixel_acc"]
    macro_rows.extend(f"model-{i},0.1,0.2,0.3" for i in range(model_count))
    (directory / "deep_macro_over_subsets.csv").write_text(
        "\n".join(macro_rows) + "\n",
        encoding="utf-8",
    )


class PromoteDeepSeedTests(unittest.TestCase):
    def test_copies_only_the_nine_deep_detail_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "deep_survey_seed17"
            target = root / "deep_survey"
            write_seed_bundle(source)
            canonical = source / "canonical_predictions"
            canonical.mkdir()
            (canonical / "manifest.json").write_text("{}", encoding="utf-8")

            promote_seed_run(source, target)

            self.assertEqual(sorted(path.name for path in target.iterdir()), sorted(DETAIL_FILES))
            for filename in DETAIL_FILES:
                self.assertEqual((target / filename).read_bytes(), (source / filename).read_bytes())
            self.assertFalse((target / "canonical_predictions").exists())

    def test_rejects_a_missing_detail_file_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "deep_survey_seed17"
            target = root / "deep_survey"
            write_seed_bundle(source)
            (source / "deep_per_image.csv").unlink()

            with self.assertRaises(FileNotFoundError):
                promote_seed_run(source, target)

            self.assertFalse(target.exists())

    def test_rejects_the_wrong_protocol_seed_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "deep_survey_seed18"
            target = root / "deep_survey"
            write_seed_bundle(source, seed=18)

            with self.assertRaisesRegex(ValueError, "seed"):
                promote_seed_run(source, target)

            self.assertFalse(target.exists())

    def test_rejects_an_incomplete_model_set_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "deep_survey_seed17"
            target = root / "deep_survey"
            write_seed_bundle(source, model_count=28)

            with self.assertRaisesRegex(ValueError, "29"):
                promote_seed_run(source, target)

            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
