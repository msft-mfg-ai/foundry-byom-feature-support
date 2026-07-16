"""Responses API with nested moderation.model — a second BYOM model slot."""
import pytest


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Nested moderation model may not be routed via the BYOM prefix.",
)
def test_responses_inline_moderation(aoai, static_model):
    main_model = static_model()
    moderation_model = static_model("MODERATION_MODEL", "omni-moderation-latest")
    resp = aoai.responses.create(
        model=main_model,
        input="Say hi in one short sentence.",
        extra_body={"moderation": {"model": moderation_model}},
    )
    assert resp.output_text and resp.output_text.strip()
