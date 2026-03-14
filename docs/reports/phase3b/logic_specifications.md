# Phase 3B Logic Specifications

Gate formula:

`PASS = A AND D AND R`

Where:
- `A` = API/explorer endpoint validity and replay behavior
- `D` = deterministic differential/cohort outputs
- `R` = report bundle validation and stable identity

Differential determinism property:

`diff(input_a, input_b)` is stable for repeated identical inputs.

Report identity property:

`bundle_hash = hash(bundle_payload_without_bundle_hash)`.
