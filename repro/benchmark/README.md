# AMAM-128 Benchmark Execution (Model Runs + Inference)

This directory contains the exact scripts used to run the AMAM-128 model experiments.

## What Is Executed Here

All model testing is executed locally from these scripts (not via a hosted inference service):

- `run_benchmark.py`: 10 classical methods.
- `run_deep_survey.py`: 29 supervised deep methods.
- `aggregate_deep_multiseed.py`: combines the five isolated deep runs and
  reproduces their per-seed and aggregate CSV artifacts.
- `run_foundation_edge_addons.py`: 6 foundation/edge add-ons (including the required TextureSAM model).
- `plot_benchmark_gap_figure.py`: main benchmark-gap figure.
- `build_appendix_representative_assets.py`: appendix visual audit assets.
- `publish_results_to_site.py`: syncs reproducibility outputs into website CSV artifacts.
- `build_model_provenance_manifest.py`: writes a 45-row per-model checkpoint/source manifest.
- `verify_45_model_repro.py`: hard verification that all 45 model ids/checkpoint rows/results are consistent.

## One-Command Full Reproduction

```bash
# from repository root; auto selects CUDA when it is available
bash repro/benchmark/run_all_repro.sh

# equivalent explicit GPU selection
DEVICE=cuda:0 bash repro/benchmark/run_all_repro.sh
```

The runner writes live output to `repro/run_all_repro.log`. Follow it from a
second terminal with:

```bash
tail -f repro/run_all_repro.log
```

A fresh run recomputes every model. To continue a genuinely interrupted run
from its completed per-model checkpoints, use:

```bash
RESUME=1 DEVICE=cuda:0 bash repro/benchmark/run_all_repro.sh
```

Do not use `RESUME=1` for the first run after a ground-truth decoder or metric
policy change; cached per-image rows were computed under the previous protocol.

To validate Python, GPU selection, and TextureSAM assets without starting any
model run:

```bash
PREFLIGHT_ONLY=1 DEVICE=cuda:0 bash repro/benchmark/run_all_repro.sh
```

Pipeline order:

1. Classical benchmark (`run_benchmark.py`)
2. Deep benchmark (`run_deep_survey.py`)
3. Foundation/edge benchmark (`run_foundation_edge_addons.py`)
4. Gap figure generation
5. Representative appendix assets generation
6. Publish CSVs to `assets/data/results/`
7. Build `repro/results/model_provenance_manifest.csv` and `.md`
8. Build `repro/results/reproducibility_audit_45_models.json` and `.md`

## Run Families Separately

```bash
# 10 classical
python3 repro/benchmark/run_benchmark.py

# 29 supervised deep (14 general + 15 metallography-oriented)
python3 repro/benchmark/run_deep_survey.py --img-size 192 --epochs 5 --batch-size 4 --device auto

# 6 foundation/edge add-ons (SAM/SlimSAM/TextureSAM/HED/PidiNet)
python3 repro/benchmark/run_foundation_edge_addons.py --img-size 192 --device auto
```

## Seeds / Protocol

- Pair-only inclusion from `assets/data/amam-dataset.json`.
- Default reporting seed: `17` for randomized internals.
- Evaluation mode: `fullset_no_holdout` (all 128 paired tuples are used for per-model inference/evaluation).
- Subset-aware macro metrics: mIoU, Dice, Pixel Accuracy.
- Per-image mIoU and Dice exclude any class absent from both ground truth and
  prediction; present-class scores are averaged per image, then per subset.
- Ground-truth RGB masks are decoded at source resolution using the frozen
  per-subset prototypes in `gt_mask_palettes.json`; only the resulting class-ID
  maps are resized, using nearest-neighbor interpolation.
- Output protocol manifests:
  - `repro/results/classical/benchmark_protocol.json`
  - `repro/results/deep_survey/deep_protocol.json`
  - `repro/results/foundation_edge/foundation_edge_protocol.json`

### Scope of reproducibility

Seed `17` is set, but seeding alone does not make GPU training reproducible.

- **Classical (10 methods)**: the published table reports seed-17 point
  estimates. The seed affects sampling and randomized estimators; ground-truth
  decoding is fixed. The release makes no cross-seed uncertainty claim for
  these methods.
- **Foundation/edge (6 methods)**: pretrained network weights are not updated
  from AMAM labels, but seeded model-side downstream clustering and
  post-processing are data-adaptive; ground-truth decoding is fixed. The
  published table reports seed-17 point estimates. The runner requires
  `transformers` 4.x; on 5.x the SAM mask-generation pipeline returns a
  whole-image mask as its top-scoring proposal, which collapses all three SAM
  variants to the same degenerate prediction.
