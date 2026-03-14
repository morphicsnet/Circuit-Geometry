#!/usr/bin/env bash
set -euo pipefail

python3 scripts/assert_phase4a_gate_report.py
python3 scripts/assert_phase4a_nightly_model_report.py

PYTHONPATH=python python3 -m pytest \
  python/tests/test_phase4_pilot_api.py \
  -q

PYTHONPATH=python python3 scripts/generate_phase4b_gate_report.py
python3 scripts/assert_phase4b_gate_report.py
python3 scripts/generate_phase4_report_pack.py --phase phase4b
