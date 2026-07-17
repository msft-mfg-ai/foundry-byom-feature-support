"""Responses API compaction with BYOM-prefixed model slots."""
import json
import os
import urllib.error
import urllib.request

import openai
import pytest

from _shared import aad_token, gateway_model


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=False,
    reason="Responses compaction support on Foundry is not confirmed.",
)
def test_responses_compaction(aoai, cfg):
    model = gateway_model(os.environ.get("CHAT_MODEL", "gpt-5-mini"), cfg, kind="static")
    observations = []

    try:
        resp = aoai.responses.create(
            model=model,
            input="hello",
            extra_body={"context_management": [{"type": "compaction", "compact_threshold": 200000}]},
        )
        observations.append(
            f"responses.create context_management OK: status={resp.status!r}, output_text={resp.output_text!r}"
        )
    except openai.APIStatusError as e:
        body = getattr(e, "response", None)
        body_text = body.text if body is not None else str(e)
        observations.append(f"responses.create context_management HTTP {e.status_code}: {body_text}")

    url = f"{cfg.project_endpoint.rstrip('/')}/openai/v1/responses/compact"
    payload = {
        "model": model,
        "input": [{"type": "message", "role": "user", "content": "hi"}],
    }
    auth_value = "Bearer " + aad_token("https://ai.azure.com/.default")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": auth_value,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            body = response.read().decode("utf-8", errors="replace")
        observations.append(f"responses.compact HTTP {response.status}: {body}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        observations.append(f"responses.compact HTTP {e.code}: {body}")

    verdict = "\n".join(observations)
    print(verdict)
    assert "responses.create context_management OK" in verdict and "responses.compact HTTP 2" in verdict, verdict
