"""LLM-supported translation via Foundry account endpoint."""
import json
import os
import urllib.error
import urllib.request

import pytest

from _shared import aad_token, account_endpoint, gateway_model


API_VERSION = "2026-06-06"


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Translator deploymentName is expected not to route the BYOM prefix.",
)
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

    try:
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        raise AssertionError(
            f"Translator returned HTTP {e.code}: {body_text}"
        ) from None

    assert payload
