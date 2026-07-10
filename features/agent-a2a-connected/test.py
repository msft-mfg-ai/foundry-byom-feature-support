"""BYOM test: agent-a2a-connected

An A2A tool needs a real A2A server \u2014 either a Foundry-registered A2A
connection (A2A_PROJECT_CONNECTION_ID) or an external endpoint speaking
the A2A protocol (A2A_ENDPOINT). Skips cleanly when neither is set,
because a Prompt Agent alone is NOT an A2A server (Foundry does not
auto-expose /agents/<name> as A2A).
"""
import os

import pytest


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="A2A connected agents with a BYOM-routed orchestrator are not yet confirmed.",
)
def test_agent_a2a_connected(project, aoai, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool, PromptAgentDefinition

    conn_id = os.environ.get("A2A_PROJECT_CONNECTION_ID")
    endpoint = os.environ.get("A2A_ENDPOINT")
    if not conn_id and not endpoint:
        pytest.skip("A2A_PROJECT_CONNECTION_ID or A2A_ENDPOINT must be set (Foundry Prompt Agents are not A2A servers)")

    tool = A2APreviewTool(project_connection_id=conn_id) if conn_id else A2APreviewTool()
    if endpoint:
        tool.base_url = endpoint

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-agent-a2a-connected"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="You are a concise assistant. Delegate to the remote A2A agent when asked.",
            tools=[tool],
        ),
    )
    assert agent.id

    resp = aoai.responses.create(
        input="Delegate a one-sentence summary task to the connected agent.",
        tool_choice="required",
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
    )
    assert resp.output_text and resp.output_text.strip()

