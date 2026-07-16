"""Memory Search tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Memory Search tool BYOM routing is not confirmed.")
def test_tool_memory(project, aoai, static_model, unique_agent_name, require_env):
    memory_store_id = require_env("MEMORY_STORE_ID")

    try:
        from azure.ai.projects.models import MemorySearchPreviewTool
    except ImportError as exc:
        pytest.xfail(f"MemorySearchPreviewTool is not available in the installed azure-ai-projects package: {exc}")

    tool = MemorySearchPreviewTool(memory_store_name=memory_store_id, scope="byom-pytest", update_delay=1)
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-memory"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Use memory search if relevant. Reply in one short sentence.",
            tools=[tool],
        ),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Remember that BYOM memory probes should use the AI gateway."}]
    )
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
