#!/usr/bin/env bash
set -euo pipefail

tmp_lane="$(mktemp)"
trap 'rm -f "${tmp_lane}"' EXIT
cat > "${tmp_lane}" <<'JSON'
{
  "lane_id": "factual_retrieval.v1",
  "behavior_id": "factual_retrieval",
  "intervention_delta_threshold": 0.1,
  "synergy_threshold": 0.05,
  "chart_stability_threshold": 0.7,
  "transport_coherence_threshold": 0.7,
  "baseline_margin_threshold": 0.05
}
JSON

cargo run -p geoclt-cli -- validate-artifacts \
  --artifact "${tmp_lane}" \
  --schema schemas/benchmark_lane.schema.json

python3 scripts/check_no_placeholders.py
python3 scripts/check_determinism.py
python3 scripts/generate_phase_gate_report.py
python3 scripts/assert_phase01_gate_report.py
PYTHONPATH=python python3 scripts/generate_phase2_gate_report.py
python3 scripts/assert_phase2_gate_report.py
python3 scripts/check_lane_registry_immutability.py
PYTHONPATH=python python3 scripts/generate_phase3a_gate_report.py
python3 scripts/assert_phase3a_gate_report.py
PYTHONPATH=python python3 scripts/generate_phase3b_gate_report.py
python3 scripts/assert_phase3b_gate_report.py
bash scripts/run_phase4a_gate.sh
bash scripts/run_phase4a_nightly_models.sh
bash scripts/run_phase4b_gate.sh
