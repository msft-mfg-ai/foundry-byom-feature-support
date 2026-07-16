"""BYOM test: image-generation-tool.

Attaches the built-in ImageGenTool to a BYOM Prompt Agent. If the image
model slot itself accepts a BYOM `{connection}/{deployment}` prefix, the
tool call succeeds. Historically it does not.
"""
import os

import pytest
from azure.ai.projects.models import ImageGenTool, PromptAgentDefinition


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=False,
    reason="Image generation tool is not in the BYOM-supported tools list.",
)
def test_image_generation_tool(project, aoai, static_model, unique_agent_name, require_env):
    image_deployment_name = require_env("IMAGE_DEPLOYMENT_NAME")
    model = static_model()
    conn = os.environ.get("AI_GATEWAY_CONNECTION_STATIC", "")
    tool_model = f"{conn}/{image_deployment_name}" if conn else image_deployment_name

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-image-generation-tool"),
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
            tools=[ImageGenTool(model=tool_model)],
        ),
    )
    assert agent.id

    conversation = aoai.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": "Generate a small icon of a blue circle, reply with the generated image URL.",
        }],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    assert resp.output_text and resp.output_text.strip()
