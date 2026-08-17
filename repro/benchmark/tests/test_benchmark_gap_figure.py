from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import matplotlib.pyplot as plt

BENCHMARK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_DIR))

from plot_benchmark_gap_figure import build_figure, create_figure, load_all_results


class BenchmarkGapFigureTests(unittest.TestCase):
    def test_released_results_have_expected_track_counts(self) -> None:
        counts = load_all_results()["family"].value_counts().to_dict()
        self.assertEqual(
            counts,
            {
                "Classical": 10,
                "Deep-General": 14,
                "Deep-Metallography": 15,
                "Foundation/Edge": 6,
            },
        )

    def test_figure_uses_four_within_track_facets_without_global_leaderboard_language(self) -> None:
        fig = create_figure(load_all_results())
        try:
            expected_counts = {
                "Classical (n=10)": 10,
                "Deep-General (n=14)": 14,
                "Deep-Metallography (n=15)": 15,
                "Foundation/Edge (n=6)": 6,
            }
            facets = {
                axis.get_title(): axis
                for axis in fig.axes
                if axis.get_title() in expected_counts
            }
            self.assertEqual(set(facets), set(expected_counts))
            for title, expected_count in expected_counts.items():
                self.assertEqual(
                    len(facets[title].collections[0].get_offsets()),
                    expected_count,
                )
            self.assertEqual(sum(expected_counts.values()), 45)

            rendered_text = " ".join(
                [text.get_text() for text in fig.texts]
                + [
                    value
                    for axis in fig.axes
                    for value in (
                        axis.get_title(),
                        axis.get_xlabel(),
                        axis.get_ylabel(),
                        *[text.get_text() for text in axis.texts],
                    )
                ]
            ).lower()
            for forbidden in (
                "highest displayed score",
                "best overall",
                "winner",
                "45-method ordering",
            ):
                self.assertNotIn(forbidden, rendered_text)
        finally:
            plt.close(fig)

    def test_build_figure_writes_nonempty_pdf_and_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdf = root / "figure.pdf"
            png = root / "figure.png"
            build_figure(load_all_results(), out_pdf=pdf, out_png=png)
            self.assertGreater(pdf.stat().st_size, 0)
            self.assertGreater(png.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
