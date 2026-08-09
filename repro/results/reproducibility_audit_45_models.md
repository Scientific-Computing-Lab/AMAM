# AMAM-128 Artifact Consistency Audit (45 Methods)

- Status: **PASS**
- Git commit: `c12f8ce8b5f3a698b6ed6fee17e9c7d0fa3891c4`
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

## Key Artifacts (SHA256)
- `repro/results/classical/benchmark_summary.csv`: `1564cb9395988534bf05ac0e7877a624d5677c63fd86e4330da62cc9cff870b2`
- `repro/results/classical/benchmark_raw_per_image.csv`: `92c1751ac2d59cde900b4c206d3f5960e8d76729694ba49298c23f30e2aebb78`
- `repro/results/classical/benchmark_per_subset.csv`: `ef3e8b9495d039e33dd93485d3d00b24d319dde20f4598141272940f9721605c`
- `repro/results/deep_survey/deep_general_summary.csv`: `065659842a23d10e5d1a6c639f3c5208ad9932179f3a00c76d90d9631782cf1a`
- `repro/results/deep_survey/deep_metallography_summary.csv`: `246cbfc43599a63b40d43d892a60c698349cf67a6b444ad4f39a61d50e847e69`
- `repro/results/deep_survey/deep_per_image.csv`: `64ee16dc36ee3ca63f4d7cafecd72303b00e92ec97eb69a26981454344d46c2e`
- `repro/results/deep_survey/deep_per_subset.csv`: `58094a1cec95f74c1270681d6491763de00a7bcec9bc698af705e22d280392be`
- `repro/results/deep_survey_multiseed_runs.csv`: `294ce1b533d73e4278b69560c6f8a1fe500ba8055f15421cc6f9f1ad80b0e968`
- `repro/results/deep_survey_multiseed_summary.csv`: `93abf428c404ba1ec4c7695ea2059fc0d5b9f8ffb6e693dae49593f098ae949f`
- `repro/results/foundation_edge/foundation_edge_summary.csv`: `6eaf32e714137dfc0ccdeed4f938a1c1657631ea7ef16d8baf5ffddad2dcbfce`
- `repro/results/foundation_edge/foundation_edge_per_image.csv`: `5974a5e775af8298e6d1f8b1a00194ef1e7ac70bf9de9419e84f1efe51b5bb0a`
- `repro/results/foundation_edge/foundation_edge_per_subset.csv`: `b251b3cb9689bcf977619d1ba7d8904aed3ee47b84f65ad75fad99bc9082fcc8`
- `repro/results/classical/benchmark_protocol.json`: `191f97b9b1d0b7c1ef79b3b3beb345480194d41584ecf3a178086e31e9380382`
- `repro/results/deep_survey/deep_protocol.json`: `1ceef6901f316a4ae8b21d678aa12b596b80f887152dea4eaf3bd0a53a04f79a`
- `repro/results/foundation_edge/foundation_edge_protocol.json`: `e34cd5510fa0ba6025a97eb756edc38d6b60ba5fb8cc2a4653b662f13b34f670`
- `repro/results/model_provenance_manifest.csv`: `e763275cc664ff5ea7d009aa5a1f485c18e46261454ad0f7af21cd6e3dcbe3fe`
- `assets/data/amam-dataset.json`: `7ea757a15626a00ecd03faac727a98deea836390ffd499ea78c910f65329c2cd`
- `repro/benchmark/run_deep_survey.py`: `8593c4331c8c48fd6331cd0d506e432545bc84d3cc8ddbbb7d4705a674a86c97`
- `repro/benchmark/aggregate_deep_multiseed.py`: `f6ca85d4bb96608f4dadb2492f6e3788851db172b71bd999ce0d0c10f013f142`
- `repro/benchmark/plot_benchmark_gap_figure.py`: `30a6f7c1e1885267de03662879373aea3b8ca465b963572dd6843311af49d773`
- `repro/requirements.txt`: `395286726e8046f58cd63a06ea87e2fce8199153ef9da7b57dde5eab9d7e699a`
- `assets/js/report.js`: `b68eda0777600b5f695929198eb8140e4590755d6e61626cb7df92feba90ed44`
