"""Video generation (Sora) with BYOM-prefixed model."""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Video generation endpoint is expected not to parse the BYOM prefix.",
)
def test_video_generation(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("VIDEO_MODEL", "sora-2"), kind="static")
    model = static_model("VIDEO_MODEL", "sora-2")
    job = aoai.videos.create(
        model=model,
        prompt="A tiny blue square moving across a white background.",
    )
    assert getattr(job, "id", None)
