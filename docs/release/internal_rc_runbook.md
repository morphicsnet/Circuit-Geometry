# Internal RC Runbook

## Prerequisites

- Python 3.11
- Rust stable toolchain
- `maturin`, `pytest`, `torch`, `transformers`, `grpcio`, `grpcio-tools`

## Default Operational Environments

```bash
export GEOCLT_REQUIRE_SIDECAR=1
export GEOCLT_MODEL_MODE=real
export GEOCLT_AUTH_MODE=token
export GEOCLT_AUTH_TOKEN=geoclt-local-token
export GEOCLT_BUNDLE_SIGNING=hmac
export GEOCLT_STORE_BACKEND=fs
export GEOCLT_QUEUE_BACKEND=memory
```

## Build + Install

```bash
maturin develop
cargo build --workspace
```

## Full Gate Chain

```bash
bash scripts/run_release_candidate.sh
```

This executes:

1. synthetic/placeholder inventory generation
2. placeholder guard
3. full phase chain (`validate_artifacts.sh`)
4. phase 3/4 report-pack refresh
5. evidence packaging
6. release readiness report generation + assertion

## Output Artifacts

- `outputs/release_readiness_report.json`
- `outputs/release_evidence_manifest.json`
- `outputs/synthetic_inventory_report.json`
- all phase gate reports under `outputs/`
- all report packs under `docs/reports/`

## Rollback Procedure

If release gates regress:

1. stop RC cut
2. inspect failing phase report in `outputs/`
3. fix regression and rerun `bash scripts/run_release_candidate.sh`
4. only re-cut RC after readiness assertions pass
