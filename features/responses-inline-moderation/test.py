"""Responses API with OpenAI inline moderation.model.

Positive-assertion probe for a `not_supported` nested model slot: the test
PASSES when Foundry accepts the request but ignores OpenAI inline moderation,
returning `moderation=None` as documented. If inline moderation starts being
honored, this test fails RED and the card must be promoted.
"""
import openai
import pytest


@pytest.mark.not_supported
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

    assert resp.output_text and resp.output_text.strip()
    assert getattr(resp, "moderation", None) is None, (
        "expected Foundry to ignore inline moderation, but moderation was populated"
    )
