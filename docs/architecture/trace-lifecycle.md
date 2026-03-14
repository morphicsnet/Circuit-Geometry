# Trace Lifecycle

This document defines the normative sidecar trace lifecycle for Phase 2.

## States

- `INIT`
- `STARTED`
- `STREAMING`
- `ENDED`
- `VALIDATED`
- `PERSISTED`
- `FINALIZED`

Failure branches:

- `STARTED` or `STREAMING` -> `ABORTED`
- `STARTED`, `STREAMING`, or `ENDED` -> `FAILED`

## Transition Rules

- `TraceStart` moves `INIT` -> `STARTED`.
- First `ActivationChunk` moves `STARTED` -> `STREAMING`.
- Additional chunks remain in `STREAMING`.
- `TraceEnd` moves `STARTED` or `STREAMING` -> `ENDED`.
- Validation success moves `ENDED` -> `VALIDATED`.
- Persistence success moves `VALIDATED` -> `PERSISTED`.
- Bundle finalization moves `PERSISTED` -> `FINALIZED`.
- `TraceAbort` moves `STARTED` or `STREAMING` -> `ABORTED`.
- Any lifecycle or payload conflict moves trace to `FAILED`.

## Duplicate Chunk Semantics

For identical `trace_id` and `chunk_idempotency_key`:

- byte-identical payload: accept as duplicate no-op
- different payload: hard fail and mark trace `FAILED`
