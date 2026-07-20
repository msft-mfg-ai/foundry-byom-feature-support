"""Fabric IQ MCP tool via BYOM-routed Prompt Agent.

Positive-assertion probe for a `not_supported` tool: the test PASSES when a
Fabric IQ tool attached to a BYOM Prompt Agent is rejected. If Fabric IQ starts
working with BYOM, or the error shape changes, this test fails RED and the card
must be promoted or updated.
"""
import openai
import pytest

from _shared import invoke_agent, make_mcp_tool, make_prompt_agent_with_tools


@pytest.mark.not_supported
@pytest.mark.needs_env
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

    with pytest.raises(openai.APIStatusError) as exc_info:
        invoke_agent(aoai, agent, "Ask Fabric IQ for one workspace name.")

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code >= 400, (
        f"expected Fabric IQ BYOM tool rejection, got HTTP {err.status_code}: {body_text[:400]}"
    )
