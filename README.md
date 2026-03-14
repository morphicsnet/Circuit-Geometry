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
PYTHONPATH=python uvicorn services.api.app:app --reload
curl "http://127.0.0.1:8000/health"
curl -X POST "http://127.0.0.1:8000/runs" \
  -H "content-type: application/json" \
  -d '{"workspace":"runs/factual-retrieval","lane_id":"factual_retrieval.v1","behavior_id":"factual_retrieval","model_id":"gpt2-small"}'
curl "http://127.0.0.1:8000/runs?workspace=runs/factual-retrieval"
curl "http://127.0.0.1:8000/runs/<run_id>/determinism?workspace=runs/factual-retrieval"
```

## Local UI
```bash
make api
make ui
```
