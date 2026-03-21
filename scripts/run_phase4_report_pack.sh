#!/usr/bin/env bash
set -euo pipefail

bash scripts/run_phase4a_gate.sh
bash scripts/run_phase4a_nightly_models.sh
bash scripts/run_phase4b_gate.sh
python3 scripts/generate_phase4_report_pack.py --phase all
