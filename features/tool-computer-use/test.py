"""BYOM test: tool-computer-use"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model, require_env  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = "byom-tool-computer-use"
GATEWAY_KIND = "static"
COMPUTER_USE_ENVIRONMENT = os.environ.get("COMPUTER_USE_ENVIRONMENT")

def main() -> int:
    if not COMPUTER_USE_ENVIRONMENT:
        print("::warning::Missing env for tool-computer-use: COMPUTER_USE_ENVIRONMENT")
        return 0
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind=GATEWAY_KIND)
    print(f"::group::tool-computer-use model={model}")

    from azure.ai.projects.models import ComputerUseTool, ComputerEnvironment
    tools = [ComputerUseTool(environment=ComputerEnvironment(COMPUTER_USE_ENVIRONMENT))]

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
            tools=tools,
        ),
    )
    print(f"agent: id={agent.id} version={agent.version}")

    conversation = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": 'Open example.com in the browser tool and report the page title.'}],
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
