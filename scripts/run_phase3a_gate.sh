#!/usr/bin/env bash
set -euo pipefail

cargo test -p geoclt-canonicalize
cargo test -p geoclt-benchmark
cargo test -p geoclt-runtime

PYTHONPATH=python python3 -m pytest \
  python/tests/test_mechanisms.py \
  python/tests/test_receipts.py \
  -q

python3 scripts/check_lane_registry_immutability.py
PYTHONPATH=python python3 scripts/generate_phase3a_gate_report.py
python3 scripts/assert_phase3a_gate_report.py
