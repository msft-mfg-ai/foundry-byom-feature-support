"""BYOM test: tool-azure-ai-search"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model, require_env  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = "byom-tool-azure-ai-search"
GATEWAY_KIND = "static"
AZURE_AI_SEARCH_CONNECTION_ID = os.environ.get("AZURE_AI_SEARCH_CONNECTION_ID")
AZURE_AI_SEARCH_INDEX_NAME = os.environ.get("AZURE_AI_SEARCH_INDEX_NAME")

def main() -> int:
    if not AZURE_AI_SEARCH_CONNECTION_ID or not AZURE_AI_SEARCH_INDEX_NAME:
        print("::warning::Missing env for tool-azure-ai-search: AZURE_AI_SEARCH_CONNECTION_ID, AZURE_AI_SEARCH_INDEX_NAME")
        return 0
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind=GATEWAY_KIND)
    print(f"::group::tool-azure-ai-search model={model}")

    from azure.ai.projects.models import AzureAISearchTool
    tools = [AzureAISearchTool(connection_id=AZURE_AI_SEARCH_CONNECTION_ID, index_name=AZURE_AI_SEARCH_INDEX_NAME)]

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
        items=[{"type": "message", "role": "user", "content": 'Use Azure AI Search to find one document, return its title.'}],
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
