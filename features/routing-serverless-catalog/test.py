"""Serverless catalog model (Foundry-hosted) via '{conn}/{model}' prefix.

NOT BYOM — the upstream is hosted by Foundry. Same prefix shape though.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

SERVERLESS_CONN = os.environ.get("AI_GATEWAY_CONNECTION_SERVERLESS")
SERVERLESS_MODEL = os.environ.get("SERVERLESS_MODEL")
AGENT_NAME = "byom-serverless"


def main() -> int:
    if not SERVERLESS_CONN or not SERVERLESS_MODEL:
        print("::warning::AI_GATEWAY_CONNECTION_SERVERLESS/SERVERLESS_MODEL not set; skipping")
        return 0
    cfg, project, aoai = build_clients()
    model = f"{SERVERLESS_CONN}/{SERVERLESS_MODEL}"
    print(f"::group::routing-serverless-catalog model={model}")
    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=model, instructions="Reply in one short sentence."),
    )
    conv = aoai.conversations.create(items=[{"type": "message", "role": "user", "content": "Say hello."}])
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
