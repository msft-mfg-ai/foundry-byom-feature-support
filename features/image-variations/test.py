"""Image variations (DALL·E 2) with BYOM-prefixed model.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES when
Foundry rejects image variations for the BYOM-prefixed DALL·E 2 model. If the
endpoint starts accepting the prefix, or the error shape changes, this test
fails RED and the card must be promoted or updated.
"""
import io

import openai
import pytest


TINY_PNG = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
    "890000000D49444154789C6300010000000500010D0A2DB40000000049454E44AE426082"
)


@pytest.mark.not_supported
def test_image_variations(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("IMAGE_VARIATION_MODEL", "dall-e-2"), kind="static")
    model = static_model("IMAGE_VARIATION_MODEL", "dall-e-2")
    image = io.BytesIO(TINY_PNG)
    image.name = "tiny.png"

    with pytest.raises(openai.APIStatusError) as exc_info:
        aoai.images.create_variation(model=model, image=image, n=1, size="256x256")

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code >= 400, (
        f"expected BYOM prefix to be rejected, got HTTP {err.status_code}: {body_text[:400]}"
    )
