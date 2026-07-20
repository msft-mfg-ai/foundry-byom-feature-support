"""Video generation (Sora) with a BYOM-prefixed model.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES when
Foundry rejects the video create path with the documented 404. If video
generation starts honoring the BYOM prefix, or the error shape changes, this
test fails RED and the card must be promoted or updated.
"""
import os

import openai
import pytest

from _shared import gateway_model


@pytest.mark.not_supported
def test_video_generation(aoai, cfg):
    model = gateway_model(os.environ.get("VIDEO_MODEL", "sora-2"), cfg, kind="static")
    with pytest.raises(openai.NotFoundError) as exc_info:
        aoai.videos.create(
            model=model,
            prompt="a red dot moves left",
            seconds="4",
            size="1280x720",
        )

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else ""
    assert err.status_code == 404, f"expected HTTP 404, got {err.status_code}: {body_text[:400]}"
    assert not body_text.strip(), f"expected empty 404 body, got: {body_text[:400]}"
