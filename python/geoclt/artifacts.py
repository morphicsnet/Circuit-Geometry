from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
import re
from typing import Any

from jsonschema.validators import validator_for

PRODUCER_PATTERN = re.compile(r"^[a-z0-9_-]+:[a-z0-9_-]+:[0-9]+\.[0-9]+\.[0-9]+$")


def _canonical_json(value: Any) -> str:
    # RFC8785-style canonical ordering and compact encoding.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def stable_hash(data: Any) -> str:
    canonical = _canonical_json(data)
    return sha256(canonical.encode("utf-8")).hexdigest()


def write_json_with_hash(path: str | Path, data: dict[str, Any]) -> str:
    write_json(path, data)
    return stable_hash(data)


def content_hash(payload: dict[str, Any]) -> str:
    return stable_hash(payload)


def derive_artifact_id(artifact_type: str, schema_version: int, payload_hash: str) -> str:
    seed = f"{artifact_type}:{schema_version}:{payload_hash}"
    return f"artifact-{sha256(seed.encode('utf-8')).hexdigest()}"


def artifact_store_path(
    *,
    store_root: str | Path,
    artifact_type: str,
    schema_version: int,
    run_id: str,
    trace_id: str,
    artifact_id: str,
) -> Path:
    return (
        Path(store_root)
        / artifact_type
        / str(schema_version)
        / run_id
        / trace_id
        / f"{artifact_id}.json"
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _validate_producer(producer: str) -> None:
    if not PRODUCER_PATTERN.match(producer):
        raise ValueError(f"invalid producer format: {producer}")


def build_artifact_entry(
    *,
    artifact_type: str,
    schema_version: int,
    producer: str,
    trace_id: str,
    run_id: str,
    payload: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    _validate_producer(producer)
    payload_hash = content_hash(payload)
    return {
        "artifact_id": derive_artifact_id(artifact_type, schema_version, payload_hash),
        "artifact_type": artifact_type,
        "schema_version": schema_version,
        "producer": producer,
        "trace_id": trace_id,
        "run_id": run_id,
        "content_hash": payload_hash,
        "created_at": created_at or _utc_now(),
        "payload": payload,
    }


def build_artifact_bundle(
    *,
    run_id: str,
    trace_id: str,
    producer: str,
    artifacts: list[dict[str, Any]],
    schema_version: int = 1,
    transitional: bool = False,
    immutable: bool = True,
    created_at: str | None = None,
) -> dict[str, Any]:
    _validate_producer(producer)
    bundle = {
        "bundle_id": f"bundle-{stable_hash({'run_id': run_id, 'trace_id': trace_id, 'count': len(artifacts)})[:16]}",
        "schema_version": schema_version,
        "producer": producer,
        "run_id": run_id,
        "trace_id": trace_id,
        "created_at": created_at or _utc_now(),
        "transitional": transitional,
        "immutable": immutable,
        "artifacts": artifacts,
    }
    bundle["bundle_hash"] = stable_hash(bundle)
    return bundle


def verify_bundle_manifest(bundle: dict[str, Any]) -> bool:
    copied = dict(bundle)
    provided_hash = copied.pop("bundle_hash", None)
    if provided_hash is None:
        return False
    return stable_hash(copied) == provided_hash


def write_bundle_to_store(bundle: dict[str, Any], store_root: str | Path) -> list[Path]:
    paths: list[Path] = []
    for artifact in bundle["artifacts"]:
        path = artifact_store_path(
            store_root=store_root,
            artifact_type=artifact["artifact_type"],
            schema_version=artifact["schema_version"],
            run_id=artifact["run_id"],
            trace_id=artifact["trace_id"],
            artifact_id=artifact["artifact_id"],
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, artifact)
        paths.append(path)
    return paths


def validate_instance(instance: dict[str, Any], schema_path: str | Path) -> None:
    schema = read_json(schema_path)
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: error.path)
    if errors:
        joined = "; ".join(error.message for error in errors)
        raise ValueError(f"schema validation failed for {schema_path}: {joined}")


def validate_instances(instances: list[dict[str, Any]], schema_path: str | Path) -> None:
    for instance in instances:
        validate_instance(instance, schema_path)
