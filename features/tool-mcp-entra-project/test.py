"""MCP project identity tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="MCP project identity tool BYOM routing is not confirmed.")
def test_tool_mcp_entra_project(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("MCP_SERVER_URL")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-mcp-entra-project"),
        [make_mcp_tool(server_url, "byom-mcp", auth="AgenticIdentity")],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "List one tool exposed by the MCP server.")
    assert resp.output_text and resp.output_text.strip()
