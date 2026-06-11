"""Embeddings through AI Gateway connection."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("EMBEDDINGS_MODEL", "text-embedding-3-small")


def main() -> int:
    cfg, _, aoai = build_clients()
    model = gateway_model(MODEL, cfg)
    print(f"::group::Embeddings {model}")
    resp = aoai.embeddings.create(model=model, input=["hello world", "byom feature test"])
    dim = len(resp.data[0].embedding)
    print(f"OK: got {len(resp.data)} embeddings, dim={dim}")
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
