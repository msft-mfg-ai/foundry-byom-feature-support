"""Image generation through AI Gateway connection."""
import base64
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-2")


def main() -> int:
    cfg, _, aoai = build_clients()
    model = gateway_model(MODEL, cfg)
    print(f"::group::Image generation {model}")
    img = aoai.images.generate(
        model=model,
        prompt="A cute robot painting a watercolor of a mountain at sunrise.",
        size="1024x1024",
        n=1,
    )
    data = img.data[0]
    out = Path(__file__).parent / "out.png"
    if getattr(data, "b64_json", None):
        out.write_bytes(base64.b64decode(data.b64_json))
        print(f"OK: wrote {out} ({out.stat().st_size} bytes)")
    elif getattr(data, "url", None):
        print(f"OK url: {data.url}")
    else:
        print("OK but no image payload:", data)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
