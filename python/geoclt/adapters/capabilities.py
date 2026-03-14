from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterCapabilities:
    adapter_id: str
    activation_capture: bool
    attention_hooks: bool
    token_tagging: bool
    intervention_hooks: bool
    stream_mode: bool
    batch_mode: bool
    logits_observable: bool
    block_granularity: str
    supported_runtimes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "activation_capture": self.activation_capture,
            "attention_hooks": self.attention_hooks,
            "token_tagging": self.token_tagging,
            "intervention_hooks": self.intervention_hooks,
            "stream_mode": self.stream_mode,
            "batch_mode": self.batch_mode,
            "logits_observable": self.logits_observable,
            "block_granularity": self.block_granularity,
            "supported_runtimes": list(self.supported_runtimes),
        }
