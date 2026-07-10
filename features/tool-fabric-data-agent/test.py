"""Fabric Data Agent tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_fabric_data_agent(project, aoai, cfg, unique_agent_name, require_env):
    connection_id = require_env("FABRIC_CONNECTION_ID")

    from azure.ai.projects.models import MicrosoftFabricPreviewTool

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-fabric-data-agent"),
        [MicrosoftFabricPreviewTool(connection_id=connection_id)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Query the Fabric data agent for a simple aggregate.")
    assert resp.output_text and resp.output_text.strip()
