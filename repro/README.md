# Reproducibility Package (AMAM-128)

This folder contains the full code and outputs used to build the benchmark results and figures.

## What Is Included

- `benchmark/`: all benchmark execution scripts (classical, deep, foundation/edge, plotting, appendix assets, site publishing).
- `results/`: generated CSV summaries and per-image/per-subset outputs.
- `figures/`: generated benchmark figures and appendix visual assets.
- `requirements.txt`: Python dependencies for reruns.

For classical methods, `repro/results/classical/benchmark_summary.csv` is the canonical subset-macro table used by the paper/site, and `benchmark_micro_over_images.csv` is also exported for image-level reference.

Protocol note: current benchmark execution uses `fullset_no_holdout` mode, so each of the 45 models is evaluated on all 128 paired images.
At evaluation time, subset identity and its valid class set are assumed known;
this preserves subset-native semantics rather than merging incompatible
taxonomies.

## Quick Start

```bash
# from repository root
python3 -m venv .venv
source .venv/bin/activate
pip install -r repro/requirements.txt
```

## Run Full Reproduction

```bash
# from repository root
bash repro/benchmark/run_all_repro.sh

# explicitly select the first CUDA GPU
DEVICE=cuda:0 bash repro/benchmark/run_all_repro.sh
```

The runner generates local per-seed deep outputs in
`repro/results/deep_survey_seed17/` through
`repro/results/deep_survey_seed21/`. These directories are the authoritative
inputs for local aggregation but are intentionally excluded from version
control. From them, GitHub tracks only
`repro/results/deep_survey_seed17/canonical_predictions/`, which contains the
qualitative masks used by the representative panels. The published numerical
record for all five seeds is `repro/results/deep_survey_multiseed_runs.csv`
(145 rows), and `deep_survey_multiseed_summary.csv` contains five-seed
mean/sample-SD values. After aggregation, the runner promotes the validated
seed-17 detail files into `repro/results/deep_survey/` for legacy consumers.

Inspect the complete command plan without starting models or mutating result
artifacts:

```bash
REPRO_DRY_RUN=1 DEVICE=cuda:0 bash repro/benchmark/run_all_repro.sh
```

Live output is written to `repro/run_all_repro.log` and can be followed with
`tail -f repro/run_all_repro.log`. Use `RESUME=1` only to continue completed
per-model rows from an interrupted run; a normal run recomputes every method,
including five complete deep sweeps.

For a script-by-script execution map (exact model families, outputs, and protocol files), see:

- `repro/benchmark/README.md`

This executes:

1. Classical benchmark (`run_benchmark.py`)
2. Five deep benchmarks for seeds 17--21 (`run_deep_survey.py`)
3. Aggregate the five deep runs (`aggregate_deep_multiseed.py`)
4. Promote validated seed-17 details (`promote_deep_seed.py`)
5. Foundation/edge benchmark (`run_foundation_edge_addons.py`)
6. Track-specific reported-score figure generation (`plot_benchmark_gap_figure.py`)
7. Representative appendix assets (`build_appendix_representative_assets.py`)
8. Publish website CSVs (`publish_results_to_site.py`)
9. Build the provenance manifest (`build_model_provenance_manifest.py`)
10. Build the 45-method audit (`verify_45_model_repro.py`)

## Optional Fast Modes

Skip expensive stages:

```bash
SKIP_DEEP=1 bash repro/benchmark/run_all_repro.sh
SKIP_FOUNDATION=1 bash repro/benchmark/run_all_repro.sh
```

`SKIP_DEEP=1` skips deep training but still aggregates and validates the five
explicit seed directories, so all five generated directories must already
exist locally. `SKIP_FOUNDATION=1` skips the foundation/edge preflight and
model stage.

## External TextureSAM Dependency

The complete 45-model run requires TextureSAM under:

- `repro/external/TextureSAM`
- `repro/external/TextureSAM_Datasets/checkpoints/sam2.1_hiera_small_0.3.pt`

The full runner validates both paths before starting the classical or deep
stages. TextureSAM is optional only when calling the foundation script with a
`--models` selection that excludes `texturesam_03`.

Exact sources used:

- `https://github.com/Scientific-Computing-Lab/TextureSAM`
- `https://drive.google.com/drive/folders/1pUJLa898WYEcb4Y_sOaXsSVe-CsPkwRv`

## Per-Model Checkpoint Provenance

The full 45-row model checkpoint/source manifest is generated at:

- `repro/results/model_provenance_manifest.csv`
- `repro/results/model_provenance_manifest.md`

Internal consistency audit outputs:

- `repro/results/reproducibility_audit_45_models.json`
- `repro/results/reproducibility_audit_45_models.md`

These validate a single run's artifacts — model counts, agreement between the
result files, and artifact hashes. They do not compare one run against another,
so a `PASS` is not evidence that a rerun reproduces the published numbers. For
what does and does not reproduce, see "Scope of reproducibility" in
`repro/benchmark/README.md`.
