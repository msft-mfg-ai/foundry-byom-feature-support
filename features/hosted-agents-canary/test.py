"""Canary hosted agent — BYOM probe matrix invoked from a pre-provisioned agent.

The infra repo (ai-gateway-pe-testing) declares `services: ByomCanaryAgent:` in
its `azure.yaml`. `azd deploy` — via the `azure.ai.agents` extension — builds
the container, pushes to ACR, registers a Foundry Hosted Agent version, and
exports `HOSTED_AGENT_NAME_CANARY` as an azd env var. That's the name we invoke
here.

The container's `agent.yaml` wires its env from azd:
  BYOM_MODEL           = ${AI_GATEWAY_CONNECTION_STATIC}/${CHAT_MODEL}
  BYOM_MODEL_ANTHROPIC = ${AI_GATEWAY_CONNECTION_ANTHROPIC}/${ANTHROPIC_MODEL}

Inside the container, `main.py` runs one Responses call per configured model and
returns a JSON matrix { ok: bool, tests: [{name, ok, error?}, ...] }. This test
asserts every sub-probe returned ok=True.

Skips gracefully if `HOSTED_AGENT_NAME_CANARY` is unset (i.e. the infra repo
hasn't been `azd deploy`-ed against this GH env).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import invoke_hosted_agent  # noqa: E402


@pytest.mark.not_confirmed
def test_hosted_agents_canary(cfg):
    agent_name = os.environ.get("HOSTED_AGENT_NAME_CANARY")
    if not agent_name:
        pytest.skip("HOSTED_AGENT_NAME_CANARY unset (run `azd deploy` in ai-gateway-pe-testing first)")

    result = invoke_hosted_agent(cfg, agent_name, prompt="Reply with the single word: ok.")
    tests = result.get("tests") or []
    assert tests, f"canary returned no sub-tests: {result!r}"

    failures = [t for t in tests if not t.get("ok")]
    assert not failures, "canary sub-probes failed:\n" + "\n".join(
        f"  - {t.get('name')}: {t.get('error')}" for t in failures
    )
