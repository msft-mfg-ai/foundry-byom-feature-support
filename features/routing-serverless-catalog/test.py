"""Serverless catalog model (Foundry-hosted) via '{conn}/{model}' prefix."""
import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.supported
@pytest.mark.needs_env
def test_routing_serverless_catalog(project, aoai, unique_agent_name, require_env):
    connection = require_env("AI_GATEWAY_CONNECTION_SERVERLESS")
    model_name = require_env("SERVERLESS_MODEL")
    model = f"{connection}/{model_name}"

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-serverless"),
        definition=PromptAgentDefinition(
            model=model,
            instructions="Reply in one short sentence.",
        ),
    )
    assert agent.id
    assert agent.definition.model == model

    conversation = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Say hello."}],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
