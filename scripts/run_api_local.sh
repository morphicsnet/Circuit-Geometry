#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=python uvicorn services.api.app:app --reload
