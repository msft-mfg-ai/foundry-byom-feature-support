"""A2A tool via BYOM-routed Prompt Agent.

Same self-provisioning pattern as agent-a2a-connected: creates a callee
Foundry Prompt Agent, attaches an AgentCard (PATCH `/agents/{name}` \u2014
not exposed on the SDK; see `_shared.attach_agent_card`), then attaches
the callee's `/endpoint/protocols/a2a` URL as a tool on a caller agent.
"""
import os

import pytest

from _shared import attach_agent_card, invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="A2A tools are not in the documented BYOM-supported tools list; cross-agent auth returns 401 without a registered A2A connection.",
)
def test_tool_a2a(project, aoai, cfg, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool, PromptAgentDefinition

    callee_name = unique_agent_name("byom-a2a-tool-callee")
    caller_name = unique_agent_name("byom-tool-a2a")

    try:
        project.agents.create_version(
            agent_name=callee_name,
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Reply with a one-sentence summary.",
                tools=[],
            ),
        )
        a2a_url = attach_agent_card(cfg, callee_name, description="BYOM A2A tool callee")

        conn_id = os.environ.get("A2A_PROJECT_CONNECTION_ID")
        if conn_id:
            tool = A2APreviewTool(project_connection_id=conn_id, name="summarizer", description="Remote summarizer")
        else:
            tool = A2APreviewTool(base_url=a2a_url, name="summarizer", description="Remote summarizer")

        agent = make_prompt_agent_with_tools(
            project,
            caller_name,
            [tool],
            instructions="You are a concise assistant. Reply in one short sentence.",
            cfg=cfg,
        )
        assert agent.id

        resp = invoke_agent(aoai, agent, "Delegate a one-sentence summary task to the remote agent.")
        assert resp.output_text and resp.output_text.strip()
    finally:
        for n in (caller_name, callee_name):
            try:
                project.agents.delete(agent_name=n, force=True)
            except Exception:
                pass

