"""OpenAPI tool via BYOM-routed Prompt Agent."""
import json
from pathlib import Path

import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.supported
@pytest.mark.needs_env
def test_tool_openapi(project, aoai, static_model, unique_agent_name, require_env):
    spec_path = require_env("OPENAPI_SPEC_PATH")
    try:
        from azure.ai.projects.models import OpenApiAnonymousAuthDetails, OpenApiTool
    except ImportError as exc:
        pytest.skip(f"OpenApiTool is not available in the installed azure-ai-projects package: {exc}")

    spec = json.loads(Path(spec_path).read_text())
    tool = OpenApiTool(
        name="openapi",
        description="Generic OpenAPI tool",
        spec=spec,
        auth=OpenApiAnonymousAuthDetails(),
    )
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-openapi"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Use the OpenAPI tool to answer. One sentence.",
            tools=[tool],
        ),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Call one operation from the API and summarize the result."}]
    )
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
