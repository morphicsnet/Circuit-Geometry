set shell := ["bash", "-cu"]

build-rust:
    cargo build --workspace

build-python:
    maturin develop

test-rust:
    cargo test --workspace

test-python:
    PYTHONPATH=python python3 -m pytest python/tests -q

lint-rust:
    cargo clippy --workspace --all-targets -- -D warnings

lint-python:
    ruff check python
    mypy python/geoclt

poc:
    PYTHONPATH=python python3 examples/python/factual_retrieval_poc.py

api:
    bash scripts/run_api_local.sh

ui:
    bash scripts/run_ui_local.sh

validate-artifacts:
    bash scripts/validate_artifacts.sh

phase2-gate:
    bash scripts/run_phase2_gate.sh

phase01-gate:
    bash scripts/run_phase01_gate.sh

phase3a-gate:
    bash scripts/run_phase3a_gate.sh

phase3b-gate:
    bash scripts/run_phase3b_gate.sh

phase3-report-pack:
    bash scripts/run_phase3_report_pack.sh

phase4a-gate:
    bash scripts/run_phase4a_gate.sh

phase4a-nightly:
    bash scripts/run_phase4a_nightly_models.sh

phase4b-gate:
    bash scripts/run_phase4b_gate.sh
