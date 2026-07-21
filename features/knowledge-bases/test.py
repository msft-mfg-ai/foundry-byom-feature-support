"""BYOM test: knowledge-bases

Foundry IQ Knowledge Bases are hosted by Azure AI Search, not by Foundry.
The KB CREATE endpoint accepts a `{conn}/{deployment}` string in
`models[].azureOpenAIParameters.deploymentId` (returns 201), but the KB
RETRIEVE endpoint has the search service call the model endpoint DIRECTLY
using its own MSI — bypassing the APIM AI Gateway entirely. The retrieve
therefore fails 404 regardless of whether the deployment name has a BYOM
prefix or not (in this account the model is only reachable via APIM).

This test uses raw REST because `azure-ai-projects 2.3.0` doesn't yet
expose the KB retrieve tool. It creates a KB with BYOM-prefixed
deploymentId, asserts CREATE succeeds, asserts RETRIEVE returns a
`model endpoint returned status code '404'` error, then cleans up.
"""
import json
import os
import time

import pytest
import requests
from azure.identity import DefaultAzureCredential


@pytest.mark.not_supported
def test_kb_retrieve_bypasses_byom(cfg):
    search_endpoint = os.environ.get("AZURE_AI_SEARCH_ENDPOINT")
    index_name = os.environ.get("AZURE_AI_SEARCH_INDEX_NAME")
    if not search_endpoint or not index_name:
        pytest.skip("AZURE_AI_SEARCH_ENDPOINT + AZURE_AI_SEARCH_INDEX_NAME not set")

    gateway = cfg.resolve_gateway("static")
    chat_deployment = os.environ.get("CHAT_MODEL", "gpt-4o-mini")
    account_endpoint = os.environ.get(
        "FOUNDRY_ACCOUNT_ENDPOINT",
        "https://ai-foundry-3swd46vd3j22a.services.ai.azure.com",
    )

    cred = DefaultAzureCredential()
    token = cred.get_token("https://search.azure.com/.default").token
    h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    ks_name = "byom-probe-ks"
    kb_name = "byom-probe-kb"
    api = "api-version=2026-05-01-preview"

    ks_body = {"name": ks_name, "kind": "searchIndex",
               "searchIndexParameters": {"searchIndexName": index_name}}
    r = requests.put(f"{search_endpoint}/knowledgesources/{ks_name}?{api}", headers=h, data=json.dumps(ks_body))
    assert r.status_code < 400, f"KS create failed: {r.status_code} {r.text}"
    time.sleep(2)

    try:
        kb_body = {
            "name": kb_name,
            "retrievalInstructions": "Answer briefly.",
            "knowledgeSources": [{"name": ks_name}],
            "models": [{
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": account_endpoint,
                    "deploymentId": f"{gateway}/{chat_deployment}",
                    "modelName": chat_deployment,
                },
            }],
        }
        cr = requests.put(f"{search_endpoint}/knowledgebases/{kb_name}?{api}", headers=h, data=json.dumps(kb_body))
        assert cr.status_code == 201, (
            f"KB CREATE with BYOM-prefixed deploymentId should be accepted at "
            f"config time; got {cr.status_code}: {cr.text}"
        )

        rr = requests.post(
            f"{search_endpoint}/knowledgebases/{kb_name}/retrieve?{api}",
            headers=h,
            data=json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": "hello"}]}]}),
        )
        assert rr.status_code == 404, (
            f"KB RETRIEVE was expected to fail 404 because the search service "
            f"dials the model endpoint directly (BYOM-unaware); got "
            f"{rr.status_code}: {rr.text}"
        )
        assert "model endpoint returned status code '404'" in rr.text, (
            f"Expected the search-service-dials-model 404 shape; got: {rr.text}"
        )
    finally:
        requests.delete(f"{search_endpoint}/knowledgebases/{kb_name}?{api}", headers=h)
        requests.delete(f"{search_endpoint}/knowledgesources/{ks_name}?{api}", headers=h)
