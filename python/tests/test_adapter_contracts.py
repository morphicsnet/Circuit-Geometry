from geoclt.adapters import LlamaCppAdapter, TransformersAdapter, VllmAdapter


def _assert_adapter_contract(adapter):
    capabilities = adapter.capabilities()
    assert capabilities.adapter_id
    assert isinstance(capabilities.supported_runtimes, tuple)

    blocks = adapter.list_blocks()
    assert blocks

    tagged = adapter.tokenize_with_tags("hello world")
    assert tagged[-1]["tag"] == "answer-token"

    adapter.start_trace("trace-1")
    activations = adapter.capture_activations("hello world", blocks[:2])
    assert len(activations["activations"]) == 2
    adapter.end_trace("trace-1")

def test_transformers_adapter_contract():
    _assert_adapter_contract(TransformersAdapter())


def test_adapter_capability_declarations_are_machine_readable():
    adapters = [TransformersAdapter(), VllmAdapter(), LlamaCppAdapter()]
    allowed_granularity = {"layer", "block", "submodule"}
    for adapter in adapters:
        caps = adapter.capabilities().as_dict()
        assert isinstance(caps["activation_capture"], bool)
        assert isinstance(caps["attention_hooks"], bool)
        assert isinstance(caps["token_tagging"], bool)
        assert isinstance(caps["intervention_hooks"], bool)
        assert isinstance(caps["stream_mode"], bool)
        assert isinstance(caps["batch_mode"], bool)
        assert caps["block_granularity"] in allowed_granularity
        assert isinstance(caps["supported_runtimes"], list)


def test_optional_adapter_runtime_unavailable_is_explicit():
    for adapter in [VllmAdapter(), LlamaCppAdapter()]:
        try:
            adapter.list_blocks()
        except RuntimeError as error:
            assert "not installed or configured" in str(error)
        else:
            raise AssertionError("expected explicit runtime unavailability")
