"""Reasoning model via BYOM, validating reasoning_effort forwarding."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

REASONING_MODEL = os.environ.get("REASONING_MODEL")


def main() -> int:
    if not REASONING_MODEL:
        print("::warning::REASONING_MODEL not set; skipping reasoning-models-byom")
        return 0
    cfg, project, aoai = build_clients()
    model = gateway_model(REASONING_MODEL, cfg, kind="static")
    print(f"::group::reasoning-models-byom model={model}")
    resp = aoai.responses.create(
        model=model,
        input="What is 7 * 8? Think briefly then answer.",
        extra_body={"reasoning": {"effort": "low"}, "max_completion_tokens": 256},
    )
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
