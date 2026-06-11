"""Direct image generation endpoint with BYOM-prefixed model.

Documents whether POST /openai/v1/images/generations parses the
'{conn}/{model}' prefix. Research suggests it does not.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")


def main() -> int:
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind="static")
    print(f"::group::image-generation-direct model={model}")
    try:
        result = aoai.images.generate(model=model, prompt="a small blue circle icon", size="1024x1024", n=1)
        print("OK:", getattr(result.data[0], "url", "(no url)")[:200])
        print("::endgroup::")
        return 0
    except Exception as e:
        print(f"::warning::Failed (expected if endpoint does not parse BYOM prefix): {e}")
        print("::endgroup::")
        return 0


if __name__ == "__main__":
    sys.exit(main())
