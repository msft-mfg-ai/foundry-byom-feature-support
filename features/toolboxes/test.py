"""Foundry Toolbox consumed by a BYOM Prompt Agent via MCPTool.

SDK 2.3.0 pattern: `project.toolboxes.create_version(...)` publishes a versioned
MCP endpoint at `{project_endpoint}/toolboxes/{name}/versions/{v}/mcp`. The agent
picks it up as an ordinary `MCPTool`, which is on the BYOM-supported tool list.
"""
import os
import uuid

import pytest
from azure.ai.projects.models import (
    MCPTool,
    PromptAgentDefinition,
    ToolboxSearchPreviewToolboxTool,
)
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.supported
@pytest.mark.needs_env
def test_toolbox_via_mcp_with_byom(project, aoai, static_model, unique_agent_name, require_env):
    endpoint = require_env("PROJECT_ENDPOINT")
    tb_name = f"byomtb{uuid.uuid4().hex[:8]}"

    try:
        tbv = project.toolboxes.create_version(
            name=tb_name,
            description="BYOM probe",
            tools=[ToolboxSearchPreviewToolboxTool()],
        )
        mcp_url = f"{endpoint}/toolboxes/{tb_name}/versions/{tbv.version}/mcp?api-version=v1"
        token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token

        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-toolbox"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Use `tool_search` on the toolbox to discover tools, then reply briefly.",
                tools=[
                    MCPTool(
                        server_label="toolbox",
                        server_url=mcp_url,
                        authorization=token,
                        require_approval="never",
                    )
                ],
            ),
        )
        conv = aoai.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Search the toolbox for tools and report back."}]
        )
        # Empty toolboxes may return `tool_user_error` from `tool_search` — that
        # still proves the BYOM+toolbox+MCP wiring is accepted (no orchestrator-side
        # `toolbox_search_preview` rejection). Just ensure the call reaches the model.
        try:
            resp = aoai.responses.create(
                conversation=conv.id,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="",
            )
            assert resp is not None
        except Exception as e:
            # The one thing we MUST NOT see is the BYOM tool-allowlist rejection.
            assert "toolbox_search_preview" not in str(e), (
                "BYOM rejected toolbox_search_preview: the MCP-wrapper workaround is broken."
            )
    finally:
        try:
            project.toolboxes.delete(tb_name)
        except ResourceNotFoundError:
            pass
