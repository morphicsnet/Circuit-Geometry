from __future__ import annotations

from .base import ModelProfile, ModelRunnerBase


DEFAULT_PHI_PROFILE = ModelProfile(
    model_profile_id="profile-phi4-mini-v1",
    model_id="Phi-4-mini",
    tokenizer_version="phi4-tokenizer-v1",
    chat_template_version="phi4-chat-v1",
    precision_mode="int8",
    quantization="int8",
    max_context=8192,
    decoding={"temperature": 0.0, "top_p": 1.0, "max_tokens": 512},
    structured_output_mode="json_schema",
    runtime_backend="stub-transformers",
    seed_policy="fixed:42",
)


class PhiRunner(ModelRunnerBase):
    def __init__(self, profile: ModelProfile = DEFAULT_PHI_PROFILE) -> None:
        super().__init__(profile)
