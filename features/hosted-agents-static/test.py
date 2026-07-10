"""Self-provisioning hosted agent \u2014 static gateway.

Marked @slow because deploying a hosted-agent version cold-starts a container
build (2\u20135 min). Opt-in via `pytest -m slow`.

Flow:
  1. Package a tiny inline agent (main.py + requirements.txt) as an in-memory zip
  2. Create a HostedAgentDefinition version via remote_build (no ACR needed)
  3. Poll until the version is `active`
  4. Invoke via POST to the Invocations endpoint with a bearer token
  5. Assert the response text is non-empty
  6. Delete the version (best-effort cleanup)

Custom env vars passed into the container:
  * AI_GATEWAY_CONNECTION \u2014 static APIM connection name (from cfg)
  * CHAT_MODEL            \u2014 model to route (default gpt-4o-mini)
Platform-injected (do NOT set manually \u2014 reserved FOUNDRY_* prefix):
  * FOUNDRY_PROJECT_ENDPOINT
"""
from __future__ import annotations

import os

import pytest

from _shared import deploy_hosted_byom_probe, invoke_hosted_agent


@pytest.mark.slow
@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Self-provisioning hosted-agent BYOM roundtrip not yet verified end-to-end (remote_build cold-start is slow and flaky).",
)
def test_hosted_agents_static(project, cfg, require_gateway, unique_agent_name):
    gateway = require_gateway("static")
    model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
    agent_name = unique_agent_name("byom-hosted-static")

    try:
        deploy_hosted_byom_probe(project, agent_name, gateway_conn=gateway, model=model)
        result = invoke_hosted_agent(cfg, agent_name, prompt="Say hello in five words.")
        assert result.get("output_text", "").strip(), f"empty response: {result!r}"
    finally:
        try:
            project.agents.delete(agent_name=agent_name, force=True)
        except Exception:  # noqa: BLE001
                pass

