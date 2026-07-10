"""A2A tool via BYOM-routed Prompt Agent.

Self-contained: spins up a small remote Prompt Agent when
A2A_REMOTE_AGENT_ENDPOINT isn't set.
"""
import os

import pytest
from azure.ai.projects.models import PromptAgentDefinition

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.not_supported
@pytest.mark.xfail(strict=True, reason="A2A tools are not in the documented BYOM-supported tools list.")
def test_tool_a2a(project, aoai, cfg, static_model, unique_agent_name):
    from azure.ai.projects.models import A2APreviewTool

    endpoint = os.environ.get("A2A_REMOTE_AGENT_ENDPOINT")
    if not endpoint:
        remote = project.agents.create_version(
            agent_name=unique_agent_name("byom-a2a-remote-tool"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Reply with one short sentence.",
                tools=[],
            ),
        )
        endpoint = f"{cfg.project_endpoint.rstrip('/')}/agents/{remote.name}"

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-a2a"),
        [A2APreviewTool(endpoint=endpoint)],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Delegate a one-sentence summary task to the remote agent.")
    assert resp.output_text and resp.output_text.strip()
