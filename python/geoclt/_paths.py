from __future__ import annotations

from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def schema_dir() -> Path:
    return package_root() / "schemas"


def schema_path(filename: str) -> Path:
    return schema_dir() / filename
