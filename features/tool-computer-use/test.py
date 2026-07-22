"""Computer Use tool via BYOM-routed Prompt Agent."""
import pytest

from _shared import invoke_agent, make_prompt_agent_with_tools


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_computer_use(project, aoai, cfg, unique_agent_name, require_env):
    environment = require_env("COMPUTER_USE_ENVIRONMENT")

    try:
        from azure.ai.projects.models import ComputerEnvironment, ComputerUsePreviewTool as ComputerUseTool
    except ImportError:
        try:
            from azure.ai.projects.models import ComputerEnvironment, ComputerUseTool
        except ImportError:
            pytest.skip("ComputerUseTool/ComputerUsePreviewTool not available in installed azure-ai-projects version")

    agent = make_prompt_agent_with_tools(
        project,
        unique_agent_name("byom-tool-computer-use"),
        [ComputerUseTool(environment=ComputerEnvironment(environment))],
        instructions="You are a concise assistant. Reply in one short sentence.",
        cfg=cfg,
    )
    assert agent.id

    resp = invoke_agent(aoai, agent, "Open example.com in the browser tool and report the page title.")
    assert resp.output_text and resp.output_text.strip()
