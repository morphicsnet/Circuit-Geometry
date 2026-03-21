# Phase 3B Coverage Analysis

Fully exercised in gate path:
- trace + lane evaluation API flows
- deterministic `/trace`, `/evaluate_lane`, `/decision_receipt/{id}`, `/analysis/report` checks
- decision receipt retrieval API flow
- mechanism lookup API flow
- deterministic differential and cohort summaries
- report bundle hash stability and identity validation
- deterministic phase3 report-pack regeneration

Partially exercised:
- large-cohort aggregate performance
- UI rendering behavior under heavy replay workloads
