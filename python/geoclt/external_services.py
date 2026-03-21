from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .artifacts import stable_hash

_MEMORY_QUEUE: list[dict[str, Any]] = []


def store_backend() -> str:
    return os.getenv("GEOCLT_STORE_BACKEND", "fs").strip().lower()


def queue_backend() -> str:
    return os.getenv("GEOCLT_QUEUE_BACKEND", "memory").strip().lower()


def store_bundle(bundle: dict[str, Any], *, workspace: str | Path) -> dict[str, Any]:
    backend = store_backend()
    payload = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode("utf-8")
    object_id = f"{bundle['bundle_id']}-{stable_hash(bundle)[:12]}.json"
    if backend == "fs":
        root = Path(workspace) / "phase4" / "artifact_store"
        root.mkdir(parents=True, exist_ok=True)
        path = root / object_id
        path.write_bytes(payload)
        return {"backend": "fs", "uri": str(path.resolve()), "object_id": object_id}
    if backend == "minio":
        try:
            from minio import Minio
        except Exception as error:  # pragma: no cover
            raise RuntimeError("minio backend requested but minio package is not installed") from error
        endpoint = os.getenv("GEOCLT_MINIO_ENDPOINT", "127.0.0.1:9000")
        access_key = os.getenv("GEOCLT_MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("GEOCLT_MINIO_SECRET_KEY", "minioadmin")
        bucket = os.getenv("GEOCLT_MINIO_BUCKET", "geoclt-artifacts")
        secure = os.getenv("GEOCLT_MINIO_SECURE", "0").strip() == "1"
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
        from io import BytesIO

        client.put_object(
            bucket_name=bucket,
            object_name=object_id,
            data=BytesIO(payload),
            length=len(payload),
            content_type="application/json",
        )
        return {
            "backend": "minio",
            "uri": f"s3://{bucket}/{object_id}",
            "object_id": object_id,
        }
    raise ValueError(f"unsupported store backend: {backend}")


def queue_event(event: dict[str, Any]) -> dict[str, Any]:
    backend = queue_backend()
    if backend == "memory":
        _MEMORY_QUEUE.append(event)
        return {"backend": "memory", "queued": True, "queue_depth": len(_MEMORY_QUEUE)}
    if backend == "redis":
        try:
            import redis
        except Exception as error:  # pragma: no cover
            raise RuntimeError("redis backend requested but redis package is not installed") from error
        url = os.getenv("GEOCLT_REDIS_URL", "redis://127.0.0.1:6379/0")
        key = os.getenv("GEOCLT_REDIS_QUEUE_KEY", "geoclt:queue")
        client = redis.Redis.from_url(url)
        client.rpush(key, json.dumps(event, sort_keys=True))
        depth = int(client.llen(key))
        return {"backend": "redis", "queued": True, "queue_depth": depth}
    raise ValueError(f"unsupported queue backend: {backend}")
