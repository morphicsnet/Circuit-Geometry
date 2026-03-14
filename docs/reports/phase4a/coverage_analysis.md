# Phase 4A Coverage Analysis

Fully exercised in gate path:

- lane registry + scorecard validation across all three Phase 4A lanes
- model profile freeze checks
- run config record validation
- deterministic replay checks over immutable manifest + run config
- canonical decision receipt + bundle emission
- fallback counters (`policy_fallback`, `model_fallback`, `operator_fallback`)
- latency/memory/success/fallback budget checks

Partially exercised:

- optional multimodal runner
- long-tail golden dataset ambiguity handling at scale
- real model divergence analysis beyond nightly shared-lane smoke path
