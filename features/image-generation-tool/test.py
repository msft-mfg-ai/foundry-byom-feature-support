"""BYOM test: image-generation-tool.

Positive-assertion probe for a `not_supported` tool: the test PASSES when
Foundry rejects ImageGenTool on a BYOM Prompt Agent with the documented
`image_generation` error. If the tool starts working with BYOM, or the error
shape changes, this test fails RED and the card must be promoted or updated.
"""
import os

import openai
import pytest
from azure.ai.projects.models import ImageGenTool, PromptAgentDefinition


@pytest.mark.not_supported
@pytest.mark.needs_env
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
    with pytest.raises(openai.BadRequestError, match="image_generation") as exc_info:
        aoai.responses.create(
            conversation=conversation.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input="",
        )

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code == 400, f"expected HTTP 400, got {err.status_code}: {body_text[:400]}"
    assert "not supported with BYO model" in body_text
