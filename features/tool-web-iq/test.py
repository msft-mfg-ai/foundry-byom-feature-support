"""Web IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_web_iq(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("WEB_IQ_MCP_URL")
    api_key = require_env("WEB_IQ_API_KEY")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-web-iq"),
        [make_mcp_tool(server_url, "web-iq", auth="None", headers={"x-apikey": api_key})],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Web IQ for one current headline.")
    assert resp.output_text and resp.output_text.strip()
