"""Direct Responses API call with BYOM model, no agent.

Reference conversion for a "supported" endpoint probe.
"""
import pytest


@pytest.mark.supported
def test_responses_direct(aoai, static_model):
    model = static_model()
    resp = aoai.responses.create(
        model=model,
        input="Say hello in one short sentence.",
    )
    assert resp.output_text and resp.output_text.strip()

