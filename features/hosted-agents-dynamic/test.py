"""Self-provisioning hosted agent — dynamic gateway.

Mirrors hosted-agents-static but routes through the dynamic-discovery APIM
connection. See hosted-agents-static/test.py for full docstring.
"""
from __future__ import annotations

import os

import pytest

from _shared import deploy_hosted_byom_probe, invoke_hosted_agent


@pytest.mark.slow
@pytest.mark.not_confirmed
def test_hosted_agents_dynamic(project, cfg, require_gateway, unique_agent_name):
    gateway = require_gateway("dynamic")
    model = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
    agent_name = unique_agent_name("byom-hosted-dynamic")

    version = None
    try:
        version = deploy_hosted_byom_probe(project, agent_name, gateway_conn=gateway, model=model)
        result = invoke_hosted_agent(cfg, agent_name, prompt="Say hello in five words.")
        assert result.get("output_text", "").strip(), f"empty response: {result!r}"
    finally:
        if version is not None:
            try:
                project.agents.delete_version(agent_name=agent_name, agent_version=version)
            except Exception:  # noqa: BLE001
                pass
