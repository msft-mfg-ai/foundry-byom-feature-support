"""Direct Responses API probe for APIM fronting Azure OpenAI."""
import pytest


@pytest.mark.supported
def test_routing_apim_openai(aoai, static_model):
    resp = aoai.responses.create(
        model=static_model(),
        input="Say hello in one short sentence.",
    )
    assert resp.output_text and resp.output_text.strip()
