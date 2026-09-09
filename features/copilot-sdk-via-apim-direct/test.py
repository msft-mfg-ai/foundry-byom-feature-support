"""GitHub Copilot SDK pointed directly at APIM (bypassing Foundry).

No BYOM `{connection}/{deployment}` prefix here — APIM is already the
gateway, so `wire_model` is just the deployment name at APIM.

Two invocation paths, in preference order:
1. If `HOSTED_AGENT_NAME_COPILOT_CANARY` is set, invoke the Copilot canary
   hosted agent (which lives inside the Foundry VNet and can reach APIM's
   private endpoint) and assert its `chat` sub-probe passed. This is the
   only path that meaningfully confirms the topology when APIM has
   `publicNetworkAccess=disabled`.
2. Otherwise run the direct CopilotClient path from the runner. Requires
   line-of-sight to APIM (i.e. self-hosted VNet runner).
Skips (::warning::) if neither path is wired.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import invoke_hosted_agent  # noqa: E402


PROMPT = "Reply with exactly one word: pong"


async def _run_direct(base_url: str, wire_model: str, api_key: str | None, bearer: str | None) -> str:
    pytest.importorskip("copilot", reason="github-copilot-sdk not installed")
    from copilot.client import CopilotClient  # noqa: WPS433
    client = CopilotClient()
    await client.start()
    try:
        provider: dict = {
            "type": "openai",
            "wire_api": "responses",
            "base_url": base_url.rstrip("/") + "/",
            "wire_model": wire_model,
        }
        if api_key:
            provider["api_key"] = api_key
            provider["headers"] = {"Ocp-Apim-Subscription-Key": api_key}
        elif bearer:
            provider["bearer_token"] = bearer

        session = await client.create_session(provider=provider)
        text = await session.send(PROMPT)
        await session.disconnect()
        return text or ""
    finally:
        await client.stop()


@pytest.mark.supported
def test_copilot_sdk_via_apim_direct(cfg):
    hosted = os.environ.get("HOSTED_AGENT_NAME_COPILOT_CANARY")
    if hosted:
        print(f"::group::copilot-sdk-via-apim-direct (via hosted agent {hosted!r})")
        try:
            result = invoke_hosted_agent(cfg, hosted, prompt=PROMPT)
        finally:
            print("::endgroup::")
        tests = result.get("tests") or []
        chat = next((t for t in tests if t.get("name") == "chat"), None)
        assert chat and chat.get("ok"), f"canary chat probe failed: {result!r}"
        return

    base_url = os.environ.get("APIM_BASE_URL")
    wire_model = os.environ.get("APIM_DEPLOYMENT") or os.environ.get("CHAT_MODEL")
    api_key = os.environ.get("APIM_SUBSCRIPTION_KEY")
    bearer = os.environ.get("APIM_BEARER_TOKEN")
    if not base_url or not wire_model or not (api_key or bearer):
        print(
            "::warning::Skipping — set HOSTED_AGENT_NAME_COPILOT_CANARY (preferred, "
            "invokes the VNet-reachable canary), or APIM_BASE_URL + "
            "APIM_DEPLOYMENT/CHAT_MODEL + APIM_SUBSCRIPTION_KEY/APIM_BEARER_TOKEN.",
            file=sys.stderr,
        )
        pytest.skip("no invocation path available")

    print(f"::group::copilot-sdk-via-apim-direct (direct, base_url={base_url}, wire_model={wire_model})")
    try:
        text = asyncio.run(_run_direct(base_url, wire_model, api_key, bearer))
    finally:
        print("::endgroup::")
    print(f"assistant: {text!r}")
    assert text.strip(), "Copilot session returned empty output"
