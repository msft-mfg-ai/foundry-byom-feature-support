"""A2A tool via BYOM-routed Prompt Agent.

Positive-assertion probe for a `not_supported` tool: the test PASSES when the
caller reaches the A2A tool path and Foundry rejects fetching the callee agent
card with the documented 424 Failed Dependency. If A2A tools start working with
BYOM, or the error shape changes, this test fails RED and the card must be
promoted or updated.
"""
import os

import openai
import pytest

from _shared import attach_agent_card, invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_supported
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
            tool = A2APreviewTool(project_connection_id=conn_id)
        else:
            tool = A2APreviewTool(base_url=a2a_url)

        agent = make_prompt_agent_with_tools(
            project,
            caller_name,
            [tool],
            instructions="You are a concise assistant. Reply in one short sentence.",
            cfg=cfg,
        )
        assert agent.id

        with pytest.raises(openai.BadRequestError, match="Failed to fetch agent card") as exc_info:
            invoke_agent(aoai, agent, "Delegate a one-sentence summary task to the remote agent.")

        err = exc_info.value
        body = getattr(err, "response", None)
        body_text = body.text if body is not None else str(err)
        assert err.status_code == 400, f"expected HTTP 400, got {err.status_code}: {body_text[:400]}"
        assert "424 (Failed Dependency)" in body_text
    finally:
        for n in (caller_name, callee_name):
            try:
                project.agents.delete(agent_name=n, force=True)
            except Exception:
                pass