- **Deep survey (29 configurations)**: five clean, non-resumed end-to-end runs
  using seeds 17--21 provide the reported mIoU means and sample standard
  deviations. The five seeds vary model initialization and batch order while
  ground-truth decoding is fixed, so the spread reflects training-run
  variability rather than label-decoding variability.

Across the 29 deep configurations, the median sample standard deviation is
`0.031784` macro mIoU (range `0.006102`--`0.059538`). After sorting models by
their five-run mean, the median of the 28 adjacent mean gaps is `0.004426`;
the ratio of these two descriptive summaries is `7.181`. The mean-ranked deep
table should therefore be read descriptively rather than as a stable total
ordering. These quantities are not confidence intervals for dataset-sampling
uncertainty and are not pairwise significance tests.

The auditable per-seed values and their aggregate are:

- `repro/results/deep_survey_multiseed_runs.csv` (145 rows: 29 models x 5 seeds)
- `repro/results/deep_survey_multiseed_summary.csv` (mIoU, Dice, and Pixel
  Accuracy mean/sample SD/range, plus mIoU rank range per model)

Each rank range is the model's best-to-worst position among the 29 supervised
deep configurations in the five seed-specific runs. It is not a rank among all
45 displayed methods.

Create the isolated runs and regenerate both published CSVs with:

```bash
for seed in 17 18 19 20 21; do
  .venv/bin/python repro/benchmark/run_deep_survey.py \
    --img-size 192 --epochs 5 --batch-size 4 --device auto \
    --seed "$seed" --out-dir "repro/results/deep_survey_seed${seed}" --no-resume
done
.venv/bin/python repro/benchmark/aggregate_deep_multiseed.py
```

Use the multi-seed summary for deep mIoU, Dice, and Pixel Accuracy. The
`deep_macro_over_subsets.csv` file remains the canonical seed-17 result.

## Where Outputs Are Written

### Classical (10)

- `repro/results/classical/benchmark_summary.csv`
- `repro/results/classical/benchmark_macro_over_subsets.csv`
- `repro/results/classical/benchmark_micro_over_images.csv`
- `repro/results/classical/benchmark_per_subset.csv`
- `repro/results/classical/benchmark_raw_per_image.csv`

`benchmark_summary.csv` is the canonical subset-macro summary used by the paper and website.

### Supervised Deep (29)

- `repro/results/deep_survey/deep_general_summary.csv`
- `repro/results/deep_survey/deep_metallography_summary.csv`
- `repro/results/deep_survey/deep_macro_over_subsets.csv`
- `repro/results/deep_survey/deep_per_subset.csv`
- `repro/results/deep_survey/deep_per_image.csv`
- `repro/results/deep_survey_multiseed_runs.csv`
- `repro/results/deep_survey_multiseed_summary.csv`

### Foundation / Edge (6)

- `repro/results/foundation_edge/foundation_edge_summary.csv`
- `repro/results/foundation_edge/foundation_edge_per_subset.csv`
- `repro/results/foundation_edge/foundation_edge_per_image.csv`

### Published Website CSVs

- `assets/data/results/benchmark_summary.csv`
- `assets/data/results/deep_macro_over_subsets.csv`
- `assets/data/results/deep_survey_multiseed_runs.csv`
- `assets/data/results/deep_survey_multiseed_summary.csv`
- `assets/data/results/foundation_edge_summary.csv`

### Checkpoint / Source Manifest (All 45 Models)

- `repro/results/model_provenance_manifest.csv`
- `repro/results/model_provenance_manifest.md`

## Artifact Consistency Audit (45 Methods)

```bash
python3 repro/benchmark/verify_45_model_repro.py
```

This command fails if any model id is missing/misaligned across result files, or if the provenance manifest is incomplete. On success, it writes:

- `repro/results/reproducibility_audit_45_models.json`
- `repro/results/reproducibility_audit_45_models.md`

## TextureSAM Dependency

TextureSAM is required for a complete 45-method reproduction. The full runner
checks these assets before starting any expensive model stage:

- `repro/external/TextureSAM`
- `repro/external/TextureSAM_Datasets/checkpoints/sam2.1_hiera_small_0.3.pt`

Exact sources used in this benchmark:

- TextureSAM repository: `https://github.com/Scientific-Computing-Lab/TextureSAM`
- TextureSAM checkpoints drive: `https://drive.google.com/drive/folders/1pUJLa898WYEcb4Y_sOaXsSVe-CsPkwRv`

Example setup:

```bash
mkdir -p repro/external
git clone https://github.com/Scientific-Computing-Lab/TextureSAM repro/external/TextureSAM
mkdir -p repro/external/TextureSAM_Datasets/checkpoints
# then place sam2.1_hiera_small_0.3.pt at:
# repro/external/TextureSAM_Datasets/checkpoints/sam2.1_hiera_small_0.3.pt
```

TextureSAM is optional only for a selective foundation run that excludes
`texturesam_03` with `--models`.
