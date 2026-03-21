#!/usr/bin/env bash
set -euo pipefail

python3 scripts/generate_synthetic_inventory.py
python3 scripts/generate_desynthetic_status.py || true
python3 scripts/check_no_placeholders.py
bash scripts/validate_artifacts.sh
python3 scripts/generate_desynthetic_status.py
python3 scripts/generate_phase3_report_pack.py
python3 scripts/generate_phase4_report_pack.py --phase all
python3 scripts/package_release_evidence.py
python3 scripts/generate_release_readiness_report.py
python3 scripts/assert_release_readiness_report.py
python3 scripts/package_release_evidence.py
