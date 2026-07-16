"""GitHub Copilot SDK pointed directly at APIM (bypassing Foundry).

No BYOM `{connection}/{deployment}` prefix here — APIM is already the
gateway, so `wire_model` is just the deployment name at APIM.

Skips (::warning::) if `github-copilot-sdk` or the APIM env vars are
missing. Auth: subscription key via header, OR `APIM_BEARER_TOKEN` if the
gateway is Entra-fronted.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

pytest.importorskip("copilot", reason="github-copilot-sdk not installed")

from copilot.client import CopilotClient  # noqa: E402


PROMPT = "Reply with exactly one word: pong"


async def _run(base_url: str, wire_model: str, api_key: str | None, bearer: str | None) -> str:
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


@pytest.mark.not_confirmed
def test_copilot_sdk_via_apim_direct():
    base_url = os.environ.get("APIM_BASE_URL")
    wire_model = os.environ.get("APIM_DEPLOYMENT") or os.environ.get("CHAT_MODEL")
    api_key = os.environ.get("APIM_SUBSCRIPTION_KEY")
    bearer = os.environ.get("APIM_BEARER_TOKEN")
    if not base_url or not wire_model or not (api_key or bearer):
        print(
            "::warning::Skipping — need APIM_BASE_URL, APIM_DEPLOYMENT (or CHAT_MODEL), "
            "and APIM_SUBSCRIPTION_KEY or APIM_BEARER_TOKEN",
            file=sys.stderr,
        )
        pytest.skip("missing env")

    print(f"::group::copilot-sdk-via-apim-direct (base_url={base_url}, wire_model={wire_model})")
    try:
        text = asyncio.run(_run(base_url, wire_model, api_key, bearer))
    finally:
        print("::endgroup::")
    print(f"assistant: {text!r}")
    assert text.strip(), "Copilot session returned empty output"
