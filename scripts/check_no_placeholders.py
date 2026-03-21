from __future__ import annotations

from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
CHECK_PATHS = [
    REPO_ROOT / "python" / "geoclt",
    REPO_ROOT / "services" / "api",
    REPO_ROOT / "scripts",
    REPO_ROOT / ".github" / "workflows",
    REPO_ROOT / "tests" / "integration",
    REPO_ROOT / "python" / "tests",
    REPO_ROOT / "crates" / "geoclt-benchmark" / "tests",
]
PATTERNS = [
    re.compile(r"\bplaceholder\b", re.IGNORECASE),
    re.compile(r"assert!\s*\(\s*true\s*\)"),
]
SELF_PATH = Path(__file__).resolve()
EXCLUDED_PATHS = {
    Path("scripts/check_no_placeholders.py"),
    Path("scripts/generate_synthetic_inventory.py"),
    Path("scripts/generate_release_readiness_report.py"),
}


def main() -> int:
    violations: list[str] = []
    for base in CHECK_PATHS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(REPO_ROOT)
            if path.resolve() == SELF_PATH or rel in EXCLUDED_PATHS:
                continue
            if path.suffix not in {".py", ".rs", ".sh", ".yml", ".yaml"}:
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in PATTERNS:
                if pattern.search(text):
                    violations.append(f"{rel} matches {pattern.pattern}")

    if violations:
        print("placeholder guard failed:")
        for violation in violations:
            print(f"- {violation}")
        return 1

    print("placeholder guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
