"""Custom function tool via BYOM-routed Prompt Agent."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition, FunctionTool

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = "byom-tool-functions"


def main() -> int:
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind="static")
    print(f"::group::tool-functions model={model}")

    def get_weather(city: str) -> str:
        return f"It is 72F and sunny in {city}."

    tool = FunctionTool(functions={get_weather})

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=model,
            instructions="Call get_weather to answer. One short sentence.",
            tools=tool.definitions,
        ),
    )
    conv = aoai.conversations.create(items=[{"type": "message", "role": "user", "content": "What's the weather in Seattle?"}])
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
