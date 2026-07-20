"""Foundry IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools, require_env as optional_env


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_foundry_iq(project, aoai, cfg, unique_agent_name):
    server_url = optional_env("FOUNDRY_IQ_MCP_URL", "tool-foundry-iq")
    if not server_url:
        return

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-foundry-iq"),
        [make_mcp_tool(server_url, "foundry_iq", auth="AgenticIdentity")],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Foundry IQ for one fact about this Foundry project.")
    assert resp.output_text and resp.output_text.strip()
