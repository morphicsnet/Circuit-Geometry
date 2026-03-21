from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
import json
from typing import Any

from .base import AdapterBase
from .capabilities import AdapterCapabilities
from ..real_pipeline import resolve_real_model_id


def _iter_blocks(model: Any) -> list[Any]:
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return list(model.transformer.h)
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return list(model.model.layers)
    raise RuntimeError("unsupported transformers architecture for block enumeration")


@lru_cache(maxsize=4)
def _load_backend(model_id: str):  # pragma: no cover - exercised in integration usage
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    resolved = resolve_real_model_id(model_id)
    tokenizer = AutoTokenizer.from_pretrained(resolved)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(resolved)
    model.eval()
    torch.manual_seed(0)
    torch.set_num_threads(1)
    return tokenizer, model, resolved


class TransformersAdapter(AdapterBase):
    def __init__(self, model_id: str = "gpt2-small") -> None:
        self.model_id = model_id
        self._active_traces: set[str] = set()
        self._hook_handles: list[Any] = []
        self._passive_capture: list[dict[str, Any]] = []

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            adapter_id="transformers",
            activation_capture=True,
            attention_hooks=True,
            token_tagging=True,
            intervention_hooks=True,
            stream_mode=True,
            batch_mode=True,
            logits_observable=True,
            block_granularity="layer",
            supported_runtimes=("python", "torch"),
        )

    def list_blocks(self) -> list[str]:
        _, model, _ = _load_backend(self.model_id)
        return [f"layer_{index}" for index, _ in enumerate(_iter_blocks(model))]

    def tokenize_with_tags(self, text: str) -> list[dict[str, Any]]:
        tokenizer, _, _ = _load_backend(self.model_id)
        tokens = tokenizer.tokenize(text)
        if not tokens:
            tokens = [tokenizer.eos_token or "<eos>"]
        return [
            {
                "token": token,
                "index": index,
                "tag": "answer-token" if index == len(tokens) - 1 else "context",
            }
            for index, token in enumerate(tokens)
        ]

    def _run_forward(self, prompt: str):
        import torch

        tokenizer, model, resolved = _load_backend(self.model_id)
        encoded = tokenizer(prompt, return_tensors="pt")
        with torch.no_grad():
            output = model(**encoded)
        return tokenizer, model, resolved, encoded, output

    def capture_activations(self, prompt: str, blocks: list[str]) -> dict[str, Any]:
        import torch

        tokenizer, model, resolved = _load_backend(self.model_id)
        block_modules = _iter_blocks(model)
        captures: dict[str, dict[str, Any]] = {}
        handles = []
        requested = {block: int(block.split("_")[-1]) for block in blocks}

        def hook_factory(name: str):
            def _hook(_module, _inputs, output):
                tensor = output[0] if isinstance(output, tuple) else output
                captures[name] = {
                    "block": name,
                    "energy": round(float(tensor.detach().abs().mean().item()), 6),
                    "shape": list(tensor.shape),
                }

            return _hook

        try:
            for name, index in requested.items():
                handles.append(block_modules[index].register_forward_hook(hook_factory(name)))
            encoded = tokenizer(prompt, return_tensors="pt")
            with torch.no_grad():
                model(**encoded)
        finally:
            for handle in handles:
                handle.remove()

        ordered = [captures[name] for name in blocks if name in captures]
        return {"model_id": resolved, "prompt": prompt, "activations": ordered}

    def start_trace(self, trace_id: str) -> dict[str, Any]:
        self._active_traces.add(trace_id)
        return {"status": "ok", "trace_id": trace_id}

    def end_trace(self, trace_id: str) -> dict[str, Any]:
        self._active_traces.discard(trace_id)
        return {"status": "ok", "trace_id": trace_id}

    def install_passive_hooks(self) -> None:
        _, model, _ = _load_backend(self.model_id)
        self.remove_hooks()
        self._passive_capture = []
        for index, block in enumerate(_iter_blocks(model)[:2]):
            self._hook_handles.append(
                block.register_forward_hook(
                    lambda _module, _inputs, output, layer=index: self._passive_capture.append(
                        {
                            "layer": layer,
                            "shape": list((output[0] if isinstance(output, tuple) else output).shape),
                        }
                    )
                )
            )

    def remove_hooks(self) -> None:
        for handle in self._hook_handles:
            handle.remove()
        self._hook_handles.clear()
        self._passive_capture.clear()

    def infer_tokens(self, prompt: str) -> list[str]:
        tokenizer, model, _, encoded, _ = self._run_forward(prompt)
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=8,
            num_beams=1,
            pad_token_id=tokenizer.pad_token_id,
        )
        return tokenizer.convert_ids_to_tokens(generated[0])

    def infer_logits_hash(self, prompt: str) -> str:
        _, _, resolved, _, output = self._run_forward(prompt)
        payload = {
            "model_id": resolved,
            "logits": output.logits.detach().cpu().tolist(),
        }
        return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def attach_transformers_hooks(model, layers=None):
    selected = list(layers or [])
    return {"model": type(model).__name__, "layers": selected, "mode": "passive"}
