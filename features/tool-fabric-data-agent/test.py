"""BYOM test: tool-fabric-data-agent"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model, require_env  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = "byom-tool-fabric-data-agent"
GATEWAY_KIND = "static"
FABRIC_CONNECTION_ID = os.environ.get("FABRIC_CONNECTION_ID")

def main() -> int:
    if not FABRIC_CONNECTION_ID:
        print("::warning::Missing env for tool-fabric-data-agent: FABRIC_CONNECTION_ID")
        return 0
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind=GATEWAY_KIND)
    print(f"::group::tool-fabric-data-agent model={model}")

    from azure.ai.projects.models import MicrosoftFabricPreviewTool
    tools = [MicrosoftFabricPreviewTool(connection_id=FABRIC_CONNECTION_ID)]

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
        items=[{"type": "message", "role": "user", "content": 'Query the Fabric data agent for a simple aggregate.'}],
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
