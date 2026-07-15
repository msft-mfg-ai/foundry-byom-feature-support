"""Azure AI Search tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchTool,
    AzureAISearchToolResource,
    PromptAgentDefinition,
)


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_azure_ai_search(project, aoai, static_model, unique_agent_name, require_env):
    connection_id = require_env("AZURE_AI_SEARCH_CONNECTION_ID")
    index_name = require_env("AZURE_AI_SEARCH_INDEX_NAME")

    tool = AzureAISearchTool(
        azure_ai_search=AzureAISearchToolResource(
            indexes=[
                AISearchIndexResource(
                    project_connection_id=connection_id,
                    index_name=index_name,
                    query_type="simple",
                    top_k=3,
                )
            ]
        )
    )
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-azure-ai-search"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Use the search tool to answer. Reply briefly.",
            tools=[tool],
        ),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Search the index and summarize one result."}]
    )
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
