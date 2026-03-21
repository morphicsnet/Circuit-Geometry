#!/usr/bin/env bash
set -euo pipefail

cargo test -p geoclt-artifacts
cargo test -p geoclt-sidecar

export GEOCLT_REQUIRE_SIDECAR=1
export GEOCLT_SIDECAR_URL="${GEOCLT_SIDECAR_URL:-127.0.0.1:50071}"
export GEOCLT_AUTH_MODE="${GEOCLT_AUTH_MODE:-token}"
export GEOCLT_AUTH_TOKEN="${GEOCLT_AUTH_TOKEN:-geoclt-local-token}"

cargo run -p geoclt-cli -- sidecar serve --addr "${GEOCLT_SIDECAR_URL}" >/tmp/geoclt-sidecar-phase2.log 2>&1 &
SIDECAR_PID=$!
trap 'kill ${SIDECAR_PID} >/dev/null 2>&1 || true' EXIT

# Wait for sidecar to come up.
python3 - <<'PY'
import os
import sys
import time
sys.path.insert(0, "python")
from geoclt.sidecar import connect_sidecar

deadline = time.time() + 20.0
last = None
while time.time() < deadline:
    client = connect_sidecar(os.environ["GEOCLT_SIDECAR_URL"])
    status = client.get_status()
    if status.get("ok"):
        break
    last = status
    time.sleep(0.25)
else:
    raise SystemExit(f"sidecar did not become ready: {last}")
PY

PYTHONPATH=python python3 -m pytest \
  python/tests/test_adapter_contracts.py \
  python/tests/test_transformers_adapter_roundtrip.py \
  python/tests/test_sidecar_roundtrip.py \
  python/tests/test_passive_nonperturbation.py \
  -q

PYTHONPATH=python python3 scripts/generate_phase2_gate_report.py
python3 scripts/assert_phase2_gate_report.py
