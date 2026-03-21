from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
import re
import time
from typing import Any

from ..artifacts import build_artifact_entry, stable_hash


@dataclass(frozen=True)
class ModelProfile:
    model_profile_id: str
    model_id: str
    tokenizer_version: str
    chat_template_version: str
    precision_mode: str
    quantization: str
    max_context: int
    decoding: dict[str, Any]
    structured_output_mode: str
    runtime_backend: str
    seed_policy: str

    def as_record_payload(self) -> dict[str, Any]:
        return {
            "model_profile_id": self.model_profile_id,
            "model_id": self.model_id,
            "tokenizer_version": self.tokenizer_version,
            "chat_template_version": self.chat_template_version,
            "precision_mode": self.precision_mode,
            "quantization": self.quantization,
            "max_context": self.max_context,
            "decoding": self.decoding,
            "structured_output_mode": self.structured_output_mode,
            "runtime_backend": self.runtime_backend,
            "seed_policy": self.seed_policy,
        }


class ModelRunnerBase:
    def __init__(self, profile: ModelProfile) -> None:
        self.profile = profile
        self._last_stats: dict[str, dict[str, float]] = {}

    def deterministic_config(self) -> dict[str, Any]:
        return {
            "model_profile_id": self.profile.model_profile_id,
            "seed_policy": self.profile.seed_policy,
            "decoding": self.profile.decoding,
            "runtime_backend": self.profile.runtime_backend,
        }

    def _prompt_for_payload(self, lane_id: str, payload: dict[str, Any]) -> str:
        text = str(payload.get("text", "")).strip()
        return (
            f"You are evaluating lane {lane_id}. "
            "Respond with exactly two lines.\n"
            "routing_label: <allow|allow_with_review>\n"
            "answer: <short justification>\n"
            f"Input: {text}"
        )

    def _parse_routing_label(self, text: str) -> str | None:
        match = re.search(r"routing_label\s*:\s*(allow_with_review|allow)\b", text, re.IGNORECASE)
        if match is not None:
            return match.group(1).lower()
        lowered = text.lower()
        if "allow_with_review" in lowered:
            return "allow_with_review"
        if re.search(r"\ballow\b", lowered):
            return "allow"
        return None

    def _parse_answer(self, text: str) -> str:
        match = re.search(r"answer\s*:\s*(.+)", text, re.IGNORECASE | re.DOTALL)
        if match is not None:
            return match.group(1).strip()
        return text.strip()

    def generate_structured_output(self, lane_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        import torch

        prompt = self._prompt_for_payload(lane_id, payload)
        key = stable_hash({"lane_id": lane_id, "payload": payload, "profile": self.profile.model_id})
        tokenizer, model = _load_seq2seq_backend(self.profile.model_id)
        encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=self.profile.max_context)

        start = time.perf_counter()
        with torch.no_grad():
            generated = model.generate(
                **encoded,
                do_sample=False,
                num_beams=1,
                max_new_tokens=int(self.profile.decoding.get("max_tokens", 64)),
                return_dict_in_generate=True,
                output_scores=True,
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

        input_terms = {term for term in re.findall(r"[a-z0-9]+", str(payload.get("text", "")).lower()) if len(term) > 2}
        answer_terms = {term for term in re.findall(r"[a-z0-9]+", answer.lower()) if len(term) > 2}
        overlap = len(input_terms & answer_terms)
        evidence_alignment = round(min(0.999, 0.4 + (0.1 * overlap) + (0.4 if routing_label else 0.0)), 6)

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

    def collect_runtime_stats(self, lane_id: str, payload: dict[str, Any]) -> dict[str, float]:
        key = stable_hash({"lane_id": lane_id, "payload": payload, "profile": self.profile.model_id})
        if key not in self._last_stats:
            self.generate_structured_output(lane_id, payload)
        return dict(self._last_stats[key])

    def emit_model_profile_record(self, trace_id: str, run_id: str) -> dict[str, Any]:
        return build_artifact_entry(
            artifact_type="model_profile_record",
            schema_version=1,
            producer="geoclt:model-runner:0.4.0",
            trace_id=trace_id,
            run_id=run_id,
            payload=self.profile.as_record_payload(),
            created_at="2026-01-01T00:00:00Z",
        )


def profile_frozen(profile: ModelProfile) -> bool:
    expected = profile.model_profile_id.startswith("profile-") and profile.seed_policy.startswith(
        "fixed:"
    )
    return expected and profile.max_context > 0 and "stub" not in profile.runtime_backend


@lru_cache(maxsize=4)
def _load_seq2seq_backend(model_id: str):  # pragma: no cover - exercised in integration usage
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    model.eval()
    torch.manual_seed(42)
    torch.set_num_threads(1)
    return tokenizer, model


def _model_memory_mb(model: Any) -> float:
    total_bytes = 0
    for parameter in model.parameters():
        total_bytes += parameter.numel() * parameter.element_size()
    return round(total_bytes / (1024 * 1024), 3)
