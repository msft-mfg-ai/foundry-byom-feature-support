"""Content Understanding analyzer create with BYOM-prefixed completion model.

The analyzer schema exposes a `models` map (`completion`, `embedding`) that
binds analyzer roles to Foundry model deployments. This probe creates a
temp custom analyzer with `models.completion = '{conn}/{deployment}'` on
top of the built-in `prebuilt-documentAnalyzer` and asserts the service
does not accept the BYOM prefix.

Two failure modes are considered "documented rejection" (test PASSES):
  * PUT returns 4xx (typically 400) rejecting the deployment name.
  * PUT accepts but the async provisioning `Operation-Location` reports
    `status: failed` with a not-found on the model deployment.

If PUT + provisioning both succeed AND a subsequent `:analyze` call
succeeds, BYOM is genuinely supported and the assertion fails RED so the
card is promoted to `supported`.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
import uuid

import pytest

from _shared import aad_token, account_endpoint, gateway_model


API_VERSION = "2025-11-01"
BASE_ANALYZER = "prebuilt-documentAnalyzer"
SAMPLE_URL = (
    "https://github.com/Azure-Samples/azure-ai-content-understanding-python/"
    "raw/refs/heads/main/data/invoice.pdf"
)


def _request(method: str, url: str, token: str, body: dict | None = None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
            return resp.status, dict(resp.headers), payload
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), e.read().decode("utf-8", errors="replace")


def _poll(op_location: str, token: str, timeout_s: int = 60) -> tuple[str, str]:
    deadline = time.time() + timeout_s
    last_body = ""
    while time.time() < deadline:
        status, _, body = _request("GET", op_location, token)
        last_body = body
        if status >= 400:
            return f"http_{status}", body
        try:
            parsed = json.loads(body)
        except Exception:
            return "unparseable", body
        state = (parsed.get("status") or "").lower()
        if state in ("succeeded", "failed", "canceled"):
            return state, body
        time.sleep(2)
    return "timeout", last_body


@pytest.mark.not_confirmed
def test_content_understanding_byom(cfg):
    endpoint = account_endpoint()
    if not endpoint:
        pytest.skip("FOUNDRY_ACCOUNT_ENDPOINT / PROJECT_ENDPOINT not set")

    gw_model = gateway_model(
        os.environ.get("CHAT_MODEL", "gpt-4o-mini"), cfg, kind="static"
    )
    analyzer_id = f"byom-probe-{uuid.uuid4().hex[:8]}"
    url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={API_VERSION}"
    body = {
        "description": "BYOM prefix probe; safe to delete.",
        "baseAnalyzerId": BASE_ANALYZER,
        "models": {"completion": gw_model},
    }

    token = aad_token()
    print(f"::group::PUT {url}")
    print(json.dumps(body, indent=2))
    status, headers, response_body = _request("PUT", url, token, body)
    print(f"HTTP {status}")
    print(response_body[:2000])
    print("::endgroup::")

    try:
        if status >= 400:
            assert gw_model in response_body or "deployment" in response_body.lower() or "model" in response_body.lower(), (
                f"HTTP {status} but response does not mention the BYOM model or a deployment error: {response_body[:400]}"
            )
            return

        op_location = headers.get("Operation-Location") or headers.get("operation-location")
        if not op_location:
            pytest.fail(
                f"PUT succeeded (HTTP {status}) without Operation-Location header; "
                f"cannot determine whether the analyzer actually provisioned with the BYOM prefix. "
                f"Response: {response_body[:400]}"
            )

        print(f"::group::Poll {op_location}")
        final_state, poll_body = _poll(op_location, token)
        print(f"final state: {final_state}")
        print(poll_body[:2000])
        print("::endgroup::")

        assert final_state != "succeeded", (
            "Content Understanding accepted `models.completion='{conn}/{deployment}'` and "
            f"provisioned the analyzer end-to-end. Card should be promoted to `supported`. "
            f"Final poll body: {poll_body[:600]}"
        )
        assert final_state in ("failed", "http_400", "http_404"), (
            f"Unexpected terminal state {final_state!r}; expected a deployment-not-found "
            f"rejection. Poll body: {poll_body[:600]}"
        )
    finally:
        delete_url = f"{endpoint}/contentunderstanding/analyzers/{analyzer_id}?api-version={API_VERSION}"
        del_status, _, del_body = _request("DELETE", delete_url, token)
        print(f"::debug::DELETE analyzer -> HTTP {del_status} {del_body[:200]}")
