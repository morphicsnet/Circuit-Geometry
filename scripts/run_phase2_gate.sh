#!/usr/bin/env bash
set -euo pipefail

cargo test -p geoclt-artifacts
cargo test -p geoclt-sidecar

PYTHONPATH=python python3 -m pytest \
  python/tests/test_adapter_contracts.py \
  python/tests/test_mock_adapter_roundtrip.py \
  python/tests/test_sidecar_roundtrip.py \
  python/tests/test_passive_nonperturbation.py \
  -q

PYTHONPATH=python python3 scripts/generate_phase2_gate_report.py
python3 scripts/assert_phase2_gate_report.py
