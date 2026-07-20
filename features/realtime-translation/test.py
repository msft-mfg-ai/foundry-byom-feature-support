"""Realtime translation session with BYOM-prefixed session.model.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES when
realtime translation rejects the BYOM-prefixed session model. If realtime
translation starts honoring the prefix, or the error shape changes, this test
fails RED and the card must be promoted or updated.
"""
import openai
import pytest


@pytest.mark.not_supported
def test_realtime_translation(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("REALTIME_TRANSLATION_MODEL", "gpt-realtime-1.5"), kind="static")
    model = static_model("REALTIME_TRANSLATION_MODEL", "gpt-realtime-1.5")
    with pytest.raises(openai.APIStatusError) as exc_info:
        aoai.post(
            "/realtime/translations/client_secrets",
            body={"session": {"type": "realtime", "model": model}},
            cast_to=object,
        )

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code >= 400, (
        f"expected BYOM prefix to be rejected, got HTTP {err.status_code}: {body_text[:400]}"
    )
