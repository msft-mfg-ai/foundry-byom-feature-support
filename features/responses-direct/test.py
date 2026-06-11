"""Direct Responses API call with BYOM model, no agent."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")


def main() -> int:
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind="static")
    print(f"::group::responses-direct model={model}")
    resp = aoai.responses.create(model=model, input="Say hello in one short sentence.")
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
