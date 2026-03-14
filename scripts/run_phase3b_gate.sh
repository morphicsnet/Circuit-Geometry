#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=python python3 -m pytest \
  python/tests/test_api_phase3.py \
  python/tests/test_differential.py \
  python/tests/test_reports.py \
  -q

PYTHONPATH=python python3 scripts/generate_phase3b_gate_report.py
python3 scripts/assert_phase3b_gate_report.py
