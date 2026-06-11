"""Prompt Agent backed by an APIM connection that fronts Anthropic."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients  # noqa: E402

from azure.ai.projects.models import PromptAgentDefinition

ANTHROPIC_CONN = os.environ.get("AI_GATEWAY_CONNECTION_ANTHROPIC")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-6")
AGENT_NAME = "byom-anthropic"


def main() -> int:
    if not ANTHROPIC_CONN:
        print("::warning::AI_GATEWAY_CONNECTION_ANTHROPIC not set; skipping")
        return 0
    cfg, project, aoai = build_clients()
    model = f"{ANTHROPIC_CONN}/{ANTHROPIC_MODEL}"
    print(f"::group::routing-apim-anthropic model={model}")
    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=model, instructions="Reply in one short sentence."),
    )
    conv = aoai.conversations.create(items=[{"type": "message", "role": "user", "content": "Say hello."}])
    resp = aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
