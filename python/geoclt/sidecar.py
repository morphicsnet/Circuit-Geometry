from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from .artifacts import build_artifact_bundle, build_artifact_entry


@dataclass
class _TraceState:
    trace_id: str
    adapter_id: str
    model_id: str
    lane_id: str
    run_id: str
    started_at: str
    status: str = "STARTED"
    chunks: dict[str, bytes] = field(default_factory=dict)


class FakeSidecarClient:
    def __init__(self, producer: str = "geoclt:sidecar:0.2.0") -> None:
        self._producer = producer
        self._traces: dict[str, _TraceState] = {}

    def start_trace(self, *, trace_id: str, adapter_id: str, model_id: str, lane_id: str, run_id: str) -> dict[str, Any]:
        self._traces[trace_id] = _TraceState(
            trace_id=trace_id,
            adapter_id=adapter_id,
            model_id=model_id,
            lane_id=lane_id,
            run_id=run_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        return {"ok": True, "trace_id": trace_id}

    def stream_activation_chunk(
        self,
        *,
        trace_id: str,
        chunk_idempotency_key: str,
        payload: bytes,
        layer_id: int,
        sequence_no: int,
    ) -> dict[str, Any]:
        state = self._traces.get(trace_id)
        if state is None:
            return {"ok": False, "message": "trace not found"}

        existing = state.chunks.get(chunk_idempotency_key)
        if existing is not None:
            if existing == payload:
                return {"ok": True, "message": "duplicate-noop"}
            state.status = "FAILED"
            return {"ok": False, "message": "duplicate chunk conflict"}

        state.chunks[chunk_idempotency_key] = payload
        state.status = "STREAMING"
        return {
            "ok": True,
            "trace_id": trace_id,
            "layer_id": layer_id,
            "sequence_no": sequence_no,
            "chunk_count": len(state.chunks),
        }

    def end_trace(self, *, trace_id: str) -> dict[str, Any]:
        state = self._traces.get(trace_id)
        if state is None:
            return {"ok": False, "message": "trace not found"}
        if state.status == "FAILED":
            return {"ok": False, "message": "trace failed"}

        state.status = "ENDED"
        digest = sha256()
        for key in sorted(state.chunks):
            digest.update(state.chunks[key])
        payload = {
            "trace_id": trace_id,
            "adapter_id": state.adapter_id,
            "model_id": state.model_id,
            "lane_id": state.lane_id,
            "chunk_count": len(state.chunks),
            "activation_digest": digest.hexdigest(),
        }
        artifact = build_artifact_entry(
            artifact_type="benchmark_result",
            schema_version=2,
            producer=self._producer,
            trace_id=trace_id,
            run_id=state.run_id,
            payload=payload,
            created_at="2026-01-01T00:00:00Z",
        )
        bundle = build_artifact_bundle(
            run_id=state.run_id,
            trace_id=trace_id,
            producer=self._producer,
            artifacts=[artifact],
            transitional=False,
            immutable=True,
            created_at="2026-01-01T00:00:00Z",
        )
        state.status = "FINALIZED"
        return {"ok": True, "bundle": bundle}

    def abort_trace(self, *, trace_id: str, reason: str) -> dict[str, Any]:
        state = self._traces.get(trace_id)
        if state is None:
            return {"ok": False, "message": "trace not found"}
        state.status = "ABORTED"
        return {"ok": True, "reason": reason}

    def stream_trace(
        self,
        *,
        trace_id: str,
        adapter_id: str,
        model_id: str,
        lane_id: str,
        run_id: str,
        chunks: list[bytes],
    ) -> dict[str, Any]:
        self.start_trace(
            trace_id=trace_id,
            adapter_id=adapter_id,
            model_id=model_id,
            lane_id=lane_id,
            run_id=run_id,
        )
        for idx, payload in enumerate(chunks):
            response = self.stream_activation_chunk(
                trace_id=trace_id,
                chunk_idempotency_key=f"{trace_id}-{idx}",
                payload=payload,
                layer_id=idx,
                sequence_no=idx,
            )
            if not response.get("ok", False):
                return response
        return self.end_trace(trace_id=trace_id)


def connect_sidecar(url: str | None = None) -> FakeSidecarClient:
    _ = url
    return FakeSidecarClient()


def start_sidecar_local(*args: Any, **kwargs: Any) -> dict[str, Any]:
    _ = (args, kwargs)
    return {"status": "ok", "component": "sidecar", "mode": "fake"}
