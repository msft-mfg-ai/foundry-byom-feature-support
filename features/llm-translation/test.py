"""LLM-supported translation via Foundry account endpoint.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES when
Translator treats the BYOM `{connection}/{model}` string as a literal deployment
name and rejects it. If Translator starts parsing the prefix, or the error shape
changes, this test fails RED and the card must be promoted or updated.
"""
import json
import os
import urllib.error
import urllib.request

import pytest

from _shared import aad_token, account_endpoint, gateway_model


API_VERSION = "2026-06-06"


@pytest.mark.not_supported
def test_llm_translation(cfg):
    endpoint = account_endpoint()
    if not endpoint:
        pytest.skip("PROJECT_ENDPOINT/FOUNDRY_ACCOUNT_ENDPOINT not set")
    region = os.environ.get("FOUNDRY_REGION", "eastus2")
    gw_model = gateway_model(os.environ.get("CHAT_MODEL", "gpt-5-mini"), cfg, kind="static")
    url = f"{endpoint}/translator/text/translate?api-version={API_VERSION}"
    body = {
        "inputs": [
            {
                "text": "The quick brown fox jumps over the lazy dog.",
                "language": "en",
                "targets": [{"language": "fr", "deploymentName": gw_model}],
            }
        ]
    }
    token = aad_token()
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Region": region,
        },
        method="POST",
    )

    with pytest.raises(urllib.error.HTTPError) as exc_info:
        with urllib.request.urlopen(req) as resp:
            json.loads(resp.read().decode("utf-8"))

    err = exc_info.value
    body_text = err.read().decode("utf-8", errors="replace")
    assert err.code == 400, f"expected HTTP 400, got {err.code}: {body_text[:400]}"
    assert "Failed to get information on deployment" in body_text
    assert gw_model in body_text
