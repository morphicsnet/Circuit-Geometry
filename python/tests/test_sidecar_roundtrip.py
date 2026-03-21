import os

from geoclt.sidecar import connect_sidecar
from geoclt.sidecar import GrpcSidecarClient, start_sidecar_local


def test_duplicate_chunk_semantics():
    sidecar = connect_sidecar()
    trace_id = "trace-dup"

    assert sidecar.start_trace(
        trace_id=trace_id,
        adapter_id="transformers",
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="run-dup",
    )["ok"] is True

    first = sidecar.stream_activation_chunk(
        trace_id=trace_id,
        chunk_idempotency_key="key-1",
        payload=b"abc",
        layer_id=1,
        sequence_no=1,
    )
    duplicate = sidecar.stream_activation_chunk(
        trace_id=trace_id,
        chunk_idempotency_key="key-1",
        payload=b"abc",
        layer_id=1,
        sequence_no=1,
    )
    conflict = sidecar.stream_activation_chunk(
        trace_id=trace_id,
        chunk_idempotency_key="key-1",
        payload=b"def",
        layer_id=1,
        sequence_no=1,
    )

    assert first["ok"] is True
    assert duplicate["ok"] is True
    assert duplicate["message"] == "duplicate-noop"
    assert conflict["ok"] is False
    assert "conflict" in conflict["message"]


def test_same_trace_produces_stable_bundle_hash():
    sidecar = connect_sidecar()
    args = {
        "trace_id": "trace-stable",
        "adapter_id": "transformers",
        "model_id": "gpt2-small",
        "lane_id": "factual_retrieval.v1",
        "run_id": "run-stable",
        "chunks": [b"a", b"b"],
    }
    first = sidecar.stream_trace(**args)
    second = sidecar.stream_trace(**args)
    assert first["ok"] is True
    assert second["ok"] is True
    assert first["bundle"]["bundle_hash"] == second["bundle"]["bundle_hash"]

def test_concurrent_trace_separation():
    sidecar = connect_sidecar()

    assert sidecar.start_trace(
        trace_id="trace-a",
        adapter_id="transformers",
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="run-a",
    )["ok"]
    assert sidecar.start_trace(
        trace_id="trace-b",
        adapter_id="transformers",
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id="run-b",
    )["ok"]

    sidecar.stream_activation_chunk(
        trace_id="trace-a",
        chunk_idempotency_key="a-1",
        payload=b"aaa",
        layer_id=1,
        sequence_no=1,
    )
    sidecar.stream_activation_chunk(
        trace_id="trace-b",
        chunk_idempotency_key="b-1",
        payload=b"bbb",
        layer_id=1,
        sequence_no=1,
    )

    end_a = sidecar.end_trace(trace_id="trace-a")
    end_b = sidecar.end_trace(trace_id="trace-b")

    assert end_a["ok"] is True
    assert end_b["ok"] is True
    assert end_a["bundle"]["trace_id"] == "trace-a"
    assert end_b["bundle"]["trace_id"] == "trace-b"
    assert end_a["bundle"]["bundle_hash"] != end_b["bundle"]["bundle_hash"]


def test_sidecar_rejects_invalid_token():
    original_mode = os.environ.get("GEOCLT_AUTH_MODE")
    original_token = os.environ.get("GEOCLT_AUTH_TOKEN")
    os.environ["GEOCLT_AUTH_MODE"] = "token"
    os.environ["GEOCLT_AUTH_TOKEN"] = "valid-token"
    process = start_sidecar_local()
    try:
        os.environ["GEOCLT_AUTH_TOKEN"] = "invalid-token"
        client = GrpcSidecarClient(process.addr)
        status = client.get_status()
        client.close()
        assert status["ok"] is False
    finally:
        process.stop()
        if original_mode is None:
            os.environ.pop("GEOCLT_AUTH_MODE", None)
        else:
            os.environ["GEOCLT_AUTH_MODE"] = original_mode
        if original_token is None:
            os.environ.pop("GEOCLT_AUTH_TOKEN", None)
        else:
            os.environ["GEOCLT_AUTH_TOKEN"] = original_token
