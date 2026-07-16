"""Work IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Work IQ tool BYOM routing is not confirmed.")
def test_tool_work_iq(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("WORK_IQ_MCP_URL")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-work-iq"),
        [make_mcp_tool(server_url, "work-iq", auth="AgenticIdentity")],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Work IQ for the title of one recent email.")
    assert resp.output_text and resp.output_text.strip()
