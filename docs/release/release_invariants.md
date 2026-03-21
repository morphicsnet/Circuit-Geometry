# Release Baseline Freeze (Internal RC)

This document is the frozen contract for Internal RC release readiness.

## Frozen Invariants

1. `mechanism_id` derivation is immutable and must remain deterministic.
2. `decision_receipt` core semantics and required fields are immutable.
3. Lane action enum is fixed to:
   - `allow`
   - `allow_with_review`
   - `route_to_fallback`
   - `block`
   - `escalate`
4. IDs-only differential semantics are mandatory:
   - `mechanism_id`
   - `mechanism_class_id`
   - `mechanism_family_id`
5. Canonical hashing remains RFC8785-style and content-hash based.
6. Immutable bundle semantics remain enforced across all phase artifacts.

## Merge Policy Lock

- No merge is release-ready if any phase gate fails.
- No merge is release-ready if placeholder guard fails.
- `scripts/validate_artifacts.sh` is the required gate chain entrypoint.
