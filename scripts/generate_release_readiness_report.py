from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "outputs" / "release_readiness_report.json"

PHASE_REPORTS = {
    "phase01": REPO_ROOT / "outputs" / "phase_gate_report.json",
    "phase2": REPO_ROOT / "outputs" / "phase2_gate_report.json",
    "phase3a": REPO_ROOT / "outputs" / "phase3a_gate_report.json",
    "phase3b": REPO_ROOT / "outputs" / "phase3b_gate_report.json",
    "phase4a": REPO_ROOT / "outputs" / "phase4a_gate_report.json",
    "phase4a_nightly": REPO_ROOT / "outputs" / "phase4a_nightly_model_report.json",
    "phase4b": REPO_ROOT / "outputs" / "phase4b_gate_report.json",
}

REQUIRED_REPORT_DIRS = [
    REPO_ROOT / "docs" / "reports" / "phase01",
    REPO_ROOT / "docs" / "reports" / "phase2",
    REPO_ROOT / "docs" / "reports" / "phase3a",
    REPO_ROOT / "docs" / "reports" / "phase3b",
    REPO_ROOT / "docs" / "reports" / "phase4a",
    REPO_ROOT / "docs" / "reports" / "phase4b",
]

INVARIANT_DOC = REPO_ROOT / "docs" / "release" / "release_invariants.md"
INVENTORY_PATH = REPO_ROOT / "outputs" / "synthetic_inventory_report.json"
DESYNTHETIC_STATUS_PATH = REPO_ROOT / "outputs" / "desynthetic_status.json"
EVIDENCE_MANIFEST_PATH = REPO_ROOT / "outputs" / "release_evidence_manifest.json"
RUNBOOK_PATH = REPO_ROOT / "docs" / "release" / "internal_rc_runbook.md"
CHANGELOG_PATH = REPO_ROOT / "docs" / "release" / "CHANGELOG_RC.md"
LIMITATIONS_PATH = REPO_ROOT / "docs" / "release" / "KNOWN_LIMITATIONS.md"
CI_PYTHON_PATH = REPO_ROOT / ".github" / "workflows" / "ci-python.yml"
NIGHTLY_PATH = REPO_ROOT / ".github" / "workflows" / "nightly-phase4-models.yml"
WHEELS_PATH = REPO_ROOT / ".github" / "workflows" / "wheels.yml"
RELEASE_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
RELEASE_SCRIPT_PATH = REPO_ROOT / "scripts" / "release.sh"
VALIDATE_SCRIPT_PATH = REPO_ROOT / "scripts" / "validate_artifacts.sh"


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _phase_status() -> tuple[dict[str, bool], bool]:
    status: dict[str, bool] = {}
    for key, path in PHASE_REPORTS.items():
        payload = _read_json(path)
        status[key] = bool(payload and payload.get("overall_pass") is True)
    return status, all(status.values())


def _doc_contains_all(path: Path, required: list[str]) -> bool:
    text = _read_text(path).lower()
    return bool(text) and all(item.lower() in text for item in required)


def _placeholder_hygiene() -> bool:
    disallowed = []
    for path in [RELEASE_PATH, RELEASE_SCRIPT_PATH, REPO_ROOT / "python" / "geoclt" / "plotting.py", REPO_ROOT / "python" / "geoclt" / "receipts.py"]:
        text = _read_text(path).lower()
        if "placeholder" in text:
            disallowed.append(str(path.relative_to(REPO_ROOT)))
    return len(disallowed) == 0


def main() -> int:
    phase_status, recert_pass = _phase_status()
    inventory = _read_json(INVENTORY_PATH) or {}
    desynthetic_status = _read_json(DESYNTHETIC_STATUS_PATH) or {}
    evidence_manifest = _read_json(EVIDENCE_MANIFEST_PATH) or {}
    ci_text = _read_text(CI_PYTHON_PATH)
    nightly_text = _read_text(NIGHTLY_PATH)
    wheels_text = _read_text(WHEELS_PATH)
    release_text = _read_text(RELEASE_PATH)
    release_script_text = _read_text(RELEASE_SCRIPT_PATH)
    validate_text = _read_text(VALIDATE_SCRIPT_PATH)

    release_baseline_frozen = _doc_contains_all(
        INVARIANT_DOC,
        [
            "mechanism_id",
            "decision_receipt",
            "lane action enum",
            "ids-only differential semantics",
            "canonical hashing",
            "immutable bundle",
        ],
    )
    synthetic_inventory_complete = bool(
        inventory.get("synthetic_inventory_complete") and inventory.get("overall_complete")
    )
    desynthetic_status_green = bool(desynthetic_status.get("overall_pass"))
    rc_merge_policy_enforced = (
        "scripts/validate_artifacts.sh" in ci_text
        and "scripts/check_no_placeholders.py" in validate_text
        and "scripts/run_release_candidate.sh" in release_text
    )
    release_automation_complete = (
        "scripts/run_release_candidate.sh" in release_script_text
        and "release placeholder" not in release_text.lower()
        and "release placeholder" not in release_script_text.lower()
    )
    ci_nightly_reliability = (
        "torch" in nightly_text
        and "transformers" in nightly_text
        and "generate_phase4a_nightly_model_report.py" in nightly_text
        and "phase4a_nightly_model_report.json" in ci_text
    )
    placeholder_hygiene = _placeholder_hygiene()
    packaging_install_ready = (
        "matrix:" in wheels_text
        and "pip install" in wheels_text
        and "cargo run -p geoclt-cli -- version" in wheels_text
    )
    release_docs_present = RUNBOOK_PATH.exists() and CHANGELOG_PATH.exists() and LIMITATIONS_PATH.exists()
    evidence_bundle_present = bool(
        evidence_manifest.get("overall_complete") and evidence_manifest.get("evidence_count", 0) > 0
    )
    report_packs_present = all(path.exists() for path in REQUIRED_REPORT_DIRS)

    delta = {
        "d0_release_baseline_frozen": release_baseline_frozen,
        "d0_synthetic_inventory_complete": synthetic_inventory_complete,
        "d0_desynthetic_status_green": desynthetic_status_green,
        "d0_rc_merge_policy_enforced": rc_merge_policy_enforced,
        "d1_release_automation_complete": release_automation_complete,
        "d2_ci_nightly_reliability": ci_nightly_reliability,
        "d3_placeholder_hygiene": placeholder_hygiene,
        "d4_packaging_install_ready": packaging_install_ready,
        "d4_release_docs_present": release_docs_present,
        "d5_evidence_bundle_present": evidence_bundle_present,
    }
    recert = {
        "r0_phase01_recert_pass": phase_status["phase01"],
        "r1_phase2_recert_pass": phase_status["phase2"],
        "r2_phase3a_recert_pass": phase_status["phase3a"],
        "r2_phase3b_recert_pass": phase_status["phase3b"],
        "r3_phase4a_recert_pass": phase_status["phase4a"],
        "r3_phase4a_nightly_recert_pass": phase_status["phase4a_nightly"],
        "r4_phase4b_recert_pass": phase_status["phase4b"],
        "r5_report_packs_present": report_packs_present,
    }

    report = {
        "git_commit": _git_commit(),
        "release_target": "internal-rc",
        "delta_closeout": delta,
        "full_recertification": recert,
        "phase_reports": phase_status,
    }
    report["overall_pass"] = all(delta.values()) and all(recert.values()) and recert_pass
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
