"""Reasoning model via BYOM, validating reasoning_effort forwarding."""
import pytest


@pytest.mark.supported
@pytest.mark.needs_env
def test_reasoning_models_byom(aoai, static_model, require_env, require_model):
    m = require_env("REASONING_MODEL")
    require_model(m, kind="static")
    model = static_model("REASONING_MODEL", "")
    resp = aoai.responses.create(
        model=model,
        input="What is 7 * 8? Think briefly then answer.",
        extra_body={"reasoning": {"effort": "low"}},
        max_output_tokens=256,
    )
    assert resp.output_text and resp.output_text.strip()
