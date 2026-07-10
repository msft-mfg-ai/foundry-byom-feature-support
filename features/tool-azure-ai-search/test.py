"""Azure AI Search tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Azure AI Search tool BYOM routing is not confirmed.")
def test_tool_azure_ai_search(project, aoai, cfg, unique_agent_name, require_env):
    connection_id = require_env("AZURE_AI_SEARCH_CONNECTION_ID")
    index_name = require_env("AZURE_AI_SEARCH_INDEX_NAME")

    from azure.ai.projects.models import AzureAISearchTool

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-azure-ai-search"),
        [AzureAISearchTool(connection_id=connection_id, index_name=index_name)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Use Azure AI Search to find one document, return its title.")
    assert resp.output_text and resp.output_text.strip()
