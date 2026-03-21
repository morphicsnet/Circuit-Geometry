import pytest

from geoclt.artifacts import (
    artifact_store_path,
    build_artifact_bundle,
    build_artifact_entry,
    derive_artifact_id,
    stable_hash,
    validate_instance,
    verify_bundle_manifest,
    write_bundle_to_store,
    write_json,
    write_json_with_hash,
)


def test_write_json(tmp_path):
    path = tmp_path / "a.json"
    write_json(path, {"ok": True})
    assert path.exists()


def test_stable_hash_is_deterministic():
    payload = {"z": 1, "a": [1, 2, 3]}
    assert stable_hash(payload) == stable_hash({"a": [1, 2, 3], "z": 1})


def test_write_json_with_hash(tmp_path):
    path = tmp_path / "hash.json"
    digest = write_json_with_hash(path, {"ok": True})
    assert len(digest) == 64


def test_validate_instance(tmp_path):
    schema = tmp_path / "schema.json"
    write_json(
        schema,
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object",
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
    )
    validate_instance({"name": "geoclt"}, schema)
    with pytest.raises(ValueError):
        validate_instance({"missing": True}, schema)


def test_derives_artifact_id_deterministically():
    one = derive_artifact_id("event_record", 2, "a" * 64)
    two = derive_artifact_id("event_record", 2, "a" * 64)
    assert one == two


def test_bundle_write_and_verify(tmp_path):
    artifact = build_artifact_entry(
        artifact_type="benchmark_result",
        schema_version=2,
        producer="geoclt:transformers-adapter:0.2.0",
        trace_id="trace-1",
        run_id="run-1",
        payload={"score": 0.9},
        created_at="2026-01-01T00:00:00Z",
    )
    bundle = build_artifact_bundle(
        run_id="run-1",
        trace_id="trace-1",
        producer="geoclt:sidecar:0.2.0",
        artifacts=[artifact],
        created_at="2026-01-01T00:00:00Z",
    )
    assert verify_bundle_manifest(bundle)
    written = write_bundle_to_store(bundle, tmp_path)
    assert len(written) == 1
    expected = artifact_store_path(
        store_root=tmp_path,
        artifact_type=artifact["artifact_type"],
        schema_version=artifact["schema_version"],
        run_id=artifact["run_id"],
        trace_id=artifact["trace_id"],
        artifact_id=artifact["artifact_id"],
    )
    assert written[0] == expected


def test_bundle_signature_verification(monkeypatch):
    monkeypatch.setenv("GEOCLT_BUNDLE_SIGNING", "hmac")
    monkeypatch.setenv("GEOCLT_BUNDLE_SIGNING_SECRET", "test-secret")
    artifact = build_artifact_entry(
        artifact_type="benchmark_result",
        schema_version=2,
        producer="geoclt:transformers-adapter:0.2.0",
        trace_id="trace-1",
        run_id="run-1",
        payload={"score": 0.9},
        created_at="2026-01-01T00:00:00Z",
    )
    bundle = build_artifact_bundle(
        run_id="run-1",
        trace_id="trace-1",
        producer="geoclt:sidecar:0.2.0",
        artifacts=[artifact],
        created_at="2026-01-01T00:00:00Z",
    )
    assert verify_bundle_manifest(bundle) is True
    tampered = dict(bundle)
    tampered["bundle_signature"] = "0" * 64
    assert verify_bundle_manifest(tampered) is False
