from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_deep_seed_status import write_seed_fixture


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "repro/benchmark/run_all_repro.sh"


class RunAllReproTests(unittest.TestCase):
    def test_dry_run_prints_five_seed_pipeline_without_executing_python(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp)
            execution_marker = temporary / "python-was-executed"
            fake_python = temporary / "fake-python"
            fake_python.write_text(
                "#!/usr/bin/env bash\n"
                f"touch {execution_marker}\n"
                "printf '[fake-python]'\n"
                "printf ' %s' \"$@\"\n"
                "printf '\\n'\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHON_BIN": str(fake_python),
                    "RUN_LOG": str(temporary / "run.log"),
                    "REPRO_DRY_RUN": "1",
                    "SKIP_FOUNDATION": "1",
                    "DEVICE": "cuda:0",
                }
            )
            completed = subprocess.run(
                ["bash", str(RUNNER)],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertFalse(execution_marker.exists(), "dry-run executed a Python stage")

            deep_commands = [
                line.replace("\\,", ",")
                for line in completed.stdout.splitlines()
                if "run_deep_survey.py" in line
            ]
            self.assertEqual(len(deep_commands), 5, completed.stdout)
            for seed, command in zip((17, 18, 19, 20, 21), deep_commands):
                self.assertIn(f"--seed {seed}", command)
                self.assertIn(f"--out-dir repro/results/deep_survey_seed{seed}", command)
                self.assertIn("--no-resume", command)

            self.assertIn("--save-canonical-predictions", deep_commands[0])
            self.assertIn(
                "--prediction-models dl_unet_effb0,metal_unetpp_clahe_effb0",
                deep_commands[0],
            )
            for command in deep_commands[1:]:
                self.assertNotIn("--save-canonical-predictions", command)
                self.assertNotIn("--prediction-models", command)

            stdout = completed.stdout
            self.assertLess(
                stdout.index("aggregate_deep_multiseed.py"),
                stdout.index("promote_deep_seed.py"),
            )
            self.assertLess(
                stdout.index("promote_deep_seed.py"),
                stdout.index("plot_benchmark_gap_figure.py"),
            )
            self.assertLess(
                stdout.index("publish_results_to_site.py"),
                stdout.index("verify_45_model_repro.py"),
            )

    def test_resume_reuses_complete_clean_seeds_and_restarts_interrupted_seed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp)
            results = temporary / "results"
            for seed in (17, 18, 19, 20):
                write_seed_fixture(
                    results / f"deep_survey_seed{seed}",
                    seed=seed,
                    canonical_manifest=(seed == 17),
                )
            write_seed_fixture(
                results / "deep_survey_seed21",
                seed=21,
                model_ids=None,
                rows_per_model=127,
            )

            fake_python = temporary / "fake-python"
            fake_python.write_text(
                "#!/usr/bin/env bash\n"
                "printf '[fake-python]'\n"
                "printf ' %s' \"$@\"\n"
                "printf '\\n'\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHON_BIN": str(fake_python),
                    "STATUS_PYTHON_BIN": sys.executable,
                    "REPRO_RESULTS_DIR": str(results),
                    "RUN_LOG": str(temporary / "run.log"),
                    "REPRO_DRY_RUN": "1",
                    "RESUME": "1",
                    "SKIP_FOUNDATION": "1",
                    "DEVICE": "cuda:0",
                }
            )

            completed = subprocess.run(
                ["bash", str(RUNNER)],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            deep_commands = [
                line.replace("\\,", ",")
                for line in completed.stdout.splitlines()
                if "run_deep_survey.py" in line
            ]
            self.assertEqual(len(deep_commands), 1, completed.stdout)
            self.assertIn("--seed 21", deep_commands[0])
            self.assertIn("--no-resume", deep_commands[0])
            self.assertNotIn("--save-canonical-predictions", deep_commands[0])
            for seed in (17, 18, 19, 20):
                self.assertIn(f"seed {seed} complete and clean -> reusing", completed.stdout)

    def test_resume_restarts_seed17_with_canonical_export_when_manifest_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temporary = Path(tmp)
            results = temporary / "results"
            for seed in (17, 18, 19, 20, 21):
                write_seed_fixture(
                    results / f"deep_survey_seed{seed}",
                    seed=seed,
                    canonical_manifest=(seed == 17),
                )
            (results / "deep_survey_seed17/canonical_predictions/manifest.json").write_text("{}")

            fake_python = temporary / "fake-python"
            fake_python.write_text(
                "#!/usr/bin/env bash\n"
                "printf '[fake-python]'\n"
                "printf ' %s' \"$@\"\n"
                "printf '\\n'\n",
                encoding="utf-8",
            )
            fake_python.chmod(0o755)
            environment = os.environ.copy()
            environment.update(
                {
                    "PYTHON_BIN": str(fake_python),
                    "STATUS_PYTHON_BIN": sys.executable,
                    "REPRO_RESULTS_DIR": str(results),
                    "RUN_LOG": str(temporary / "run.log"),
                    "REPRO_DRY_RUN": "1",
                    "RESUME": "1",
                    "SKIP_FOUNDATION": "1",
                    "DEVICE": "cuda:0",
                }
            )

            completed = subprocess.run(
                ["bash", str(RUNNER)],
                cwd=REPO_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            deep_commands = [
                line.replace("\\,", ",")
                for line in completed.stdout.splitlines()
                if "run_deep_survey.py" in line
            ]
            self.assertEqual(len(deep_commands), 1, completed.stdout)
            self.assertIn("--seed 17", deep_commands[0])
            self.assertIn("--no-resume", deep_commands[0])
            self.assertIn("--save-canonical-predictions", deep_commands[0])
            self.assertIn(
                "--prediction-models dl_unet_effb0,metal_unetpp_clahe_effb0",
                deep_commands[0],
            )


if __name__ == "__main__":
    unittest.main()
