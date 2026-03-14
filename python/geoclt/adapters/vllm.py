from __future__ import annotations

from .mock import MockAdapter


class VllmAdapter(MockAdapter):
    def capabilities(self):
        capabilities = super().capabilities()
        return capabilities.__class__(
            adapter_id="vllm",
            activation_capture=capabilities.activation_capture,
            attention_hooks=capabilities.attention_hooks,
            token_tagging=capabilities.token_tagging,
            intervention_hooks=False,
            stream_mode=True,
            batch_mode=True,
            logits_observable=False,
            block_granularity=capabilities.block_granularity,
            supported_runtimes=("python", "vllm"),
        )


def attach_vllm_hooks(engine, layers=None):
    return {"engine": repr(engine), "layers": layers or []}
