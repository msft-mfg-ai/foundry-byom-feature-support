"""Web search tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import (
    BingGroundingSearchConfiguration,
    BingGroundingSearchToolParameters,
    BingGroundingTool,
    PromptAgentDefinition,
)


def _bing_tool(connection_id: str) -> BingGroundingTool:
    return BingGroundingTool(
        bing_grounding=BingGroundingSearchToolParameters(
            search_configurations=[
                BingGroundingSearchConfiguration(project_connection_id=connection_id)
            ]
        )
    )


def _web_search_agent(project, static_model, unique_agent_name, connection_id):
    return project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-web-search"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Use web search to answer. Reply in one short sentence.",
            tools=[_bing_tool(connection_id)],
        ),
    )


def _ask(aoai, agent, conversation_id, question):
    return aoai.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input=question,
    )


@pytest.mark.not_supported
@pytest.mark.needs_env
def test_tool_web_search_rejected_by_byom(project, aoai, static_model, unique_agent_name, require_env):
    """Foundry rejects bing_grounding with 400 when the agent uses a BYOM-prefixed model.

    Server error verbatim:
        The following tools are not supported with BYO model: bing_grounding.
        Please remove these tools or use a standard model deployment.
    """
    import openai
    connection_id = require_env("BING_CONNECTION_ID")
    agent = _web_search_agent(project, static_model, unique_agent_name, connection_id)
    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Search for an AI headline."}]
    )
    with pytest.raises(openai.BadRequestError, match="bing_grounding"):
        _ask(aoai, agent, conv.id, "")
