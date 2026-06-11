"""Web search tool via BYOM-routed Prompt Agent.

Known bug: the FIRST web-search invocation succeeds, but the SECOND (and
all subsequent) web-search calls in the same conversation fail. This test
runs two consecutive turns and reports both outcomes so the regression
status is visible in CI.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
BING_CONNECTION_ID = os.environ.get("BING_CONNECTION_ID")
AGENT_NAME = "byom-tool-web-search"


def _ask(aoai, agent, conversation_id, question):
    return aoai.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input=question,
    )


def main() -> int:
    if not BING_CONNECTION_ID:
        print("::warning::BING_CONNECTION_ID not set; skipping tool-web-search")
        return 0

    from azure.ai.projects.models import BingGroundingTool

    cfg, project, aoai = build_clients()
    model = gateway_model(MODEL, cfg, kind="static")
    print(f"::group::tool-web-search model={model}")

    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(
            model=model,
            instructions="Use web search to answer. Reply in one short sentence.",
            tools=[BingGroundingTool(connection_id=BING_CONNECTION_ID)],
        ),
    )
    print(f"agent: id={agent.id} version={agent.version}")

    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Search the web for one current headline about AI."}],
    )

    first_ok = second_ok = False
    try:
        r1 = _ask(aoai, agent, conv.id, "")
        print("FIRST CALL OK:", r1.output_text[:200])
        first_ok = True
    except Exception as e:
        print(f"::error::FIRST CALL FAILED: {type(e).__name__}: {e}")

    try:
        r2 = _ask(aoai, agent, conv.id, "Now search the web again for one current headline about cloud computing.")
        print("SECOND CALL OK:", r2.output_text[:200])
        second_ok = True
    except Exception as e:
        print(f"::warning::SECOND CALL FAILED (known bug): {type(e).__name__}: {e}")

    print("::endgroup::")
    # Fail only if the FIRST call broke; document the 2nd-call regression via a warning
    if not first_ok:
        return 1
    if not second_ok:
        print("::warning::Web search partial: 2nd consecutive call failed (known regression)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
