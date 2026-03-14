#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=python python3 -m pytest \
  python/tests/test_phase4_contracts.py \
  python/tests/test_phase4_demo_api.py \
  -q

PYTHONPATH=python python3 scripts/generate_phase4a_gate_report.py
python3 scripts/assert_phase4a_gate_report.py
python3 scripts/generate_phase4_report_pack.py --phase phase4a
