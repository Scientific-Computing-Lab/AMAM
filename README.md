# AMAM Benchmark Website

Interactive dataset website for the **Annotated Metallic Alloys Microstructures (AMAM)** benchmark.

## Features

- Dataset overview, creation workflow, and statistics
- Section-by-section explorer for all AMAM subsets
- Responsive image gallery with zoom/lightbox navigation
- Per-image metadata and quick property view
- Category-level and global download controls
- Metadata export (`amam-dataset-manifest.json`)

## Local preview

```bash
# from repository root
python3 -m http.server 4177
# open http://127.0.0.1:4177
```

## Files

- `index.html`: page structure
- `assets/css/styles.css`: design and responsive layout
- `assets/js/app.js`: rendering, filters, lightbox, downloads
- `assets/data/amam-dataset.json`: dataset metadata + links
- `assets/images/*`: representative microstructure samples
- `repro/*`: full reproducibility package (benchmark code, outputs, and figures)

## Reproduce benchmark results

```bash
# from repository root
python3 -m venv .venv
.venv/bin/pip install -r repro/requirements.txt
bash repro/benchmark/run_all_repro.sh
```

The complete 45-model run also needs TextureSAM, which is not tracked in this
repository. The runner validates it before any model stage, so set it up first:

```bash
mkdir -p repro/external
git clone https://github.com/Scientific-Computing-Lab/TextureSAM repro/external/TextureSAM
mkdir -p repro/external/TextureSAM_Datasets/checkpoints
# then download sam2.1_hiera_small_0.3.pt from
# https://drive.google.com/drive/folders/1pUJLa898WYEcb4Y_sOaXsSVe-CsPkwRv
# to repro/external/TextureSAM_Datasets/checkpoints/sam2.1_hiera_small_0.3.pt
```

To check the environment and those assets without starting a model run:

```bash
PREFLIGHT_ONLY=1 bash repro/benchmark/run_all_repro.sh
```

Use `SKIP_FOUNDATION=1` to run without TextureSAM.

A rerun does not reproduce every published number. The 10 classical methods and
6 foundation/edge models are deterministic, but the 29 supervised deep models
are retrained on each run and move by about 0.03 macro mIoU. See "Scope of
reproducibility" in `repro/benchmark/README.md` before comparing results.

Detailed instructions are in `repro/README.md`.
Execution details for every model family are in `repro/benchmark/README.md`.
Per-model checkpoint/source traceability is in `repro/results/model_provenance_manifest.csv`.
The 45-model internal consistency audit — model counts, cross-file agreement and
artifact hashes for a single run — is in
`repro/results/reproducibility_audit_45_models.json`. It does not compare
separate runs.

## Deployment notes

- A `.nojekyll` file is included so GitHub Pages serves static assets directly.
- For private-only GitHub Pages publication, GitHub requires enterprise access-control support.
- On personal `GitHub Free`, GitHub Pages is not private-access controlled.
