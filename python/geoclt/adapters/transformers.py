from __future__ import annotations

from .mock import MockAdapter


class TransformersAdapter(MockAdapter):
    def capabilities(self):
        capabilities = super().capabilities()
        return capabilities.__class__(
            adapter_id="transformers",
            activation_capture=capabilities.activation_capture,
            attention_hooks=capabilities.attention_hooks,
            token_tagging=capabilities.token_tagging,
            intervention_hooks=True,
            stream_mode=capabilities.stream_mode,
            batch_mode=capabilities.batch_mode,
            logits_observable=capabilities.logits_observable,
            block_granularity=capabilities.block_granularity,
            supported_runtimes=("python", "torch"),
        )


def attach_transformers_hooks(model, layers=None):
    return {"model": repr(model), "layers": layers or []}
