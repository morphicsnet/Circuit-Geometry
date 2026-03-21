# Phase 3B Logic Specifications

Gate formula:

`PASS = A AND D AND R`

Where:
- `A` = API/explorer endpoint validity and deterministic endpoint behavior
- `D` = deterministic differential/cohort outputs
- `R` = report bundle validation, stable identity, and deterministic report-pack regeneration

Differential determinism property:

`diff(input_a, input_b)` is stable for repeated identical inputs.

Report identity property:

`bundle_hash = hash(bundle_payload_without_bundle_hash)`.

Report-pack regeneration property:

`render(report_state_n) == render(report_state_n)` for identical gate output payloads.
