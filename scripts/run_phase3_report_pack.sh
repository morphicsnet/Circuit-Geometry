#!/usr/bin/env bash
set -euo pipefail

bash scripts/run_phase3a_gate.sh
bash scripts/run_phase3b_gate.sh
python3 scripts/generate_phase3_report_pack.py
