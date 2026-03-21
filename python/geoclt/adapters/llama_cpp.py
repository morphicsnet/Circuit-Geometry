from __future__ import annotations

from hashlib import sha256
from typing import Any

from .base import AdapterBase
from .capabilities import AdapterCapabilities


class LlamaCppAdapter(AdapterBase):
    def __init__(self, model_id: str = "gpt2-small") -> None:
        self.model_id = model_id

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_id="llama_cpp",
            activation_capture=True,
            attention_hooks=False,
            token_tagging=True,
            intervention_hooks=False,
            stream_mode=False,
            batch_mode=True,
            logits_observable=False,
            block_granularity="block",
            supported_runtimes=("python", "llama_cpp"),
        )

    def _unavailable(self) -> RuntimeError:
        return RuntimeError("llama.cpp runtime is not installed or configured in this environment")

    def list_blocks(self) -> list[str]:
        raise self._unavailable()

    def tokenize_with_tags(self, text: str) -> list[dict[str, Any]]:
        tokens = text.split()
        return [
            {
                "token": token,
                "index": index,
                "tag": "answer-token" if index == len(tokens) - 1 else "context",
            }
            for index, token in enumerate(tokens)
        ]

    def capture_activations(self, prompt: str, blocks: list[str]) -> dict[str, Any]:
        _ = (prompt, blocks)
        raise self._unavailable()

    def start_trace(self, trace_id: str) -> dict[str, Any]:
        return {"status": "ok", "trace_id": trace_id}

    def end_trace(self, trace_id: str) -> dict[str, Any]:
        return {"status": "ok", "trace_id": trace_id}

    def install_passive_hooks(self) -> None:
        raise self._unavailable()

    def remove_hooks(self) -> None:
        return None

    def infer_tokens(self, prompt: str) -> list[str]:
        return prompt.split()

    def infer_logits_hash(self, prompt: str) -> str:
        return sha256(f"llama_cpp:{self.model_id}:{prompt}".encode("utf-8")).hexdigest()


def attach_llama_cpp_hooks(model, layers=None):
    selected = list(layers or [])
    return {"model": type(model).__name__, "layers": selected, "mode": "passive"}
