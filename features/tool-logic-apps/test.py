"""Logic Apps tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Logic Apps tool BYOM routing is not confirmed.")
def test_tool_logic_apps(project, aoai, cfg, unique_agent_name, require_env):
    resource_id = require_env("LOGIC_APP_RESOURCE_ID")
    workflow_name = require_env("LOGIC_APP_WORKFLOW_NAME")

    from azure.ai.projects.models import AzureStandardLogicAppTool

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-logic-apps"),
        [AzureStandardLogicAppTool(resource_id=resource_id, workflow_name=workflow_name)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Invoke the logic app and summarize the result in one sentence.")
    assert resp.output_text and resp.output_text.strip()
