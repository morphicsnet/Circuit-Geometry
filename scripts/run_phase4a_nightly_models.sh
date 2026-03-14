#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=python python3 scripts/generate_phase4a_nightly_model_report.py
python3 scripts/assert_phase4a_nightly_model_report.py
python3 scripts/generate_phase4_report_pack.py --phase phase4a
