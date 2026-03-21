from geoclt.adapters import TransformersAdapter
from geoclt.sidecar import connect_sidecar


def test_transformers_adapter_real_sidecar_roundtrip():
    adapter = TransformersAdapter(model_id="gpt2-small")
    sidecar = connect_sidecar()

    trace_id = "trace-transformers-1"
    run_id = "run-transformers-1"
    prompt = "how many moons does mars have"

    blocks = adapter.list_blocks()[:3]
    activations = adapter.capture_activations(prompt, blocks)
    chunks = [str(item).encode("utf-8") for item in activations["activations"]]

    result = sidecar.stream_trace(
        trace_id=trace_id,
        adapter_id=adapter.capabilities().adapter_id,
        model_id="gpt2-small",
        lane_id="factual_retrieval.v1",
        run_id=run_id,
        chunks=chunks,
    )

    assert result["ok"] is True
    bundle = result["bundle"]
    assert bundle["immutable"] is True
    assert bundle["artifacts"][0]["artifact_type"] == "benchmark_result"
