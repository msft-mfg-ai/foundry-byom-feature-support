"""Image variations (DALL·E 2) with BYOM-prefixed model."""
import io

import pytest


TINY_PNG = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
    "890000000D49444154789C6300010000000500010D0A2DB40000000049454E44AE426082"
)


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Image variations endpoint is expected not to parse the BYOM prefix.",
)
def test_image_variations(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("IMAGE_VARIATION_MODEL", "dall-e-2"), kind="static")
    model = static_model("IMAGE_VARIATION_MODEL", "dall-e-2")
    image = io.BytesIO(TINY_PNG)
    image.name = "tiny.png"

    result = aoai.images.create_variation(model=model, image=image, n=1, size="256x256")
    assert getattr(result.data[0], "url", None) or getattr(result.data[0], "b64_json", None)
