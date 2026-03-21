from __future__ import annotations

from .base import ModelProfile, ModelRunnerBase


DEFAULT_PHI_PROFILE = ModelProfile(
    model_profile_id="profile-flan-t5-base-v1",
    model_id="google/flan-t5-base",
    tokenizer_version="flan-t5-base-tokenizer-v1",
    chat_template_version="flan-t5-base-prompt-v1",
    precision_mode="fp32",
    quantization="none",
    max_context=2048,
    decoding={"temperature": 0.0, "top_p": 1.0, "max_tokens": 32},
    structured_output_mode="line_protocol",
    runtime_backend="hf-transformers-seq2seq",
    seed_policy="fixed:42",
)


class PhiRunner(ModelRunnerBase):
    def __init__(self, profile: ModelProfile = DEFAULT_PHI_PROFILE) -> None:
        super().__init__(profile)
