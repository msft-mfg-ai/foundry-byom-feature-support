"""Direct image generation endpoint with BYOM-prefixed model.

Reference conversion for a "not_supported" endpoint probe. Marked strict-xfail
so that if OpenAI/Foundry ever start honoring the BYOM prefix here, CI turns
red and the matrix card must be promoted.
"""
import os

import openai
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Image generation endpoint is expected NOT to parse the {conn}/{model} BYOM prefix.",
)
def test_image_generation_direct(aoai, static_model, require_model):
    model_name = os.environ.get("IMAGE_MODEL", "gpt-image-2")
    require_model(model_name, kind="static")
    model = static_model("IMAGE_MODEL", "gpt-image-2")
    try:
        result = aoai.images.generate(
            model=model,
            prompt="a small blue circle icon",
            size="1024x1024",
            n=1,
        )
    except openai.APIStatusError as e:
        body = getattr(e, "response", None)
        body_text = body.text if body is not None else str(e)
        raise AssertionError(f"images.generate HTTP {e.status_code}: {body_text}") from None
    assert getattr(result.data[0], "url", None) or getattr(result.data[0], "b64_json", None)

