"""Prompt Agent backed by a ModelGateway connection (non-OpenAI provider)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MG_CONN = os.environ.get("AI_GATEWAY_CONNECTION_MODELGATEWAY")
MG_MODEL = os.environ.get("MODELGATEWAY_MODEL")
AGENT_NAME = "byom-modelgateway"


def main() -> int:
    if not MG_CONN or not MG_MODEL:
        print("::warning::AI_GATEWAY_CONNECTION_MODELGATEWAY/MODELGATEWAY_MODEL not set; skipping")
        return 0
    cfg, project, aoai = build_clients()
    model = f"{MG_CONN}/{MG_MODEL}"
    print(f"::group::routing-modelgateway-non-openai model={model}")
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
