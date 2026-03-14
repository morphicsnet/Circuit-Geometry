from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LANE_ROOT = REPO_ROOT / "crates" / "geoclt-benchmark" / "lanes"
LOCK_PATH = LANE_ROOT / "IMMUTABLE_LOCK.json"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    locked_files: dict[str, str] = lock.get("locked_files", {})

    mismatches: list[str] = []
    for relative, expected in locked_files.items():
        file_path = LANE_ROOT / relative
        if not file_path.exists():
            mismatches.append(f"missing locked lane file: {relative}")
            continue
        actual = file_hash(file_path)
        if actual != expected:
            mismatches.append(f"lane file hash mismatch: {relative}")

    if mismatches:
        for mismatch in mismatches:
            print(mismatch)
        return 1

    print("lane registry immutable lock check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
