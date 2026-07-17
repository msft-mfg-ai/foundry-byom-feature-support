"""Responses API with OpenAI inline moderation.model."""
import openai
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=False,
    reason="omni-moderation-latest is an OpenAI-only model, not an Azure Foundry BYOM target.",
)
def test_responses_inline_moderation(aoai, static_model):
    try:
        resp = aoai.responses.create(
            model=static_model(),
            input="Say hi in one short sentence.",
            extra_body={"moderation": {"model": "omni-moderation-latest"}},
        )
    except openai.APIStatusError as e:
        body = getattr(e, "response", None)
        body_text = body.text if body is not None else str(e)
        raise AssertionError(f"responses.create moderation HTTP {e.status_code}: {body_text}") from None
    print(f"responses.create moderation OK: status={resp.status!r}, moderation={getattr(resp, 'moderation', None)!r}, output_text={resp.output_text!r}")
    assert resp.output_text and resp.output_text.strip()
