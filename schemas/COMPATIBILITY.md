# Compatibility Policy

Geo-CLT Phase 2 enforces `strict_n_n_minus_1` compatibility.

- `N` (current schema version): accepted.
- `N-1`: accepted.
- `N-2` and below: rejected.
- Mixed-version artifact bundles: rejected by default.
- Mixed-version bundles may only be accepted when `transitional=true` is explicitly set.

This policy is enforced by the Rust artifact compatibility checker and mirrored in Python tests.
