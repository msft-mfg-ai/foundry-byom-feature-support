"""SharePoint grounding tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_sharepoint(project, aoai, cfg, unique_agent_name, require_env):
    connection_id = require_env("SHAREPOINT_CONNECTION_ID")

    from azure.ai.projects.models import SharepointPreviewTool

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-sharepoint"),
        [SharepointPreviewTool(connection_id=connection_id)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Search SharePoint for one document and return its title.")
    assert resp.output_text and resp.output_text.strip()
