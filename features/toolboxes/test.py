"""Toolboxes: BYOM rejects `toolbox_search_preview` on agent invocation."""
import openai
import pytest
from azure.ai.projects.models import (
    MCPTool,
    PromptAgentDefinition,
    ToolboxSearchPreviewTool,
)


@pytest.mark.not_supported
@pytest.mark.needs_env
def test_toolbox_rejected_by_byom(project, aoai, static_model, unique_agent_name, require_env):
    """Toolbox creation succeeds, but attaching it to a BYOM-prefixed agent is rejected.

    Server error verbatim:
        The following tools are not supported with BYO model: toolbox_search_preview.
        Please remove these tools or use a standard model deployment.
    """
    mcp_url = require_env("MCP_SERVER_URL")
    toolbox_name = unique_agent_name("byomtb").replace("-", "").lower()[:24]

    project.beta.toolboxes.create_version(
        name=toolbox_name,
        tools=[MCPTool(server_label="probe", server_url=mcp_url, require_approval="never")],
    )
    try:
        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-toolbox"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Discover and use tools from the toolbox.",
                tools=[ToolboxSearchPreviewTool(name=toolbox_name)],
            ),
        )
        conv = aoai.conversations.create(
            items=[{"type": "message", "role": "user", "content": "hi"}]
        )
        with pytest.raises(openai.BadRequestError, match="toolbox_search_preview"):
            aoai.responses.create(
                conversation=conv.id,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="",
            )
    finally:
        project.beta.toolboxes.delete(name=toolbox_name)
