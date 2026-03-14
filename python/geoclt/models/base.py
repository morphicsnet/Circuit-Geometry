from __future__ import annotations

from dataclasses import dataclass
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

    def deterministic_config(self) -> dict[str, Any]:
        return {
            "model_profile_id": self.profile.model_profile_id,
            "seed_policy": self.profile.seed_policy,
            "decoding": self.profile.decoding,
            "runtime_backend": self.profile.runtime_backend,
        }

    def generate_structured_output(self, lane_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        seed = stable_hash(
            {
                "lane_id": lane_id,
                "payload": payload,
                "profile": self.deterministic_config(),
            }
        )
        base_confidence = int(seed[:8], 16) / float(0xFFFFFFFF)
        # Keep stub outputs mostly high-confidence so scorecard thresholds are stable in CI.
        confidence = round(0.86 + (0.13 * base_confidence), 6)
        if payload.get("force_fallback") is True:
            confidence = 0.72
            routing_label = "allow_with_review"
        else:
            routing_label = "allow"
        return {
            "answer": f"stub-response-{seed[:12]}",
            "routing_label": routing_label,
            "confidence": confidence,
            "evidence_alignment": round(min(0.999, (confidence * 0.7) + 0.25), 6),
            "schema_valid": True,
        }

    def collect_runtime_stats(self, lane_id: str, payload: dict[str, Any]) -> dict[str, float]:
        digest = stable_hash({"lane_id": lane_id, "payload": payload, "model": self.profile.model_id})
        latency = 300 + (int(digest[0:4], 16) % 600)
        memory_mb = 1024 + (int(digest[4:8], 16) % 2048)
        return {"latency_ms": float(latency), "memory_mb": float(memory_mb)}

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
    return expected and profile.max_context > 0
