"""Direct image generation endpoint with BYOM-prefixed model.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES
when Foundry rejects the BYOM prefix (as documented). If Foundry starts
honoring the prefix here, the test fails RED and the card must be
promoted.
"""
import os

import openai
import pytest


@pytest.mark.not_supported
def test_image_generation_direct(aoai, static_model, require_model):
    model_name = os.environ.get("IMAGE_MODEL", "gpt-image-2")
    require_model(model_name, kind="static")
    model = static_model("IMAGE_MODEL", "gpt-image-2")
    with pytest.raises(openai.APIStatusError) as exc_info:
        aoai.images.generate(
            model=model,
            prompt="a small blue circle icon",
            size="1024x1024",
            n=1,
        )
    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else ""
    assert err.status_code >= 400, (
        f"expected BYOM prefix to be rejected, got HTTP {err.status_code}: {body_text[:400]}"
    )

