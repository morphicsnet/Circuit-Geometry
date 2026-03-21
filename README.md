# Geo-CLT

Geo-CLT is a Rust-core, Python-facing framework for mechanism discovery, mechanism admission, and benchmarked mechanistic assurance.

## Core ideas
- Rust core for deterministic schemas, kernels, validation, sidecar runtime, and benchmark enforcement
- Python workspace for model integration, orchestration, and user ergonomics
- canonical mechanism object: chart-consistent causal hyperedge event
- canonical admitted mechanism: causally necessary, synergistic, chart-stable, transport-coherent hyperpath

## Quickstart
```bash
cargo test --workspace
PYTHONPATH=python python3 -m pytest python/tests -q
PYTHONPATH=python python3 examples/python/factual_retrieval_poc.py
```

## CLI
```bash
cargo run -p geoclt-cli -- version
cargo run -p geoclt-cli -- run-profile
cargo run -p geoclt-cli -- benchmark --lane-id factual_retrieval.v1 --behavior-id factual_retrieval
cargo run -p geoclt-cli -- validate-artifacts --artifact /tmp/geoclt-benchmark-lane.json --schema schemas/benchmark_lane.schema.json
```

## Python Workspace
```python
from geoclt import Workspace, BenchmarkLaneConfig

ws = Workspace.create("runs/factual-retrieval")
ws.attach_model("gpt2-small")
ws.fit_atlas(profile="factual_retrieval")
ws.fit_transport()
ws.propose_events()
ws.verify_mechanisms()
run = ws.run_benchmark(BenchmarkLaneConfig(
    lane_id="factual_retrieval.v1",
    behavior_id="factual_retrieval",
))
ws.export_report(run["run_id"])
```

## Local API
```bash
export GEOCLT_AUTH_MODE=token
export GEOCLT_AUTH_TOKEN=geoclt-local-token
PYTHONPATH=python uvicorn services.api.app:app --reload
curl "http://127.0.0.1:8000/health"
curl -X POST "http://127.0.0.1:8000/runs" \
  -H "content-type: application/json" \
  -d '{"workspace":"runs/factual-retrieval","lane_id":"factual_retrieval.v1","behavior_id":"factual_retrieval","model_id":"gpt2-small"}'
curl "http://127.0.0.1:8000/runs?workspace=runs/factual-retrieval"
curl "http://127.0.0.1:8000/runs/<run_id>/determinism?workspace=runs/factual-retrieval"
```

Demo/pilot endpoints require bearer auth when `GEOCLT_AUTH_MODE=token`:
```bash
curl -X POST "http://127.0.0.1:8000/demo/submit" \
  -H "authorization: Bearer geoclt-local-token" \
  -H "content-type: application/json" \
  -d '{"workspace":"runs/phase4-demo","lane_id":"realworld-claims-triage.v1","requested_action":"allow"}'
```

## Local UI
```bash
make api
make ui
```

## Phase Gates
```bash
# Full phase validation chain (0 -> 4B)
bash scripts/validate_artifacts.sh

# Phase 4A CI stub gate
bash scripts/run_phase4a_gate.sh

# Phase 4A nightly/manual model validation
bash scripts/run_phase4a_nightly_models.sh

# Phase 4B bounded pilot gate (requires 4A reports present)
bash scripts/run_phase4b_gate.sh

# Refresh all Phase 4 report pack docs
bash scripts/run_phase4_report_pack.sh

# Internal RC readiness chain
bash scripts/run_release_candidate.sh

# Internal RC cut (archive + optional tag via GEOCLT_RC_TAG)
bash scripts/release.sh
```

## Real Deterministic Mode (Phase 0/1)
Phase 0/1 gate scripts now always run the real deterministic activation flow using Transformers (`gpt2` backend for `gpt2-small` alias).

```bash
# Optional one-time local cache warmup
python3 - <<'PY'
from transformers import AutoTokenizer, AutoModelForCausalLM
AutoTokenizer.from_pretrained("gpt2")
AutoModelForCausalLM.from_pretrained("gpt2")
print("gpt2 cache warm")
PY

# Real deterministic evidence
python3 scripts/check_determinism.py
python3 scripts/generate_phase_gate_report.py
python3 scripts/assert_phase01_gate_report.py
```
