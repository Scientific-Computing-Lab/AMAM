#!/usr/bin/env python3
"""Create the main-paper track-specific benchmark score figure.

This figure is built directly from the released CSV outputs:
- repro/results/classical/benchmark_macro_over_subsets.csv
- repro/results/deep_survey/deep_macro_over_subsets.csv (model metadata)
- repro/results/deep_survey_multiseed_summary.csv (five-run deep mIoU means)
- repro/results/foundation_edge/foundation_edge_summary.csv
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.style.use("default")
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS = REPO_ROOT / "repro" / "results"
OUT_PDF = REPO_ROOT / "repro" / "figures" / "benchmark-gap-overview.pdf"
OUT_PNG = REPO_ROOT / "repro" / "figures" / "benchmark-gap-overview.png"
FAMILY_ORDER = ["Classical", "Deep-General", "Deep-Metallography", "Foundation/Edge"]
PALETTE = {
    "Classical": "#1f77b4",
    "Deep-General": "#2ca02c",
    "Deep-Metallography": "#d62728",
    "Foundation/Edge": "#9467bd",
}


def load_all_results() -> pd.DataFrame:
    classical = pd.read_csv(RESULTS / "classical" / "benchmark_macro_over_subsets.csv")
    classical_map = {
        "rf_pixel": "RF (pixel features)",
        "gmm_rgb": "GMM-RGB",
        "svm_pixel": "Linear SVM (pixel features)",
        "gabor_kmeans": "Gabor+KMeans",
        "slic_cluster": "SLIC+KMeans",
        "kmeans_rgb": "KMeans-RGB",
        "felzenszwalb_cluster": "Felzenszwalb-GMM",
        "lbp_kmeans": "LBP+KMeans",
        "canny_watershed": "Canny+Watershed",
        "sobel_watershed": "Sobel+Watershed",
    }
    classical = classical.assign(
        model=classical["method"].map(classical_map).fillna(classical["method"]),
        family="Classical",
    )[["model", "family", "miou"]]

    deep_meta = pd.read_csv(RESULTS / "deep_survey" / "deep_macro_over_subsets.csv")
    deep_spread = pd.read_csv(RESULTS / "deep_survey_multiseed_summary.csv")
    deep = deep_meta.merge(
        deep_spread[["model_id", "miou_mean"]],
        on="model_id",
        how="inner",
        validate="one_to_one",
    )
    if len(deep) != len(deep_meta):
        raise ValueError("Deep multiseed summary does not cover every deep model.")
    deep = deep.assign(
        model=deep["display_name"],
        family=np.where(deep["group"] == "general", "Deep-General", "Deep-Metallography"),
        miou=deep["miou_mean"],
    )[["model", "family", "miou"]]

    foundation = pd.read_csv(RESULTS / "foundation_edge" / "foundation_edge_summary.csv")
    foundation_map = {
        "sam_vit_base": "SAM ViT-Base (auto-mask)",
        "slimsam_50": "SlimSAM-50 (auto-mask)",
        "slimsam_77": "SlimSAM-77 (auto-mask)",
        "texturesam_03": "TextureSAM-0.3 (auto-mask)",
        "hed_watershed": "HED + Watershed",
        "pidi_watershed": "PidiNet + Watershed",
    }
    foundation = foundation.assign(
        model=foundation["model_id"].map(foundation_map).fillna(foundation["model_id"]),
        family="Foundation/Edge",
    )[["model", "family", "miou"]]

    df = pd.concat([classical, deep, foundation], ignore_index=True)
    df["miou"] = df["miou"].astype(float)
    return df


def create_figure(df: pd.DataFrame) -> plt.Figure:
    """Build Figure 3 without saving it so callers can inspect the rendered contract."""
    fig = plt.figure(figsize=(13.4, 5.8))
    outer = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.65], wspace=0.25)
    ax_left = fig.add_subplot(outer[0, 0])
    facet_grid = outer[0, 1].subgridspec(2, 2, hspace=0.50, wspace=0.24)
    facet_axes = [
        fig.add_subplot(facet_grid[row, column])
        for row in range(2)
        for column in range(2)
    ]
    ax_left.set_facecolor("white")

    # Left panel: per-track distributions with track-local leader markers.
    rng = np.random.default_rng(7)
    positions = np.arange(len(FAMILY_ORDER))
    family_values = [df.loc[df["family"] == fam, "miou"].to_numpy() for fam in FAMILY_ORDER]

    bp = ax_left.boxplot(
        family_values,
        positions=positions,
        widths=0.52,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "black", "linewidth": 1.4},
        whiskerprops={"color": "#666666", "linewidth": 1.0},
        capprops={"color": "#666666", "linewidth": 1.0},
    )
    for patch, fam in zip(bp["boxes"], FAMILY_ORDER):
        patch.set_facecolor(PALETTE[fam])
        patch.set_alpha(0.24)
        patch.set_edgecolor(PALETTE[fam])
        patch.set_linewidth(1.2)

    for idx, fam in enumerate(FAMILY_ORDER):
        vals = df.loc[df["family"] == fam, "miou"].to_numpy()
        jitter = rng.normal(0.0, 0.06, size=len(vals))
        ax_left.scatter(
            np.full_like(vals, idx, dtype=float) + jitter,
            vals,
            s=26,
            color=PALETTE[fam],
            alpha=0.82,
            edgecolor="white",
            linewidth=0.35,
            zorder=3,
        )
        leader_idx = df.loc[df["family"] == fam, "miou"].idxmax()
        leader_row = df.loc[leader_idx]
        ax_left.scatter(
            idx,
            leader_row["miou"],
            marker="*",
            s=190,
            color="#ffcc00",
            edgecolor="black",
            linewidth=0.7,
            zorder=6,
        )
        ax_left.text(
            idx,
            leader_row["miou"] + 0.015,
            f"{leader_row['miou']:.3f}",
            ha="center",
            va="bottom",
            fontsize=8,
            weight="bold",
        )

    ax_left.axhline(1.0, color="#555555", linestyle="--", linewidth=1.0)
    ax_left.axhline(0.7, color="#9a9a9a", linestyle=":", linewidth=1.0)
    ax_left.text(3.48, 1.0, "Perfect (1.0)", fontsize=8, va="bottom", ha="right", color="#555555")
    ax_left.text(3.48, 0.7, "0.7 reference", fontsize=8, va="bottom", ha="right", color="#666666")
    ax_left.set_ylim(0.30, 1.02)
    ax_left.set_ylabel("Subset-Macro mIoU")
    ax_left.set_xticks(positions)
    ax_left.set_xticklabels(
        ["Classical\n(n=10)", "Deep-General\n(n=14)", "Deep-Metal\n(n=15)", "Foundation/Edge\n(n=6)"],
        fontsize=8,
    )
    ax_left.set_title("Track-Group Score Distributions")
    ax_left.grid(axis="y", alpha=0.22, linewidth=0.7)

    # Right panel: four independent within-track score orderings.
    for facet_index, (axis, family) in enumerate(zip(facet_axes, FAMILY_ORDER)):
        subset = (
            df.loc[df["family"] == family]
            .sort_values(["miou", "model"], ascending=[False, True])
            .reset_index(drop=True)
        )
        facet_positions = np.arange(1, len(subset) + 1)
        values = subset["miou"].to_numpy()

        axis.set_facecolor("white")
        axis.scatter(
            facet_positions,
            values,
            s=27,
            color=PALETTE[family],
            alpha=0.88,
            edgecolor="white",
            linewidth=0.35,
            zorder=3,
        )
        axis.plot(
            facet_positions,
            values,
            color=PALETTE[family],
            linewidth=1.0,
            alpha=0.65,
            zorder=2,
        )
        axis.scatter(
            1,
            values[0],
            marker="*",
            s=135,
            color="#ffcc00",
            edgecolor="black",
            linewidth=0.6,
            zorder=4,
        )
        axis.text(
            1,
            values[0] + 0.020,
            f"{values[0]:.3f}",
            ha="center",
            va="bottom",
            fontsize=7.5,
            weight="bold",
        )
        axis.axhline(1.0, color="#777777", linestyle="--", linewidth=0.8)
        axis.set_xlim(0.5, len(subset) + 0.5)
        axis.set_ylim(0.30, 1.02)
        middle_position = max(1, round(len(subset) / 2))
        axis.set_xticks(sorted({1, middle_position, len(subset)}))
        axis.set_xlabel("Within-track position", fontsize=8)
        axis.set_title(f"{family} (n={len(subset)})", fontsize=9.5, weight="bold")
        axis.tick_params(axis="both", labelsize=7.5)
        axis.grid(axis="y", alpha=0.22, linewidth=0.65)
        if facet_index % 2 == 0:
            axis.set_ylabel("Subset-Macro mIoU", fontsize=8)
        else:
            axis.tick_params(axis="y", labelleft=False)

    fig.suptitle(
        "AMAM-128 Track-Specific Reported Score Distributions",
        y=0.975,
        fontsize=12,
        weight="bold",
    )
    fig.text(
        0.5,
        0.018,
        "Deep points are five-run means (seeds 17–21); classical and foundation/edge points are seed-17 "
        "estimates. Label handling differs across tracks.",
        ha="center",
        va="bottom",
        fontsize=8,
        color="#333333",
    )
    fig.subplots_adjust(left=0.060, right=0.985, bottom=0.17, top=0.86)
    return fig


def build_figure(
    df: pd.DataFrame,
    out_pdf: Path = OUT_PDF,
    out_png: Path = OUT_PNG,
) -> None:
    """Save Figure 3 in both released formats."""
    fig = create_figure(df)
    try:
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
        fig.savefig(out_png, dpi=300, bbox_inches="tight")
    finally:
        plt.close(fig)


def main() -> None:
    df = load_all_results()
    build_figure(df)
    print(f"[ok] wrote {OUT_PDF}")
    print(f"[ok] wrote {OUT_PNG}")
    counts = df["family"].value_counts()
    count_text = ", ".join(f"{family}={counts[family]}" for family in FAMILY_ORDER)
    print(f"[summary] methods={len(df)}; {count_text}")


if __name__ == "__main__":
    main()
