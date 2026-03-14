# UI

Local Mechanism Explorer UI for Phase 1 run/inspect/export flows.

## Run locally

1. Start API:
```bash
PYTHONPATH=python uvicorn services.api.app:app --reload
```
2. Start UI:
```bash
cd services/ui
npm run dev
```
3. Open `http://127.0.0.1:4173`

## Current capabilities

- Run benchmark lane from browser controls
- List and select runs in a workspace
- Inspect run metadata and key artifact summaries
- Check rerun determinism for selected run
- Export selected run report
