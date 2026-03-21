.PHONY: all build test lint poc api ui phase01-gate phase2-gate phase3a-gate phase3b-gate phase3-report-pack phase4a-gate phase4a-nightly phase4b-gate phase4-report-pack release-candidate release

all: build test

build:
	cargo build --workspace
	maturin develop

test:
	cargo test --workspace
	PYTHONPATH=python python3 -m pytest python/tests -q

lint:
	cargo clippy --workspace --all-targets -- -D warnings
	ruff check python
	mypy python/geoclt

poc:
	PYTHONPATH=python python3 examples/python/factual_retrieval_poc.py

api:
	bash scripts/run_api_local.sh

ui:
	bash scripts/run_ui_local.sh

phase01-gate:
	bash scripts/run_phase01_gate.sh

phase2-gate:
	bash scripts/run_phase2_gate.sh

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

phase4-report-pack:
	bash scripts/run_phase4_report_pack.sh

release-candidate:
	bash scripts/run_release_candidate.sh

release:
	bash scripts/release.sh
