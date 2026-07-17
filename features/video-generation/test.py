"""Video generation (Sora) with a BYOM-prefixed model."""
import os

import openai
import pytest

from _shared import gateway_model


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=False,
    reason="Foundry video generation exposure and BYOM routing are not confirmed.",
)
def test_video_generation(aoai, cfg):
    model = gateway_model(os.environ.get("VIDEO_MODEL", "sora-2"), cfg, kind="static")
    try:
        job = aoai.videos.create(
            model=model,
            prompt="a red dot moves left",
            seconds="4",
            size="1280x720",
        )
    except openai.APIStatusError as e:
        body = getattr(e, "response", None)
        body_text = body.text if body is not None else str(e)
        raise AssertionError(f"videos.create HTTP {e.status_code}: {body_text}") from None
    assert getattr(job, "id", None)
