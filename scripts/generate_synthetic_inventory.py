from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "outputs" / "synthetic_inventory_report.json"

SCAN_PATHS = [
    REPO_ROOT / "python" / "geoclt",
    REPO_ROOT / "services" / "api",
    REPO_ROOT / "scripts",
    REPO_ROOT / ".github" / "workflows",
    REPO_ROOT / "crates",
    REPO_ROOT / "tests" / "integration",
    REPO_ROOT / "python" / "tests",
]

PATTERN = re.compile(r"\b(placeholder|synthetic|mock|stub)\b", re.IGNORECASE)
VALID_SUFFIXES = {".py", ".rs", ".sh", ".yml", ".yaml", ".toml"}
EXCLUDED_FILES = {
    "scripts/generate_synthetic_inventory.py",
    "scripts/generate_release_readiness_report.py",
}


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


def _classify(path: Path, line: str, token: str) -> tuple[str, str]:
    text = line.strip()
    rel = path.relative_to(REPO_ROOT).as_posix()
    lower = text.lower()
    token = token.lower()

    if rel == "scripts/check_no_placeholders.py":
        return ("keep", "guard-script-token")
    if rel == ".github/workflows/ci-python.yml" and "phase-gate-evidence-pr-stub" in lower:
        return ("keep", "artifact-name-stub-signal")
    if token == "stub" and ("pb2_grpc.sidecarservicestub" in lower or "sidecarservicestub" in lower):
        return ("keep", "grpc-stub-client-type")
    if token == "stub" and "non_stub_backend_used" in lower:
        return ("keep", "assertion-key-not-pipeline-stub")
    if token == "stub" and '"stub" not in profile.runtime_backend' in lower:
        return ("keep", "runtime-backend-guard")
    if token == "synthetic" and "geoclt_use_synthetic" in lower and '"0"' in lower:
        return ("keep", "real-mode-override")
    if token == "placeholder":
        return ("replace", "placeholder-token-not-allowed")
    if token in {"mock", "synthetic"}:
        return ("replace", "synthetic-marker-not-allowed")
    return ("review", "unclassified")


def _scan() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for base in SCAN_PATHS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix not in VALID_SUFFIXES:
                continue
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                match = PATTERN.search(line)
                if match is None:
                    continue
                if path.relative_to(REPO_ROOT).as_posix() in EXCLUDED_FILES:
                    continue
                action, reason = _classify(path, line, match.group(1))
                findings.append(
                    {
                        "path": path.relative_to(REPO_ROOT).as_posix(),
                        "line": line_number,
                        "token": match.group(1).lower(),
                        "action": action,
                        "reason": reason,
                        "snippet": line.strip()[:180],
                    }
                )
    return findings


def main() -> int:
    findings = _scan()
    summary = {"keep": 0, "replace": 0, "review": 0}
    for finding in findings:
        summary[finding["action"]] += 1

    report = {
        "git_commit": _git_commit(),
        "findings": findings,
        "summary": summary,
        "synthetic_inventory_complete": summary["review"] == 0,
        "overall_complete": summary["replace"] == 0 and summary["review"] == 0,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["overall_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
