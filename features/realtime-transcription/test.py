"""Realtime transcription session with BYOM-prefixed transcription.model."""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Nested realtime transcription model is expected not to route the BYOM prefix.",
)
def test_realtime_transcription(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("REALTIME_TRANSCRIPTION_MODEL", "gpt-realtime-1.5"), kind="static")
    model = static_model("REALTIME_TRANSCRIPTION_MODEL", "gpt-realtime-1.5")
    session = aoai.beta.realtime.transcription_sessions.create(
        input_audio_transcription={"model": model},
    )
    assert getattr(session, "id", None)
