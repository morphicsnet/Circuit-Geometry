from __future__ import annotations

import atexit
from dataclasses import dataclass
from datetime import UTC, datetime
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PROTO_PATH = REPO_ROOT / "proto" / "sidecar.proto"
GENERATED_DIR = REPO_ROOT / ".tmp" / "grpc_sidecar"
_DEFAULT_CLIENT: GrpcSidecarClient | None = None


def _normalize_target(url: str) -> str:
    return url.replace("grpc://", "").replace("http://", "").replace("https://", "")


def _auth_mode() -> str:
    return os.getenv("GEOCLT_AUTH_MODE", "token").strip().lower()


def _auth_token() -> str:
    return os.getenv("GEOCLT_AUTH_TOKEN", "geoclt-local-token")


def _auth_metadata() -> list[tuple[str, str]] | None:
    if _auth_mode() != "token":
        return None
    return [("authorization", f"Bearer {_auth_token()}")]


def _free_local_addr() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        host, port = sock.getsockname()
    return f"{host}:{port}"


def _load_proto_modules():
    try:
        import grpc  # noqa: F401
    except ImportError as error:  # pragma: no cover
        raise RuntimeError("grpcio is required for the real sidecar client") from error

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    pb2_path = GENERATED_DIR / "sidecar_pb2.py"
    grpc_path = GENERATED_DIR / "sidecar_pb2_grpc.py"
    if (
        not pb2_path.exists()
        or not grpc_path.exists()
        or pb2_path.stat().st_mtime < PROTO_PATH.stat().st_mtime
        or grpc_path.stat().st_mtime < PROTO_PATH.stat().st_mtime
    ):
        command = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"-I{PROTO_PATH.parent}",
            f"--python_out={GENERATED_DIR}",
            f"--grpc_python_out={GENERATED_DIR}",
            str(PROTO_PATH),
        ]
        subprocess.run(command, check=True, cwd=REPO_ROOT)

    if str(GENERATED_DIR) not in sys.path:
        sys.path.insert(0, str(GENERATED_DIR))
    pb2 = importlib.import_module("sidecar_pb2")
    pb2_grpc = importlib.import_module("sidecar_pb2_grpc")
    return pb2, pb2_grpc


@dataclass
class SidecarProcess:
    addr: str
    process: subprocess.Popen[str]

    def stop(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)


