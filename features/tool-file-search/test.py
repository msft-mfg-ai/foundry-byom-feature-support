"""BYOM test: tool-file-search

Reference conversion for a "needs env" probe: the vector-store id is optional,
so we self-skip when it isn't provided.
"""
import pytest
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_file_search(project, aoai, static_model, unique_agent_name, require_env):
    vector_store_id = require_env("FILE_SEARCH_VECTOR_STORE_ID")
    model = static_model()

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-file-search"),
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
            tools=[FileSearchTool(vector_store_ids=[vector_store_id])],
        ),
    )
    assert agent.id

    conversation = aoai.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": "Search the indexed files for an interesting term and quote one line.",
        }],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()

