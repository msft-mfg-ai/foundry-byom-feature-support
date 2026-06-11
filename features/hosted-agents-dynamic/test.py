"""Invoke a pre-deployed Hosted Agent (dynamic gateway).

The hosted agent itself must already exist in the Foundry project (deployed
via HostedAgentDefinition with a container or code configuration). This test
only validates that BYOM routing through the dynamic APIM gateway works when
the hosted agent is invoked through the Responses API.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients  # noqa: E402

AGENT_NAME = os.environ.get("HOSTED_AGENT_NAME_DYNAMIC")


def main() -> int:
    if not AGENT_NAME:
        print("::warning::HOSTED_AGENT_NAME_DYNAMIC not set; skipping hosted-agents-dynamic test")
        return 0

    cfg, project, aoai = build_clients()
    print(f"::group::Hosted agent (dynamic) {AGENT_NAME}")

    agent = project.agents.get(agent_name=AGENT_NAME)
    print(f"agent: id={agent.id} kind={getattr(agent.versions.latest.definition, 'kind', '?')}")

    conversation = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Say hello."}],
    )
    resp = aoai.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )
    print("OK:", resp.output_text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
