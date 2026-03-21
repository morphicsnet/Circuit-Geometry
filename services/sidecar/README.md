# Circuit-Geometry Sidecar Service
> Phase-2 runtime boundary for trace lifecycle, streaming activations, and bundle delivery.

This directory marks the sidecar-first runtime surface for Circuit-Geometry. The repo already includes the protocol, tests, and local scripts that define how traces start, stream, validate, persist, and finalize.

## Fastest path
```bash
bash scripts/run_sidecar_local.sh
PYTHONPATH=python pytest python/tests/test_sidecar_roundtrip.py -q
```

## What the sidecar owns
- trace lifecycle semantics: `INIT -> STARTED -> STREAMING -> ENDED -> VALIDATED -> PERSISTED -> FINALIZED`
- duplicate-chunk handling and hard-fail conflict rules
- delivery of inline artifacts or store-backed bundle references
- backpressure and status control messages for runtime hygiene

## Read this first
- Protocol: [docs/architecture/sidecar-protocol.md](../../docs/architecture/sidecar-protocol.md)
- Lifecycle: [docs/architecture/trace-lifecycle.md](../../docs/architecture/trace-lifecycle.md)
- Protobuf contract: [proto/sidecar.proto](../../proto/sidecar.proto)

## Current status
- This surface is intentionally narrower than the root workspace, because it is the runtime boundary rather than the full assurance product.
- The repo contains roundtrip tests and local scripts today; production deployment hardening is the next step.

## Go next
- Root guide: [Circuit-Geometry](../../README.md)
- API surface: [API README](../api/README.md)
- Benchmark/report evidence: [Phase 4B pack](../../docs/reports/phase4b/README.md)
