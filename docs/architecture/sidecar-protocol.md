# Sidecar Protocol

Primary inference emits activation chunks to the sidecar over a trace lifecycle contract.

## Lifecycle messages

- `TraceStart`
- `ActivationChunk`
- `TraceEnd`
- `TraceAbort`

## Artifact delivery

- `ArtifactInline` for small bundles
- `ArtifactBundleRef` for store-backed bundles

## Control messages

- `Ack`
- `Nack`
- `BackpressureSignal`
- `ServerStatus`

## Duplicate chunk rule

For identical `trace_id + chunk_idempotency_key`:

- byte-identical payload: accept as no-op duplicate
- different payload: hard fail trace

## Trace state machine

`INIT -> STARTED -> STREAMING -> ENDED -> VALIDATED -> PERSISTED -> FINALIZED`

Failure branches:

- `ABORTED`
- `FAILED`
