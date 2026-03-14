# API Service

Local FastAPI surface for Phase 1 workflow automation.

## Run locally

```bash
PYTHONPATH=python uvicorn services.api.app:app --reload
```

## Endpoints

- `GET /health`
- `GET /runs?workspace=<path>`
- `POST /runs`
- `GET /runs/{run_id}?workspace=<path>`
- `GET /runs/{run_id}/determinism?workspace=<path>`
- `POST /runs/{run_id}/export?workspace=<path>`
- `GET /reports/{run_id}?workspace=<path>`
