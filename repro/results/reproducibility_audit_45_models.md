# AMAM-128 Artifact Consistency Audit (45 Methods)

- Status: **PASS**
- Git commit: `538036de06d019094c15471103329ad5e1e77478`
- Model counts:
  - Classical: 10
  - Deep general: 14
  - Deep metallography: 15
  - Foundation/edge: 6
  - Total: 45

## Consistency Checks
- Classical summary/per-image/per-subset IDs match: `True`
- Deep summary/per-image/per-subset IDs match: `True`
- Foundation summary/per-image/per-subset IDs match: `True`
- Provenance manifest matches results IDs: `True`
- Deep five-run values are complete (29 x 5): `True`
- Deep aggregate matches the per-seed values: `True`
- Canonical prediction manifests and hashes validate: `True`
- Representative panels use seed-17 canonical predictions: `True`

## Key Artifacts (SHA256)
- `repro/results/classical/benchmark_summary.csv`: `344f0a83e359af8622d88957428cb810417e5f16e7da22e21b967d9edf527a34`
- `repro/results/classical/benchmark_raw_per_image.csv`: `476746eb25853ed0de3658fd7e53db4b978f5810e113b77425922eb9fdbc6a6d`
- `repro/results/classical/benchmark_per_subset.csv`: `2197cf897be361a4693f931cb5fae343868ba63303d750546dded51b5dab44b1`
- `repro/results/deep_survey/deep_general_summary.csv`: `cdb6d0b7f7204c10b1cd7be8c421eb104b9402f44b4f611b7d03cbfda8e3455b`
- `repro/results/deep_survey/deep_metallography_summary.csv`: `7023e36bf9fb1580df60ee53e757f15f40bc910a642d4be975ad774a8b152048`
- `repro/results/deep_survey/deep_per_image.csv`: `198b6ea160e589ca0ae5e96fa05d1346f5d6ef095aaeab91a888fa19be19125d`
- `repro/results/deep_survey/deep_per_subset.csv`: `e3af8c0f23a9e62e608b90d44d6e05beee690cf7089bf9f7eb60b4ae878146d5`
- `repro/results/deep_survey_multiseed_runs.csv`: `be6b73aba79c7a81d73b700bd3906d7fab4781dc58b47dfa93860a9ab623f5f0`
- `repro/results/deep_survey_multiseed_summary.csv`: `239e69a11ae873504a30f682c6db9385d04a1a1d42a394cd73ac807e89bfc5fe`
- `repro/results/foundation_edge/foundation_edge_summary.csv`: `abce555e4b8e689065c4d91bee9f26e499f94b77ffa4f7ae6435e5384df5ce60`
- `repro/results/foundation_edge/foundation_edge_per_image.csv`: `ef5e15a378032edcad058269a0b0dcda3d05f6657de89c78ba1e7d2167a0bbd8`
- `repro/results/foundation_edge/foundation_edge_per_subset.csv`: `5d3dc6dd34c68b9975b7a2a3096fdcbf0c278a00dc84784ade2c2520e930d2cb`
- `repro/results/classical/benchmark_protocol.json`: `b8bbee2af19c0b89b3f4c119f645c4df578bb7c949d9456b2895c3378a59b8e7`
- `repro/results/deep_survey/deep_protocol.json`: `58f807ef590c392da1f0386c8dca2611ad473ad2e7e0866ba17a6378ccb51905`
- `repro/results/foundation_edge/foundation_edge_protocol.json`: `ea6115c8499c8ceac408d95463c2707640274fd298a5687a93a8de7905723495`
- `repro/results/classical/canonical_predictions/manifest.json`: `eadcbe9d2c6dfcb638aef59669fb7af05518851d596f158eb3b655f3ba1f40b7`
- `repro/results/deep_survey_seed17/canonical_predictions/manifest.json`: `caaca3afbc0945bf7999e5390f450df1450abea45e2c48b193c4c0d2f24a8c6c`
- `repro/figures/appendix_preds/panel_metadata.json`: `baf7c3e72c93748c55b12bb432686e2ce0108a01db73ebe1f6bd69e7a1d52eb2`
- `repro/results/model_provenance_manifest.csv`: `d703d0a17771ab5a364da45421ef60795483fa9cba67ce62914a9c4d75a694b9`
- `assets/data/amam-dataset.json`: `7ea757a15626a00ecd03faac727a98deea836390ffd499ea78c910f65329c2cd`
- `repro/benchmark/run_deep_survey.py`: `cc31989c366441b4630ccdc191f876e97e470f373ac528826a96fa2e7060d961`
- `repro/benchmark/aggregate_deep_multiseed.py`: `d042896d426d00a6f0bfd7925b6b34d7d2aca19adc2c0396d9348e8acff846f4`
- `repro/benchmark/plot_benchmark_gap_figure.py`: `f75f5669f4c0d0793cba9dce19db78737d003b4296310ba9b30b4818c3ce1575`
- `repro/benchmark/canonical_predictions.py`: `f5877be8218a51f09c593f3523fe451d48e56bbafe74066a572e25019d874c25`
- `repro/benchmark/build_appendix_representative_assets.py`: `b7fca125f5dda5062fe48a237a43312ffa8f4b8acf12bb2d391e472d627a8109`
- `repro/requirements.txt`: `395286726e8046f58cd63a06ea87e2fce8199153ef9da7b57dde5eab9d7e699a`
- `assets/js/report.js`: `451e80c4b7e91bf9fc0c366c94200f2ed41357e3f8e3eca0363800ce020dab3a`
