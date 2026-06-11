"""BYOM test: tool-mcp-oauth-passthrough"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model, require_env  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
AGENT_NAME = "byom-tool-mcp-oauth-passthrough"
GATEWAY_KIND = "static"
MCP_SERVER_URL_OAUTH = os.environ.get("MCP_SERVER_URL_OAUTH")

def main() -> int:
    if not MCP_SERVER_URL_OAUTH:
        print("::warning::Missing env for tool-mcp-oauth-passthrough: MCP_SERVER_URL_OAUTH")
        return 0
    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind=GATEWAY_KIND)
    print(f"::group::tool-mcp-oauth-passthrough model={model}")

    from _shared import make_mcp_tool
    tools = [make_mcp_tool(MCP_SERVER_URL_OAUTH, "byom-mcp-oauth", auth="UserEntraToken")]

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
        items=[{"type": "message", "role": "user", "content": 'List one tool exposed by the MCP server.'}],
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
