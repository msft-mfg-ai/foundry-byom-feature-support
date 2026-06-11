"""Prompt Agent (v2) via the dynamic AI Gateway connection."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = os.environ.get("PROMPT_AGENT_NAME_DYNAMIC", "byom-prompt-dynamic")
GATEWAY_KIND = "dynamic"


def main() -> int:
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind=GATEWAY_KIND)
    print(f"::group::Prompt agent ({GATEWAY_KIND}) {AGENT_NAME} model={model}")

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
        ),
    )
    print(f"agent: id={agent.id} version={agent.version} model={agent.definition.model}")

    conversation = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Say hello."}],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
