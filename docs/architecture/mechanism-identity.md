# Mechanism Identity

Phase 2 establishes deterministic artifact identity and canonical hashing so Phase 3 can enforce mechanism identity stability.

Mechanism identity drift risks:

- unstable IDs across runs
- unstable IDs across chart substitutions
- unstable IDs across schema migration with unchanged semantics

Phase 3A must build canonical mechanism identity on top of the Phase 2 artifact identity contract.
