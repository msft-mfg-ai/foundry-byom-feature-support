"""Realtime translation session with BYOM-prefixed session.model."""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Realtime translation endpoint is expected not to route the BYOM prefix.",
)
def test_realtime_translation(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("REALTIME_TRANSLATION_MODEL", "gpt-realtime-1.5"), kind="static")
    model = static_model("REALTIME_TRANSLATION_MODEL", "gpt-realtime-1.5")
    raw = aoai.post(
        "/realtime/translations/client_secrets",
        body={"session": {"type": "realtime", "model": model}},
        cast_to=object,
    )
    assert raw
