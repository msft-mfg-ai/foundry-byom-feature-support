"""Prompt Agent backed by a ModelGateway connection (non-OpenAI provider)."""
import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=False,
    reason="ModelGateway non-OpenAI BYOM routing is not yet confirmed.",
)
def test_routing_modelgateway_non_openai(project, aoai, unique_agent_name, require_env):
    connection = require_env("AI_GATEWAY_CONNECTION_MODELGATEWAY")
    model_name = require_env("MODELGATEWAY_MODEL")
    model = f"{connection}/{model_name}"

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-modelgateway"),
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
