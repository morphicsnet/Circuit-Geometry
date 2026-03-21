# Internal RC Known Limitations

## Validation Modes

- PR CI uses deterministic gate execution and includes Phase 4A stub-gated path.
- Nightly/manual validation runs real-model Phase 4A evidence separately.
- RC sign-off requires both paths green.

## Runtime Scope

- Phase 4 remains bounded validation, not autonomous production operation.
- SQLite + filesystem storage are retained for RC scope.

## Optional Adapters

- vLLM and llama.cpp adapters remain optional runtime integrations.
- baseline conformance is enforced with the primary Transformers adapter path.
