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
STATUS_PYTHON_BIN="${STATUS_PYTHON_BIN:-$PYTHON_BIN}"
REPRO_RESULTS_DIR="${REPRO_RESULTS_DIR:-repro/results}"

# The model scripts resume from existing per-model rows by default, so a rerun
# would re-emit cached results instead of recomputing them -- and the audit in
# step 10 would then verify stale output. A reproduction run must recompute;
# export RESUME=1 to continue a genuinely interrupted run instead.
RESUME_ARGS=(--no-resume)
CLASSICAL_PREDICTION_ARGS=(--save-canonical-predictions --prediction-models rf_pixel)
DEEP_PREDICTION_ARGS=(
  --save-canonical-predictions
  --prediction-models dl_unet_effb0,metal_unetpp_clahe_effb0
)
if [[ "${RESUME:-0}" == "1" ]]; then
  RESUME_ARGS=()
  CLASSICAL_PREDICTION_ARGS=()
  echo "[info] RESUME=1 -> reusing complete clean deep seeds; incomplete seeds restart cleanly"
fi

run_cmd() {
  if [[ "${REPRO_DRY_RUN:-0}" == "1" ]]; then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
    return 0
  fi
  "$@"
}

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
  run_cmd "$PYTHON_BIN" -u repro/benchmark/run_foundation_edge_addons.py \
    --img-size "$IMG_SIZE" --device "$DEVICE" --preflight-only
fi

if [[ "${PREFLIGHT_ONLY:-0}" == "1" ]]; then
  echo "[preflight] all requested checks passed"
  exit 0
fi

echo "[1/10] Classical benchmark (10 methods)"
run_cmd "$PYTHON_BIN" -u repro/benchmark/run_benchmark.py \
  "${RESUME_ARGS[@]}" "${CLASSICAL_PREDICTION_ARGS[@]}"

if [[ "${SKIP_DEEP:-0}" != "1" ]]; then
  echo "[2/10] Deep supervised survey (29 models x seeds 17-21)"
  for seed in 17 18 19 20 21; do
    seed_dir="${REPRO_RESULTS_DIR}/deep_survey_seed${seed}"
    seed_resume_args=(--no-resume)
    seed_prediction_args=()
    if [[ "$seed" == "17" ]]; then
      seed_prediction_args=("${DEEP_PREDICTION_ARGS[@]}")
    fi

    if [[ "${RESUME:-0}" == "1" ]]; then
      status_args=(
        --seed-dir "$seed_dir"
        --seed "$seed"
        --expected-img-size "$IMG_SIZE"
      )
      if [[ "$seed" == "17" ]]; then
        status_args+=(--require-canonical-manifest)
      fi
      if "$STATUS_PYTHON_BIN" -u repro/benchmark/deep_seed_status.py "${status_args[@]}"; then
        echo "[info] seed $seed complete and clean -> reusing"
        continue
      fi
      echo "[info] seed $seed incomplete or non-clean -> restarting with --no-resume"
    fi

    run_cmd "$PYTHON_BIN" -u repro/benchmark/run_deep_survey.py \
      --img-size "$IMG_SIZE" --epochs 5 --batch-size 4 --device "$DEVICE" \
      --seed "$seed" --out-dir "$seed_dir" \
      "${seed_resume_args[@]}" "${seed_prediction_args[@]}"
  done
else
  echo "[2/10] SKIP_DEEP=1 -> using existing seed 17-21 deep results"
fi

echo "[3/10] Aggregate deep seeds 17-21"
run_cmd "$PYTHON_BIN" -u repro/benchmark/aggregate_deep_multiseed.py

echo "[4/10] Promote validated seed-17 deep details"
run_cmd "$PYTHON_BIN" -u repro/benchmark/promote_deep_seed.py

if [[ "${SKIP_FOUNDATION:-0}" != "1" ]]; then
  echo "[5/10] Foundation/edge survey (6 models incl. TextureSAM)"
  run_cmd "$PYTHON_BIN" -u repro/benchmark/run_foundation_edge_addons.py \
    --img-size "$IMG_SIZE" --device "$DEVICE" "${RESUME_ARGS[@]}"
else
  echo "[5/10] SKIP_FOUNDATION=1 -> skipping foundation/edge survey"
fi

echo "[6/10] Track-specific reported-score figure"
run_cmd "$PYTHON_BIN" -u repro/benchmark/plot_benchmark_gap_figure.py

echo "[7/10] Representative appendix prediction assets"
run_cmd "$PYTHON_BIN" -u repro/benchmark/build_appendix_representative_assets.py

echo "[8/10] Publish results to website assets"
run_cmd "$PYTHON_BIN" -u repro/benchmark/publish_results_to_site.py

echo "[9/10] Build per-model provenance manifest"
run_cmd "$PYTHON_BIN" -u repro/benchmark/build_model_provenance_manifest.py

echo "[10/10] Artifact consistency audit (45 methods)"
run_cmd "$PYTHON_BIN" -u repro/benchmark/verify_45_model_repro.py

echo "[done] Repro pipeline complete."
