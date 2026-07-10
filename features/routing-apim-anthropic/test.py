"""Prompt Agent backed by an APIM connection that fronts Anthropic."""
import os

import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.supported
@pytest.mark.needs_env
def test_routing_apim_anthropic(project, aoai, unique_agent_name, require_env):
    connection = require_env("AI_GATEWAY_CONNECTION_ANTHROPIC")
    model_name = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6")
    model = f"{connection}/{model_name}"

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-anthropic"),
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
