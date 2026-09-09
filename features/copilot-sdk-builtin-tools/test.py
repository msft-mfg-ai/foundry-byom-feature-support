"""Copilot SDK built-in tools (shell + files) via the BYOK APIM route.

Invokes the `copilot-canary` hosted agent from the ai-gateway-pe-testing infra
repo and asserts that every sub-probe (`chat`, `bash`, `files`) reported ok.
The hosted agent auto-approves every `on_permission_request` per the
Agent Framework devblog pattern:
https://devblogs.microsoft.com/agent-framework/build-ai-agents-with-github-copilot-sdk-and-microsoft-agent-framework/

Skips gracefully if `HOSTED_AGENT_NAME_COPILOT_CANARY` is unset (i.e. the
infra repo hasn't been `azd deploy`-ed against this GH env yet).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import invoke_hosted_agent  # noqa: E402


@pytest.mark.not_confirmed
def test_copilot_sdk_builtin_tools(cfg):
    agent_name = os.environ.get("HOSTED_AGENT_NAME_COPILOT_CANARY")
    if not agent_name:
        pytest.skip("HOSTED_AGENT_NAME_COPILOT_CANARY unset (run `azd deploy` in ai-gateway-pe-testing first)")

    print(f"::group::copilot-sdk-builtin-tools (via {agent_name!r})")
    try:
        result = invoke_hosted_agent(cfg, agent_name, prompt="run all probes")
    finally:
        print("::endgroup::")

    tests = result.get("tests") or []
    names = {t.get("name") for t in tests}
    assert {"chat", "bash", "files"}.issubset(names), (
        f"canary must return chat+bash+files sub-probes, got names={names!r}: {result!r}"
    )

    failures = [t for t in tests if not t.get("ok")]
    assert not failures, "canary sub-probes failed:\n" + "\n".join(
        f"  - {t.get('name')}: {t.get('error') or t.get('output_text')!r}" for t in failures
    )
