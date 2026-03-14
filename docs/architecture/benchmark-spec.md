# Benchmark Spec

Phase 0/1 benchmark contract is fixture-driven and hard-fail in CI.

## Lane

- `lane_id`: `factual_retrieval.v1`
- `behavior_id`: `factual_retrieval`
- thresholds:
  - intervention delta: `0.10`
  - synergy: `0.05`
  - chart stability: `0.70`
  - transport coherence: `0.70`
  - baseline margin: `0.05`

## Baselines

Baseline IDs are fixed for Phase 0/1:

- `single_sae`
- `ensemble_sae`
- `pairwise_graph`
- `geometry_free`

## Falsifiers

- `pairwise_sufficiency_triggered`
- `chart_fragility_triggered`
- `transport_irrelevance_triggered`
- `geometry_non_predictiveness_triggered`
- `spurious_synergy_triggered`

`any_triggered` is true if any falsifier above is true.

## Conformance Mapping

- `conformant`: admission passes, baseline margin passes, no falsifiers.
- `provisional`: admission passes and baseline margin passes, but one or more falsifiers.
- `rejected`: all other outcomes.

## Fixture Source Of Truth

- manifest: `tests/fixtures/factual_retrieval_v1/fixture_manifest.json`
- fixture bundles: `tests/fixtures/factual_retrieval_v1/*.json`
