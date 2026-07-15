"""Knowledge Base: register a Foundry Index and query it via a BYOM Prompt Agent."""
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
def test_knowledge_base_create_and_query(project, aoai, static_model, unique_agent_name, require_env):
    """Create a project-level Foundry Index (KB) backed by AI Search, then query it via BYOM.

    The ai-gateway-pe-testing environment has NO Foundry-native model deployments
    on the account itself — every model call flows through APIM. If KB creation
    or query worked only with account-local deployments, this test would fail.
    """
    connection_id = require_env("AZURE_AI_SEARCH_CONNECTION_ID")
    index_name = require_env("AZURE_AI_SEARCH_INDEX_NAME")
    # Search connection is the last segment of the ARM-style connection id.
    connection_name = connection_id.split("/")[-1]

    kb_name = f"byomkb{uuid.uuid4().hex[:8]}"
    try:
        project.indexes.create_or_update(
            name=kb_name,
            version="1",
            index=AzureAISearchIndex(connection_name=connection_name, index_name=index_name),
        )

        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-knowledge-bases"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Use the knowledge base to answer. Reply briefly.",
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
            items=[{"type": "message", "role": "user", "content": "Search the knowledge base and summarize one fact."}]
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
