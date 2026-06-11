"""LLM-supported translation via Foundry account endpoint.

Probes whether the translator's targets[].deploymentName accepts the BYOM
'{conn}/{model}' prefix. Account-level endpoint, not project-level.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import account_endpoint, aad_token, gateway_model, load_config  # noqa: E402

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")
REGION = os.environ.get("FOUNDRY_REGION", "eastus2")
API_VERSION = "2026-06-06"


def main() -> int:
    endpoint = account_endpoint()
    if not endpoint:
        print("::warning::FOUNDRY_ACCOUNT_ENDPOINT not set; skipping llm-translation")
        return 0
    cfg = load_config()
    gw_model = gateway_model(MODEL, cfg, kind="static")
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
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Region": REGION,
        },
        method="POST",
    )
    print(f"::group::llm-translation POST {url} deploymentName={gw_model}")
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8")
            print("OK:", payload[:500])
            print("::endgroup::")
            return 0
    except urllib.error.HTTPError as e:
        print(f"::error::HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:500]}")
        print("::endgroup::")
        return 1


if __name__ == "__main__":
    sys.exit(main())
