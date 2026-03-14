# Phase 3A Traceability

| Requirement | Assertion | Source |
|---|---|---|
| Stable mechanism identity | `mechanism_identity_stable`, `mechanism_id_deterministic` | `scripts/generate_phase3a_gate_report.py` |
| Deterministic mechanism families | `cluster_deterministic`, `cluster_identity_deterministic` | `scripts/generate_phase3a_gate_report.py` |
| Receipt as immutable audit object | `decision_receipt_complete`, `receipt_hash_stable`, `artifact_bundle_linkage_valid` | `python/geoclt/receipts.py`, gate script |
| Lane policy contract validity | `lane_registry_loaded`, `lane_thresholds_valid`, `lane_falsifiers_valid`, `lane_registry_immutable` | lane files + lock + gate script |
| Deterministic policy output | `policy_evaluation_deterministic` | gate script |
