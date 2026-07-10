"""Prompt Agent (v2) via the static AI Gateway connection.

Reference conversion for the "supported" shape: BYOM works, so assertions
directly gate CI.
"""
import os

import pytest
from azure.ai.projects.models import PromptAgentDefinition


AGENT_NAME_ENV = "PROMPT_AGENT_NAME_STATIC"
AGENT_NAME_DEFAULT = "byom-prompt-static"


@pytest.mark.supported
def test_prompt_agent_static(project, aoai, static_model, unique_agent_name):
    model = static_model()
    agent_name = os.environ.get(AGENT_NAME_ENV) or unique_agent_name(AGENT_NAME_DEFAULT)

    agent = project.agents.create_version(
        agent_name=agent_name,
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
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

