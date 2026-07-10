"""Responses API compaction with BYOM-prefixed model slots."""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Responses compaction endpoints are expected not to route the BYOM prefix.",
)
def test_responses_compaction(aoai, static_model):
    model = static_model()
    resp = aoai.responses.create(
        model=model,
        input="Say hi in one short sentence.",
        extra_body={"context_management": [{"type": "compaction", "compact_threshold": 1000}]},
    )
    assert resp.output_text and resp.output_text.strip()

    raw = aoai.post(
        "/responses/compact",
        body={"model": model, "input": [{"type": "message", "role": "user", "content": "hello"}]},
        cast_to=object,
    )
    assert raw
