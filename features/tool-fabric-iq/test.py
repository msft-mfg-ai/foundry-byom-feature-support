"""Fabric IQ MCP tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(strict=True, reason="Fabric IQ is not in the documented BYOM-supported tools list.")
def test_tool_fabric_iq(project, aoai, cfg, unique_agent_name, require_env):
    server_url = require_env("FABRIC_IQ_MCP_URL")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-fabric-iq"),
        [make_mcp_tool(server_url, "fabric-iq", auth="AgenticIdentity")],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Ask Fabric IQ for one workspace name.")
    assert resp.output_text and resp.output_text.strip()
