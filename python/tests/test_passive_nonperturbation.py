from geoclt.adapters import MockAdapter


def test_passive_hooks_preserve_token_outputs_and_logits_hash():
    adapter = MockAdapter(model_id="gpt2-small")
    prompt = "who discovered penicillin"

    tokens_before = adapter.infer_tokens(prompt)
    logits_hash_before = adapter.infer_logits_hash(prompt)

    adapter.install_passive_hooks()
    tokens_after = adapter.infer_tokens(prompt)
    logits_hash_after = adapter.infer_logits_hash(prompt)
    adapter.remove_hooks()

    assert tokens_before == tokens_after
    assert logits_hash_before == logits_hash_after
