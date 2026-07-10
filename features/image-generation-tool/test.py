"""BYOM test: image-generation-tool"""
import pytest
from azure.ai.projects.models import PromptAgentDefinition


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=True,
    reason="Image generation tool is expected not to route through a BYOM orchestrator model.",
)
def test_image_generation_tool(project, aoai, static_model, unique_agent_name, require_env):
    image_deployment_name = require_env("IMAGE_DEPLOYMENT_NAME")
    model = static_model()

    from azure.ai.projects.models import ImageGenTool

    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-image-generation-tool"),
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a concise assistant. Reply in one short sentence.",
            tools=[ImageGenTool(deployment_name=image_deployment_name)],
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
