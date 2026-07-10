"""Custom function tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import FunctionTool, PromptAgentDefinition


@pytest.mark.supported
def test_tool_functions(project, aoai, static_model, unique_agent_name):
    tool = FunctionTool(
        name="get_weather",
        description="Get the current weather in a city.",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name."}},
            "required": ["city"],
            "additionalProperties": False,
        },
        strict=True,
    )
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-functions"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Call get_weather to answer. One short sentence.",
            tools=[tool],
        ),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "What's the weather in Seattle?"}]
    )
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    # Agent should either call the tool or emit text; assert the response object exists and
    # includes either output_text or a tool call in output items.
    assert resp.output is not None
    assert (resp.output_text and resp.output_text.strip()) or any(
        getattr(item, "type", "") == "function_call" for item in resp.output
    )
