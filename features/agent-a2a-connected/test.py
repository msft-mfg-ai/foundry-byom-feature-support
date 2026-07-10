"""BYOM test: agent-a2a-connected

Self-provisions a callee Prompt Agent (BYOM-routed), attaches an AgentCard
via PATCH `/agents/{name}` (SDK does not surface this method — see
`_shared.attach_agent_card`), then wires a caller Prompt Agent whose
A2APreviewTool.base_url points at the callee's auto-materialised
`/endpoint/protocols/a2a` URL.

The BYOM concern is that the caller-side orchestrator's model prefix
survives the A2A tool wiring. Cross-agent A2A auth (401 on caller \u2192
callee) is a separate infra issue tracked outside this repo.
"""
import os

import pytest

from _shared import attach_agent_card


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Full A2A roundtrip needs registered A2A connection for cross-agent auth; BYOM routing of the caller orchestrator alone works.",
)
def test_agent_a2a_connected(project, cfg, aoai, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool, PromptAgentDefinition

    callee_name = unique_agent_name("byom-a2a-callee")
    caller_name = unique_agent_name("byom-a2a-caller")

    try:
        project.agents.create_version(
            agent_name=callee_name,
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Reply with a one-sentence summary of the user request.",
                tools=[],
            ),
        )
        a2a_url = attach_agent_card(cfg, callee_name, description="BYOM A2A callee")

        conn_id = os.environ.get("A2A_PROJECT_CONNECTION_ID")
        if conn_id:
            tool = A2APreviewTool(project_connection_id=conn_id, name="summarizer", description="Remote summarizer")
        else:
            tool = A2APreviewTool(base_url=a2a_url, name="summarizer", description="Remote summarizer")

        caller = project.agents.create_version(
            agent_name=caller_name,
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="When asked to summarize, delegate to the summarizer tool.",
                tools=[tool],
            ),
        )
        assert caller.id

        resp = aoai.responses.create(
            input="Summarize this: The quick brown fox jumps over the lazy dog.",
            extra_body={"agent_reference": {"name": caller.name, "type": "agent_reference"}},
        )
        assert resp.output_text and resp.output_text.strip()
    finally:
        for n in (caller_name, callee_name):
            try:
                project.agents.delete(agent_name=n, force=True)
            except Exception:
                pass

