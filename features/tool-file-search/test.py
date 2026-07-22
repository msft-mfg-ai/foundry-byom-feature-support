"""BYOM test: tool-file-search

Vector stores are ephemeral OpenAI resources — create + delete one per run
instead of requiring a pre-provisioned store in the environment.
"""
import io

import pytest
from azure.ai.projects.models import FileSearchTool, PromptAgentDefinition


@pytest.mark.supported
def test_tool_file_search(project, aoai, static_model, unique_agent_name):
    model = static_model()

    doc = io.BytesIO(
        b"Project Aurora is the internal codename for the BYOM feature-support "
        b"matrix. Aurora ships with a curated set of Prompt Agent tools.\n"
    )
    doc.name = "aurora.txt"
    uploaded = aoai.files.create(file=doc, purpose="assistants")

    vs = aoai.vector_stores.create(name=f"byom-file-search-{uploaded.id[:8]}")
    aoai.vector_stores.files.create_and_poll(vector_store_id=vs.id, file_id=uploaded.id)

    agent = None
    try:
        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-tool-file-search"),
            definition=PromptAgentDefinition(
                model=model,
                instructions="You are a concise assistant. Reply in one short sentence.",
                tools=[FileSearchTool(vector_store_ids=[vs.id])],
            ),
        )
        assert agent.id

        conversation = aoai.conversations.create(
            items=[{
                "type": "message",
                "role": "user",
                "content": "What is Project Aurora, according to the indexed files?",
            }],
        )
        resp = aoai.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input="",
        )
        assert resp.output_text and resp.output_text.strip()
        assert "aurora" in resp.output_text.lower(), (
            f"Expected the file-search tool to surface content from aurora.txt; got: {resp.output_text}"
        )
    finally:
        try:
            aoai.vector_stores.delete(vs.id)
        except Exception:
            pass
        try:
            aoai.files.delete(uploaded.id)
        except Exception:
            pass


