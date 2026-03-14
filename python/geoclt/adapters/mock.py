from __future__ import annotations

from hashlib import sha256
from typing import Any

from .base import AdapterBase
from .capabilities import AdapterCapabilities


class MockAdapter(AdapterBase):
    def __init__(self, model_id: str = "mock-model") -> None:
        self.model_id = model_id
        self._hooks_installed = False
        self._active_traces: set[str] = set()

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_id="mock",
            activation_capture=True,
            attention_hooks=True,
            token_tagging=True,
            intervention_hooks=False,
            stream_mode=True,
            batch_mode=True,
            logits_observable=True,
            block_granularity="layer",
            supported_runtimes=("python",),
        )

    def list_blocks(self) -> list[str]:
        return [f"layer_{idx}" for idx in range(12)]

    def tokenize_with_tags(self, text: str) -> list[dict[str, Any]]:
        tokens = text.split()
        return [
            {"token": token, "index": idx, "tag": "answer-token" if idx == len(tokens) - 1 else "context"}
            for idx, token in enumerate(tokens)
        ]

    def _score(self, seed: str, low: float, high: float) -> float:
        digest = sha256(seed.encode("utf-8")).hexdigest()
        ratio = int(digest[:16], 16) / float(0xFFFFFFFFFFFFFFFF)
        return low + (high - low) * ratio

    def capture_activations(self, prompt: str, blocks: list[str]) -> dict[str, Any]:
        activations = []
        for block in blocks:
            activations.append(
                {
                    "block": block,
                    "energy": round(self._score(f"{self.model_id}:{prompt}:{block}", 0.1, 1.0), 6),
                }
            )
        return {"model_id": self.model_id, "prompt": prompt, "activations": activations}

    def start_trace(self, trace_id: str) -> dict[str, Any]:
        self._active_traces.add(trace_id)
        return {"status": "ok", "trace_id": trace_id}

    def end_trace(self, trace_id: str) -> dict[str, Any]:
        self._active_traces.discard(trace_id)
        return {"status": "ok", "trace_id": trace_id}

    def install_passive_hooks(self) -> None:
        self._hooks_installed = True

    def remove_hooks(self) -> None:
        self._hooks_installed = False

    def infer_tokens(self, prompt: str) -> list[str]:
        # Passive hooks must not perturb outputs.
        _ = self._hooks_installed
        return [f"tok_{idx}" for idx, _ in enumerate(prompt.split())]

    def infer_logits_hash(self, prompt: str) -> str:
        return sha256(f"{self.model_id}:{prompt}:logits".encode("utf-8")).hexdigest()
