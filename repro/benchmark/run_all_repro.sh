#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_BIN="$PYTHON_BIN"
elif [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
  PYTHON_BIN="python3"
fi
DEVICE="${DEVICE:-auto}"
IMG_SIZE="${IMG_SIZE:-192}"
RUN_LOG="${RUN_LOG:-repro/run_all_repro.log}"

# The model scripts resume from existing per-model rows by default, so a rerun
# would re-emit cached results instead of recomputing them -- and the audit in
# step 8 would then verify stale output. A reproduction run must recompute;
# export RESUME=1 to continue a genuinely interrupted run instead.
RESUME_ARGS=(--no-resume)
if [[ "${RESUME:-0}" == "1" ]]; then
  RESUME_ARGS=()
  echo "[info] RESUME=1 -> reusing completed models from a previous run"
fi

mkdir -p "$(dirname "$RUN_LOG")"
if [[ "${RESUME:-0}" != "1" ]]; then
  : > "$RUN_LOG"
fi
exec > >(tee -a "$RUN_LOG") 2>&1

echo "[info] python=$PYTHON_BIN"
echo "[info] device=$DEVICE img_size=$IMG_SIZE"
echo "[info] live log: $RUN_LOG"

if [[ "${SKIP_FOUNDATION:-0}" != "1" ]]; then
  echo "[preflight] Foundation/edge device and TextureSAM assets"
  "$PYTHON_BIN" -u repro/benchmark/run_foundation_edge_addons.py \
    --img-size "$IMG_SIZE" --device "$DEVICE" --preflight-only
fi

if [[ "${PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo "[preflight] all requested checks passed"
  exit 0
fi

echo "[1/8] Classical benchmark (10 methods)"
"$PYTHON_BIN" -u repro/benchmark/run_benchmark.py "${RESUME_ARGS[@]}"

if [[ "${SKIP_DEEP:-0}" != "1" ]]; then
  echo "[2/8] Deep supervised survey (29 models)"
  "$PYTHON_BIN" -u repro/benchmark/run_deep_survey.py \
    --img-size "$IMG_SIZE" --epochs 5 --batch-size 4 --device "$DEVICE" "${RESUME_ARGS[@]}"
else
  echo "[2/8] SKIP_DEEP=1 -> skipping deep survey"
fi

if [[ "${SKIP_FOUNDATION:-0}" != "1" ]]; then
  echo "[3/8] Foundation/edge survey (6 models incl. TextureSAM)"
  "$PYTHON_BIN" -u repro/benchmark/run_foundation_edge_addons.py \
    --img-size "$IMG_SIZE" --device "$DEVICE" "${RESUME_ARGS[@]}"
else
  echo "[3/8] SKIP_FOUNDATION=1 -> skipping foundation/edge survey"
fi

echo "[4/8] Benchmark gap figure"
"$PYTHON_BIN" -u repro/benchmark/plot_benchmark_gap_figure.py

echo "[5/8] Representative appendix prediction assets"
"$PYTHON_BIN" -u repro/benchmark/build_appendix_representative_assets.py

echo "[6/8] Publish results to website assets"
"$PYTHON_BIN" -u repro/benchmark/publish_results_to_site.py

echo "[7/8] Build per-model provenance manifest"
"$PYTHON_BIN" -u repro/benchmark/build_model_provenance_manifest.py

echo "[8/8] Hard reproducibility audit (45 models)"
"$PYTHON_BIN" -u repro/benchmark/verify_45_model_repro.py

echo "[done] Repro pipeline complete."
