"""Invoke a pre-deployed Hosted Agent (static gateway).

The hosted agent itself must already exist in the Foundry project (deployed
via HostedAgentDefinition with a container or code configuration). This test
only validates that BYOM routing through the static APIM gateway works when
the hosted agent is invoked through the Responses API.
"""
import pytest


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=False,
    reason="Hosted agents through the static gateway are not yet confirmed.",
)
def test_hosted_agents_static(project, aoai, require_env):
    agent_name = require_env("HOSTED_AGENT_NAME_STATIC")

    agent = project.agents.get(agent_name=agent_name)
    assert agent.id

    conversation = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Say hello."}],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
