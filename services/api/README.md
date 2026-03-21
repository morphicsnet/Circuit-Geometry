# Circuit-Geometry API
> Local FastAPI surface for starting lanes, listing runs, and exporting evidence without dropping into notebooks.

This service is the operator-friendly control surface above the Python workspace. Use it when you want run submission, report export, and determinism checks through HTTP instead of direct SDK calls.

## Fastest path
```bash
export GEOCLT_AUTH_MODE=token
export GEOCLT_AUTH_TOKEN=geoclt-local-token
PYTHONPATH=python uvicorn services.api.app:app --reload
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/runs \
  -H 'content-type: application/json' \
  -d '{"workspace":"runs/factual-retrieval","lane_id":"factual_retrieval.v1","behavior_id":"factual_retrieval","model_id":"gpt2-small"}'
```

## What this service owns
- run submission and listing
- determinism checks for existing runs
- report export and run detail retrieval
- demo and pilot endpoints guarded by bearer auth when token mode is enabled

## Key routes
- `GET /health`
- `GET /runs?workspace=<path>`
- `POST /runs`
- `GET /runs/{run_id}?workspace=<path>`
- `GET /runs/{run_id}/determinism?workspace=<path>`
- `POST /runs/{run_id}/export?workspace=<path>`
- `GET /reports/{run_id}?workspace=<path>`
- `POST /demo/submit` and related demo/pilot routes in token mode

## When to use it
- Use the API when you need a thin local control plane for scripts, demos, or the browser UI.
- Use the Python workspace when you want direct orchestration inside code.
- Use the CLI when you want artifact validation and benchmark commands without running a server.

## Go next
- Root guide: [Circuit-Geometry](../../README.md)
- Browser surface: [UI README](../ui/README.md)
- Sidecar boundary: [Sidecar README](../sidecar/README.md)
