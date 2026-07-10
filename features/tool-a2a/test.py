"""A2A tool via BYOM-routed Prompt Agent.

Requires either A2A_PROJECT_CONNECTION_ID (an A2A connection registered
in the Foundry project) or A2A_ENDPOINT (external A2A server URL).
Skips cleanly when neither is set.
"""
import os

import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_supported
@pytest.mark.xfail(strict=True, reason="A2A tools are not in the documented BYOM-supported tools list.")
def test_tool_a2a(project, aoai, cfg, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool

    conn_id = os.environ.get("A2A_PROJECT_CONNECTION_ID")
    endpoint = os.environ.get("A2A_ENDPOINT")
    if not conn_id and not endpoint:
        pytest.skip("A2A_PROJECT_CONNECTION_ID or A2A_ENDPOINT must be set")

    tool = A2APreviewTool(project_connection_id=conn_id) if conn_id else A2APreviewTool()
    if endpoint:
        tool.base_url = endpoint

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-a2a"),
        [tool],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Delegate a one-sentence summary task to the remote agent.")
    assert resp.output_text and resp.output_text.strip()

