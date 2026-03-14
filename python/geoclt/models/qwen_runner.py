from __future__ import annotations

from .base import ModelProfile, ModelRunnerBase


DEFAULT_QWEN_PROFILE = ModelProfile(
    model_profile_id="profile-qwen25-7b-instruct-v1",
    model_id="Qwen2.5-7B-Instruct",
    tokenizer_version="qwen2.5-tokenizer-v1",
    chat_template_version="qwen2.5-chat-v1",
    precision_mode="fp16",
    quantization="none",
    max_context=32768,
    decoding={"temperature": 0.0, "top_p": 1.0, "max_tokens": 512},
    structured_output_mode="json_schema",
    runtime_backend="stub-transformers",
    seed_policy="fixed:42",
)


class QwenRunner(ModelRunnerBase):
    def __init__(self, profile: ModelProfile = DEFAULT_QWEN_PROFILE) -> None:
        super().__init__(profile)
