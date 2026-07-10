"""Foundry IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Foundry IQ tool BYOM routing is not confirmed.")
def test_tool_foundry_iq(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("FOUNDRY_IQ_MCP_URL")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-foundry-iq"),
        [make_mcp_tool(server_url, "foundry-iq", auth="AgenticIdentity")],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Foundry IQ for one fact about this Foundry project.")
    assert resp.output_text and resp.output_text.strip()
