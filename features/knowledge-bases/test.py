"""Knowledge Base tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Knowledge Base tool BYOM routing is not confirmed.")
def test_knowledge_bases(project, aoai, static_model, unique_agent_name, require_env):
    knowledge_base_id = require_env("KNOWLEDGE_BASE_ID")

    try:
        from azure.ai.projects.models import KnowledgeBaseTool
    except ImportError:
        KnowledgeBaseTool = None

    tools = []
    instructions = "You are a concise assistant. Reply in one short sentence."
    if KnowledgeBaseTool is not None:
        try:
            tools = [KnowledgeBaseTool(knowledge_base_id=knowledge_base_id)]
        except TypeError:
            tools = [KnowledgeBaseTool(knowledge_base_ids=[knowledge_base_id])]
        instructions = "Use the knowledge base to answer. Reply in one short sentence."

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-knowledge-bases"),
        definition=PromptAgentDefinition(model=static_model(), instructions=instructions, tools=tools),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Use the knowledge base if available and summarize one relevant fact."}]
    )
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
