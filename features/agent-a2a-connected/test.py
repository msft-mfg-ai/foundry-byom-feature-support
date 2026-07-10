"""BYOM test: agent-a2a-connected

Creates a small Prompt Agent to act as the "remote" A2A target so the test
is self-contained. If A2A_REMOTE_AGENT_ENDPOINT is set it overrides this.
"""
import os

import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="A2A connected agents with a BYOM-routed orchestrator are not yet confirmed.",
)
def test_agent_a2a_connected(cfg, project, aoai, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool

    remote_endpoint = os.environ.get("A2A_REMOTE_AGENT_ENDPOINT")
    if not remote_endpoint:
        remote = project.agents.create_version(
            agent_name=unique_agent_name("byom-a2a-remote"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="You are a summarizer. Reply with one short sentence.",
                tools=[],
            ),
        )
        # Best-effort default endpoint format; Foundry exposes Prompt Agents
        # at /agents/<name> when A2A discovery is enabled on the account.
        remote_endpoint = f"{cfg.project_endpoint.rstrip('/')}/agents/{remote.name}"

    tools = [A2APreviewTool(endpoint=remote_endpoint)]
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-agent-a2a-connected"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="You are a concise assistant. Delegate to the remote A2A agent.",
            tools=tools,
        ),
    )
    assert agent.id

    conversation = aoai.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": "Delegate a one-sentence summary task to the connected agent.",
        }],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
