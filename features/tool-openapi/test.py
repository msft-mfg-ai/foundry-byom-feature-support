"""OpenAPI tool with BYOM-routed orchestrator."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
SPEC_PATH = os.environ.get("OPENAPI_SPEC_PATH")
AGENT_NAME = "byom-tool-openapi"


def main() -> int:
    if not SPEC_PATH:
        print("::warning::OPENAPI_SPEC_PATH not set; skipping tool-openapi")
        return 0
    try:
        from azure.ai.projects.models import OpenApiTool, OpenApiAnonymousAuthDetails
    except ImportError as e:
        print(f"::warning::OpenApiTool not in installed azure-ai-projects: {e}; skipping")
        return 0

    spec = json.loads(Path(SPEC_PATH).read_text())
    tool = OpenApiTool(
        name="openapi",
        description="Generic OpenAPI tool",
        spec=spec,
        auth=OpenApiAnonymousAuthDetails(),
    )

    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind="static")
    print(f"::group::tool-openapi model={model}")

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=model, instructions="Use the OpenAPI tool to answer. One sentence.", tools=[tool]),
    )
    conv = aoai.conversations.create(items=[{"type": "message", "role": "user", "content": "Call one operation from the API and summarize the result."}])
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
