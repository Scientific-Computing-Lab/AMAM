# AMAM-128 Artifact Consistency Audit (45 Methods)

- Status: **PASS**
- Git commit: `81fd30d3052a873d92679b47f78ca98524925ff6`
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
- `repro/results/deep_survey/deep_general_summary.csv`: `dde4dd4be17f240899ecb395afa701744dac400717f63f013d27ca76588d11a0`
- `repro/results/deep_survey/deep_metallography_summary.csv`: `c1ac71b7a24deb2731c5d694249ac98f62f045a12ca640f0ee7996e106fef206`
- `repro/results/deep_survey/deep_per_image.csv`: `dbd0da87741cb5d086f1a5eeb24ff0acb550ae3697c56534785b59a68f7793ab`
- `repro/results/deep_survey/deep_per_subset.csv`: `68187d722f4db5092bbf1ee254b14b8b6e53485628c110c2d8ab575800efd830`
- `repro/results/deep_survey_multiseed_runs.csv`: `be6b73aba79c7a81d73b700bd3906d7fab4781dc58b47dfa93860a9ab623f5f0`
- `repro/results/deep_survey_multiseed_summary.csv`: `239e69a11ae873504a30f682c6db9385d04a1a1d42a394cd73ac807e89bfc5fe`
- `repro/results/foundation_edge/foundation_edge_summary.csv`: `abce555e4b8e689065c4d91bee9f26e499f94b77ffa4f7ae6435e5384df5ce60`
- `repro/results/foundation_edge/foundation_edge_per_image.csv`: `ef5e15a378032edcad058269a0b0dcda3d05f6657de89c78ba1e7d2167a0bbd8`
- `repro/results/foundation_edge/foundation_edge_per_subset.csv`: `5d3dc6dd34c68b9975b7a2a3096fdcbf0c278a00dc84784ade2c2520e930d2cb`
- `repro/results/classical/benchmark_protocol.json`: `b8bbee2af19c0b89b3f4c119f645c4df578bb7c949d9456b2895c3378a59b8e7`
- `repro/results/deep_survey/deep_protocol.json`: `6e8021540649575699313898957d09bcd3674a77314f80f8e446ab8ccbb378a6`
- `repro/results/foundation_edge/foundation_edge_protocol.json`: `ea6115c8499c8ceac408d95463c2707640274fd298a5687a93a8de7905723495`
- `repro/results/classical/canonical_predictions/manifest.json`: `eadcbe9d2c6dfcb638aef59669fb7af05518851d596f158eb3b655f3ba1f40b7`
- `repro/results/deep_survey_seed17/canonical_predictions/manifest.json`: `caaca3afbc0945bf7999e5390f450df1450abea45e2c48b193c4c0d2f24a8c6c`
- `repro/figures/appendix_preds/panel_metadata.json`: `baf7c3e72c93748c55b12bb432686e2ce0108a01db73ebe1f6bd69e7a1d52eb2`
- `repro/results/model_provenance_manifest.csv`: `65645e1d4c2b61020be590f98661f6b0b465f1b4b81b53c8f5400196d215a22b`
- `assets/data/amam-dataset.json`: `227fc057a460cbc2e63ab8634704b46f4e19256971c4ab616e467d0ff10cfc9c`
- `repro/benchmark/run_deep_survey.py`: `fdbc4e0edd05fa43900328dd1f34f68e831854de1e3cf223283046f5aed8d193`
- `repro/benchmark/aggregate_deep_multiseed.py`: `d042896d426d00a6f0bfd7925b6b34d7d2aca19adc2c0396d9348e8acff846f4`
- `repro/benchmark/plot_benchmark_gap_figure.py`: `05a16516bb06deb39ba59244c092418a47d4fda26b6aa7c83678f43612ce046e`
- `repro/benchmark/canonical_predictions.py`: `19558b5405f4cfef96542748daabbfe6e808d03c5d589752946b656be9611148`
- `repro/benchmark/build_appendix_representative_assets.py`: `b7fca125f5dda5062fe48a237a43312ffa8f4b8acf12bb2d391e472d627a8109`
- `repro/requirements.txt`: `395286726e8046f58cd63a06ea87e2fce8199153ef9da7b57dde5eab9d7e699a`
- `assets/js/report.js`: `3fd96adc4fbd637d3ab461048371204afb3cde011e23d9e356c26d12dc45c9ff`
