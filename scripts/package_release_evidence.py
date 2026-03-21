from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "release_evidence"
MANIFEST_PATH = REPO_ROOT / "outputs" / "release_evidence_manifest.json"

REPORT_FILES = [
    "determinism_evidence.json",
    "phase_gate_report.json",
    "phase2_gate_report.json",
    "phase3a_gate_report.json",
    "phase3b_gate_report.json",
    "phase4a_gate_report.json",
    "phase4a_nightly_model_report.json",
    "phase4b_gate_report.json",
    "synthetic_inventory_report.json",
    "desynthetic_status.json",
]

OPTIONAL_REPORT_FILES = [
    "release_readiness_report.json",
]

REPORT_DIRS = [
    "docs/reports/phase01",
    "docs/reports/phase2",
    "docs/reports/phase3a",
    "docs/reports/phase3b",
    "docs/reports/phase4a",
    "docs/reports/phase4b",
]


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


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(p for p in path.rglob("*") if p.is_file()):
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(file_path.read_bytes())
    return digest.hexdigest()


def _copy_files() -> tuple[list[dict[str, Any]], list[str]]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[dict[str, Any]] = []
    missing: list[str] = []

    for rel in REPORT_FILES:
        source = REPO_ROOT / "outputs" / rel
        if not source.exists():
            missing.append(f"outputs/{rel}")
            continue
        target = OUTPUT_DIR / rel
        shutil.copy2(source, target)
        copied.append(
            {
                "path": f"outputs/{rel}",
                "size_bytes": source.stat().st_size,
                "sha256": _sha256(source),
            }
        )
    for rel in OPTIONAL_REPORT_FILES:
        source = REPO_ROOT / "outputs" / rel
        if not source.exists():
            continue
        target = OUTPUT_DIR / rel
        shutil.copy2(source, target)
        copied.append(
            {
                "path": f"outputs/{rel}",
                "size_bytes": source.stat().st_size,
                "sha256": _sha256(source),
            }
        )
    for rel in REPORT_DIRS:
        source_dir = REPO_ROOT / rel
        if not source_dir.exists():
            missing.append(rel)
            continue
        target_dir = OUTPUT_DIR / rel.replace("/", "__")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
        copied.append(
            {
                "path": rel,
                "size_bytes": sum(p.stat().st_size for p in source_dir.rglob("*") if p.is_file()),
                "sha256": _tree_sha256(source_dir),
            }
        )
    return copied, missing


def main() -> int:
    copied, missing = _copy_files()
    manifest = {
        "git_commit": _git_commit(),
        "evidence_count": len(copied),
        "missing": missing,
        "evidence": copied,
        "overall_complete": len(missing) == 0,
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["overall_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
