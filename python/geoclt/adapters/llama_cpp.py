from __future__ import annotations

from .mock import MockAdapter


class LlamaCppAdapter(MockAdapter):
    def capabilities(self):
        capabilities = super().capabilities()
        return capabilities.__class__(
            adapter_id="llama_cpp",
            activation_capture=capabilities.activation_capture,
            attention_hooks=False,
            token_tagging=capabilities.token_tagging,
            intervention_hooks=False,
            stream_mode=False,
            batch_mode=True,
            logits_observable=False,
            block_granularity="block",
            supported_runtimes=("python", "llama_cpp"),
        )


def attach_llama_cpp_hooks(model, layers=None):
    return {"model": repr(model), "layers": layers or []}
