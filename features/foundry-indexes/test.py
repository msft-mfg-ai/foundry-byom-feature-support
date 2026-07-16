"""Foundry Index (project.indexes) + AzureAISearchTool consumed by a BYOM Prompt Agent.

This is the lower-level 'Indexes' primitive — NOT the Foundry IQ 'Knowledge bases'
surface, which needs Standard-SKU AI Search + semantic ranker + network access.
"""
import uuid

import pytest
from azure.ai.projects.models import (
    AISearchIndexResource,
    AzureAISearchIndex,
    AzureAISearchTool,
    AzureAISearchToolResource,
    PromptAgentDefinition,
)


@pytest.mark.supported
@pytest.mark.needs_env
def test_foundry_index_registered_and_queried(project, aoai, static_model, unique_agent_name, require_env):
    connection_id = require_env("AZURE_AI_SEARCH_CONNECTION_ID")
    index_name = require_env("AZURE_AI_SEARCH_INDEX_NAME")
    connection_name = connection_id.split("/")[-1]

    kb_name = f"byomidx{uuid.uuid4().hex[:8]}"
    try:
        project.indexes.create_or_update(
            name=kb_name,
            version="1",
            index=AzureAISearchIndex(connection_name=connection_name, index_name=index_name),
        )
        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-foundry-index"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Search the index and summarize one result briefly.",
                tools=[
                    AzureAISearchTool(
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
                ],
            ),
        )
        conv = aoai.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Search the index and summarize."}]
        )
        resp = aoai.responses.create(
            conversation=conv.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input="",
        )
        assert resp.output_text and resp.output_text.strip()
    finally:
        try:
            project.indexes.delete(name=kb_name, version="1")
        except Exception:
            pass
