#!/usr/bin/env bash
set -euo pipefail

python3 scripts/generate_phase_gate_report.py
python3 scripts/assert_phase01_gate_report.py
