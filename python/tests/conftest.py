from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _default_external_backends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEOCLT_STORE_BACKEND", "fs")
    monkeypatch.setenv("GEOCLT_QUEUE_BACKEND", "memory")
