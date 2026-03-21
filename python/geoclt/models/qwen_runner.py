from __future__ import annotations

from functools import lru_cache
import time
from typing import Any

from ..artifacts import stable_hash
from .base import ModelProfile, ModelRunnerBase, _model_memory_mb


DEFAULT_QWEN_PROFILE = ModelProfile(
    model_profile_id="profile-qwen25-0.5b-instruct-v1",
    model_id="Qwen/Qwen2.5-0.5B-Instruct",
    tokenizer_version="qwen2.5-tokenizer-v1",
    chat_template_version="qwen2.5-instruct-v1",
    precision_mode="fp32",
    quantization="none",
    max_context=4096,
    decoding={"temperature": 0.0, "top_p": 1.0, "max_tokens": 64},
    structured_output_mode="line_protocol",
    runtime_backend="hf-transformers-causal",
    seed_policy="fixed:42",
)


@lru_cache(maxsize=2)
def _load_qwen_backend(model_id: str):  # pragma: no cover - exercised in integration usage
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_id)
    model.eval()
    torch.manual_seed(42)
    torch.set_num_threads(1)
    return tokenizer, model


class QwenRunner(ModelRunnerBase):
    def __init__(self, profile: ModelProfile = DEFAULT_QWEN_PROFILE) -> None:
        super().__init__(profile)

    def generate_structured_output(self, lane_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        import torch

        prompt = self._prompt_for_payload(lane_id, payload)
        tokenizer, model = _load_qwen_backend(self.profile.model_id)
        encoded = tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=self.profile.max_context
        )

        start = time.perf_counter()
        with torch.no_grad():
            generated = model.generate(
                **encoded,
                do_sample=False,
                num_beams=1,
                max_new_tokens=int(self.profile.decoding.get("max_tokens", 64)),
                return_dict_in_generate=True,
                output_scores=True,
                pad_token_id=tokenizer.pad_token_id,
            )
        latency_ms = (time.perf_counter() - start) * 1000.0
        decoded = tokenizer.decode(generated.sequences[0], skip_special_tokens=True).strip()
        routing_label = self._parse_routing_label(decoded)
        answer = self._parse_answer(decoded)

        confidence = 0.0
        if generated.scores:
            scores = []
            for score in generated.scores:
                probabilities = torch.softmax(score[0], dim=-1)
                scores.append(float(probabilities.max().item()))
            confidence = sum(scores) / len(scores)
        confidence = round(confidence, 6)

        input_text = str(payload.get("text", ""))
        overlap = len(
            {
                term
                for term in input_text.lower().split()
                if term and term in (answer.lower() if answer else decoded.lower())
            }
        )
        evidence_alignment = round(min(0.999, 0.4 + (0.1 * overlap) + (0.4 if routing_label else 0.0)), 6)

        key = stable_hash({"lane_id": lane_id, "payload": payload, "profile": self.profile.model_id})
        self._last_stats[key] = {
            "latency_ms": round(latency_ms, 3),
            "memory_mb": float(_model_memory_mb(model)),
        }

        return {
            "answer": answer or decoded,
            "routing_label": routing_label or "allow_with_review",
            "confidence": confidence,
            "evidence_alignment": evidence_alignment,
            "schema_valid": routing_label is not None and bool(answer or decoded),
            "raw_output": decoded,
        }
