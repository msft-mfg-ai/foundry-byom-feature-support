"""Web search tool via BYOM-routed Prompt Agent."""
import pytest
from azure.ai.projects.models import BingGroundingTool, PromptAgentDefinition


def _web_search_agent(project, static_model, unique_agent_name, connection_id):
    return project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-web-search"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions="Use web search to answer. Reply in one short sentence.",
            tools=[BingGroundingTool(connection_id=connection_id)],
        ),
    )


def _ask(aoai, agent, conversation_id, question):
    return aoai.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input=question,
    )


@pytest.mark.partial
@pytest.mark.needs_env
def test_tool_web_search(project, aoai, static_model, unique_agent_name, require_env):
    connection_id = require_env("BING_CONNECTION_ID")
    agent = _web_search_agent(project, static_model, unique_agent_name, connection_id)
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Search the web for one current headline about AI."}]
    )
    resp = _ask(aoai, agent, conv.id, "")
    assert resp.output_text and resp.output_text.strip()


@pytest.mark.partial
@pytest.mark.needs_env
@pytest.mark.xfail(strict=False, reason="Known regression: second consecutive web-search call can fail.")
def test_tool_web_search_second_consecutive_call(project, aoai, static_model, unique_agent_name, require_env):
    connection_id = require_env("BING_CONNECTION_ID")
    agent = _web_search_agent(project, static_model, unique_agent_name, connection_id)
    assert agent.id

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Search the web for one current headline about AI."}]
    )
    first = _ask(aoai, agent, conv.id, "")
    assert first.output_text and first.output_text.strip()

    second = _ask(aoai, agent, conv.id, "Now search the web again for one current headline about cloud computing.")
    assert second.output_text and second.output_text.strip()


@pytest.mark.partial
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=False,
    reason="Known regression: agent invoking the web-search tool twice within a single turn can fail on the second internal call.",
)
def test_tool_web_search_two_queries_one_turn(project, aoai, static_model, unique_agent_name, require_env):
    """Force the agent to perform TWO web searches inside ONE Responses call.

    Distinct from `test_tool_web_search_second_consecutive_call`, which uses two
    separate turns on the same conversation. Here the model must plan both
    searches and answer in a single response — this exercises the intra-turn
    tool-orchestration path where the second internal `bing_grounding` call has
    been observed to regress.
    """
    connection_id = require_env("BING_CONNECTION_ID")
    agent = project.agents.create_version(
        agent_name=unique_agent_name("byom-tool-web-search-two-in-one"),
        definition=PromptAgentDefinition(
            model=static_model(),
            instructions=(
                "You MUST use the web-search tool separately for each requested topic — "
                "run one search per topic — then combine the findings in a single reply."
            ),
            tools=[BingGroundingTool(connection_id=connection_id)],
        ),
    )
    assert agent.id

    conv = aoai.conversations.create(
        items=[{
            "type": "message",
            "role": "user",
            "content": (
                "In one reply, share (a) one current headline about AI and (b) one current "
                "headline about cloud computing. Search the web for each topic separately."
            ),
        }]
    )
    resp = _ask(aoai, agent, conv.id, "")
    text = (resp.output_text or "").strip()
    assert text
    # Best-effort check that both topics ended up in the answer.
    lower = text.lower()
    assert "ai" in lower or "artificial" in lower
    assert "cloud" in lower
