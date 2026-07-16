"""Code Interpreter tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.supported
def test_tool_code_interpreter(project, aoai, cfg, unique_agent_name):
    from azure.ai.projects.models import CodeInterpreterTool

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-code-interpreter"),
        [CodeInterpreterTool()],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Compute 17 * 23 using the code interpreter and reply with the result.")
    assert resp.output_text and resp.output_text.strip()
