"""GitHub Copilot SDK pointed at the Foundry project /openai/v1/ endpoint,
using the BYOM `{connection}/{deployment}` prefix as the wire model.

Skips (::warning::) if `github-copilot-sdk` is not installed or the required
env vars are missing. Otherwise sends a one-turn message and asserts the
assistant produced non-empty output.
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

from azure.identity import DefaultAzureCredential

pytest.importorskip("copilot", reason="github-copilot-sdk not installed")

from copilot.client import CopilotClient  # noqa: E402


PROMPT = "Reply with exactly one word: pong"


async def _run(project_endpoint: str, wire_model: str) -> str:
    cred = DefaultAzureCredential()

    def token_provider(_args):
        return cred.get_token("https://ai.azure.com/.default").token

    client = CopilotClient()
    await client.start()
    try:
        collected: list[str] = []
        session = await client.create_session(
            provider={
                "type": "openai",
                "wire_api": "responses",
                "base_url": project_endpoint.rstrip("/") + "/openai/v1/",
                "bearer_token_provider": token_provider,
                "wire_model": wire_model,
            },
        )
        session.on(lambda evt: collected.append(evt.type))
        text = await session.send(PROMPT)
        await session.disconnect()
        return text or ""
    finally:
        await client.stop()


@pytest.mark.not_confirmed
def test_copilot_sdk_via_foundry():
    project_endpoint = os.environ.get("PROJECT_ENDPOINT")
    conn = os.environ.get("AI_GATEWAY_CONNECTION_STATIC")
    model = os.environ.get("CHAT_MODEL")
    if not (project_endpoint and conn and model):
        print(
            "::warning::Skipping — need PROJECT_ENDPOINT, AI_GATEWAY_CONNECTION_STATIC, CHAT_MODEL",
            file=sys.stderr,
        )
        pytest.skip("missing env")

    wire_model = f"{conn}/{model}"
    print(f"::group::copilot-sdk-via-foundry (wire_model={wire_model})")
    try:
        text = asyncio.run(_run(project_endpoint, wire_model))
    finally:
        print("::endgroup::")
    print(f"assistant: {text!r}")
    assert text.strip(), "Copilot session returned empty output"