class GrpcSidecarClient:
    def __init__(self, target: str, process: SidecarProcess | None = None) -> None:
        import grpc

        pb2, pb2_grpc = _load_proto_modules()
        self._grpc = grpc
        self._pb2 = pb2
        self._pb2_grpc = pb2_grpc
        self._target = _normalize_target(target)
        self._channel = grpc.insecure_channel(self._target)
        self._stub = pb2_grpc.SidecarServiceStub(self._channel)
        self._process = process

    def close(self) -> None:
        self._channel.close()
        if self._process is not None:
            self._process.stop()
            self._process = None

    def get_status(self) -> dict[str, Any]:
        try:
            response = self._stub.GetStatus(
                self._pb2.Ack(ok=True, message="status"),
                metadata=_auth_metadata(),
            )
            return {"ok": True, "status": response.status, "active_traces": response.active_traces}
        except self._grpc.RpcError as error:
            return {"ok": False, "message": error.details() or str(error)}

    def start_trace(
        self, *, trace_id: str, adapter_id: str, model_id: str, lane_id: str, run_id: str
    ) -> dict[str, Any]:
        request = self._pb2.TraceStart(
            trace_id=trace_id,
            adapter_id=adapter_id,
            model_id=model_id,
            lane_id=lane_id,
            run_id=run_id,
            started_at=datetime.now(UTC).isoformat(),
        )
        try:
            response = self._stub.StartTrace(request, metadata=_auth_metadata())
            return {"ok": response.ok, "message": response.message, "trace_id": trace_id}
        except self._grpc.RpcError as error:
            return {"ok": False, "message": error.details() or str(error)}

    def stream_activation_chunk(
        self,
        *,
        trace_id: str,
        chunk_idempotency_key: str,
        payload: bytes,
        layer_id: int,
        sequence_no: int,
    ) -> dict[str, Any]:
        request = self._pb2.ActivationChunk(
            trace_id=trace_id,
            chunk_idempotency_key=chunk_idempotency_key,
            layer_id=layer_id,
            payload=payload,
            sequence_no=sequence_no,
        )
        try:
            response = self._stub.PushActivation(request, metadata=_auth_metadata())
            message = response.message or "chunk accepted"
            return {
                "ok": response.ok,
                "message": "duplicate-noop" if "duplicate" in message else message,
                "trace_id": trace_id,
                "layer_id": layer_id,
                "sequence_no": sequence_no,
            }
        except self._grpc.RpcError as error:
            return {"ok": False, "message": error.details() or str(error)}

    def end_trace(self, *, trace_id: str) -> dict[str, Any]:
        request = self._pb2.TraceEnd(trace_id=trace_id, total_chunks=0)
        try:
            response = self._stub.EndTrace(request, metadata=_auth_metadata())
            bundle = json.loads(response.bundle_json.decode("utf-8"))
            return {"ok": True, "bundle": bundle, "bundle_hash": response.bundle_hash}
        except self._grpc.RpcError as error:
            return {"ok": False, "message": error.details() or str(error)}

    def abort_trace(self, *, trace_id: str, reason: str) -> dict[str, Any]:
        request = self._pb2.TraceAbort(trace_id=trace_id, reason=reason)
        try:
            response = self._stub.AbortTrace(request, metadata=_auth_metadata())
            return {"ok": response.ok, "message": response.message, "reason": reason}
        except self._grpc.RpcError as error:
            return {"ok": False, "message": error.details() or str(error)}

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
        started = self.start_trace(
            trace_id=trace_id,
            adapter_id=adapter_id,
            model_id=model_id,
            lane_id=lane_id,
            run_id=run_id,
        )
        if not started.get("ok", False):
            return started
        for index, payload in enumerate(chunks):
            chunk = self.stream_activation_chunk(
                trace_id=trace_id,
                chunk_idempotency_key=f"{trace_id}-{index}",
                payload=payload,
                layer_id=index,
                sequence_no=index,
            )
            if not chunk.get("ok", False):
                return chunk
        return self.end_trace(trace_id=trace_id)


def start_sidecar_local(addr: str | None = None) -> SidecarProcess:
    target = addr or _free_local_addr()
    process = subprocess.Popen(
        ["cargo", "run", "-p", "geoclt-cli", "--", "sidecar", "serve", "--addr", target],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    process_handle = SidecarProcess(addr=target, process=process)
    client = GrpcSidecarClient(target)
    deadline = time.time() + 30
    while time.time() < deadline:
        status = client.get_status()
        if status.get("ok"):
            client.close()
            return process_handle
        if process.poll() is not None:
            raise RuntimeError(f"sidecar process exited early with code {process.returncode}")
        time.sleep(0.25)
    client.close()
    process_handle.stop()
    raise RuntimeError("timed out waiting for sidecar server to become ready")


def _close_default_client() -> None:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is not None:
        _DEFAULT_CLIENT.close()
        _DEFAULT_CLIENT = None


atexit.register(_close_default_client)


def connect_sidecar(url: str | None = None) -> GrpcSidecarClient:
    global _DEFAULT_CLIENT
    if url is not None:
        return GrpcSidecarClient(url)
    configured_url = os.getenv("GEOCLT_SIDECAR_URL")
    require_sidecar = os.getenv("GEOCLT_REQUIRE_SIDECAR", "1").strip() == "1"
    if configured_url:
        return GrpcSidecarClient(configured_url)
    if require_sidecar and _DEFAULT_CLIENT is None:
        process = start_sidecar_local()
        _DEFAULT_CLIENT = GrpcSidecarClient(process.addr, process=process)
        return _DEFAULT_CLIENT
    if require_sidecar and _DEFAULT_CLIENT is not None:
        return _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        process = start_sidecar_local()
        _DEFAULT_CLIENT = GrpcSidecarClient(process.addr, process=process)
    return _DEFAULT_CLIENT
