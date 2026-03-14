from __future__ import annotations

from .base import ModelProfile, ModelRunnerBase


DEFAULT_MULTIMODAL_PROFILE = ModelProfile(
    model_profile_id="profile-qwen25-vl-7b-v1",
    model_id="Qwen2.5-VL-7B",
    tokenizer_version="qwen2.5-vl-tokenizer-v1",
    chat_template_version="qwen2.5-vl-chat-v1",
    precision_mode="fp16",
    quantization="none",
    max_context=16384,
    decoding={"temperature": 0.0, "top_p": 1.0, "max_tokens": 512},
    structured_output_mode="json_schema",
    runtime_backend="stub-vl",
    seed_policy="fixed:42",
)


class MultimodalRunner(ModelRunnerBase):
    def __init__(self, profile: ModelProfile = DEFAULT_MULTIMODAL_PROFILE) -> None:
        super().__init__(profile)
