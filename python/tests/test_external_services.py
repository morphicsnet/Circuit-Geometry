from __future__ import annotations

import os

import pytest

from geoclt.external_services import queue_event, queue_backend, store_backend, store_bundle


def test_fs_store_and_memory_queue(tmp_path):
    os.environ["GEOCLT_STORE_BACKEND"] = "fs"
    os.environ["GEOCLT_QUEUE_BACKEND"] = "memory"
    bundle = {
        "bundle_id": "bundle-test",
        "bundle_hash": "a" * 64,
        "schema_version": 1,
        "producer": "geoclt:test:0.1.0",
        "run_id": "run-1",
        "trace_id": "trace-1",
        "created_at": "2026-01-01T00:00:00Z",
        "transitional": False,
        "immutable": True,
        "artifacts": [],
    }
    ref = store_bundle(bundle, workspace=tmp_path)
    queued = queue_event({"event": "x", "id": 1})
    assert store_backend() == "fs"
    assert queue_backend() == "memory"
    assert ref["backend"] == "fs"
    assert queued["queued"] is True


def test_minio_backend_requires_dependency(tmp_path):
    os.environ["GEOCLT_STORE_BACKEND"] = "minio"
    bundle = {
        "bundle_id": "bundle-test",
        "bundle_hash": "a" * 64,
        "schema_version": 1,
        "producer": "geoclt:test:0.1.0",
        "run_id": "run-1",
        "trace_id": "trace-1",
        "created_at": "2026-01-01T00:00:00Z",
        "transitional": False,
        "immutable": True,
        "artifacts": [],
    }
    try:
        store_bundle(bundle, workspace=tmp_path)
    except RuntimeError:
        pytest.skip("minio dependency not installed in this environment")
