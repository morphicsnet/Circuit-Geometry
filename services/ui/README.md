# Circuit-Geometry UI
> Lightweight mechanism explorer for running lanes, selecting workspaces, and inspecting exported artifacts in the browser.

The UI is deliberately simple: it is the fastest visual path into run metadata, determinism checks, and exported report bundles.

## Fastest path
```bash
make api
make ui
# open http://127.0.0.1:4173
```

Or run manually:
```bash
PYTHONPATH=python uvicorn services.api.app:app --reload
cd services/ui
npm run dev
```

## What you can do today
- submit a benchmark lane from browser controls
- list and select runs in a workspace
- inspect run metadata and key artifact summaries
- trigger determinism checks for a selected run
- export a report bundle for a selected run

## Why this exists
The UI is not meant to replace the SDK or CLI. It exists so an operator can answer “what happened in that run?” without opening Python or chasing artifact files by hand.

## Go next
- Root guide: [Circuit-Geometry](../../README.md)
- API surface: [API README](../api/README.md)
- Phase reports: [docs/reports/](../../docs/reports/)
