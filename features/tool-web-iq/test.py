"""Web IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_web_iq(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("WEB_IQ_MCP_URL")
    # As of azure-ai-projects 2.x, MCPTool no longer accepts custom `headers`
    # server-side (invalid_payload: "Use project_connection_id instead"). Pass
    # the resource id of a Foundry Custom-Keys connection that carries the
    # `x-apikey` header. Skip when the connection isn't wired.
    connection_id = require_env("WEB_IQ_CONNECTION_ID")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-web-iq"),
        [make_mcp_tool(server_url, "web-iq", auth="None", project_connection_id=connection_id)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Web IQ for one current headline.")
    assert resp.output_text and resp.output_text.strip()
