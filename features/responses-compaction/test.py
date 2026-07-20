"""Responses API compaction with BYOM-prefixed model slots.

Two probes:
1. Inline `context_management` — chain enough turns to exceed `compact_threshold`
   and assert the stored response transitions to a `type='compaction'` input_item.
   This is the only observable that survives the Responses→ChatCompletions
   translation and proves Foundry's state layer actually ran compaction.
2. Standalone `POST /v1/responses/compact` — expected to 404 (endpoint not
   exposed on the project route).
"""
import json
import os
import urllib.error
import urllib.request

import openai
import pytest

from _shared import aad_token, gateway_model


@pytest.mark.partial
def test_responses_compaction_inline_context_management(aoai, cfg):
    """Chain 6 turns above `compact_threshold=1000` and assert Foundry replaces
    the stored history with a `type='compaction'` item."""
    model = gateway_model(os.environ.get("CHAT_MODEL", "gpt-5-mini"), cfg, kind="static")
    filler = ("Please give me a detailed 200-word paragraph. " * 10)
    ctx_mgmt = [{"type": "compaction", "compact_threshold": 1000}]

    prev = None
    ids = []
    for i in range(6):
        kwargs = dict(
            model=model,
            input=f"Turn {i}. {filler} Now write a rich, 200-word paragraph about topic #{i}.",
            extra_body={"context_management": ctx_mgmt},
        )
        if prev:
            kwargs["previous_response_id"] = prev
        r = aoai.responses.create(**kwargs)
        ids.append(r.id)
        prev = r.id

    types_per_turn = []
    for rid in ids:
        items = list(aoai.responses.input_items.list(rid).data)
        types_per_turn.append([it.type for it in items])

    print("types_per_turn=", types_per_turn)
    assert any("compaction" in t for t in types_per_turn), (
        f"Foundry should have replaced the stored history with a compaction item once "
        f"total_tokens crossed 1000, but no turn's input_items contained a 'compaction' entry: "
        f"{types_per_turn}"
    )


@pytest.mark.not_supported
def test_responses_compaction_standalone_endpoint_404(cfg):
    """The standalone /v1/responses/compact endpoint is not exposed on Foundry
    project routes; expect a 404 DeploymentNotFound."""
    model = gateway_model(os.environ.get("CHAT_MODEL", "gpt-5-mini"), cfg, kind="static")
    url = f"{cfg.project_endpoint.rstrip('/')}/openai/v1/responses/compact"
    payload = {
        "model": model,
        "input": [{"type": "message", "role": "user", "content": "hi"}],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + aad_token("https://ai.azure.com/.default"),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=60)
    body = exc.value.read().decode("utf-8", errors="replace")
    assert exc.value.code == 404, f"expected 404, got {exc.value.code}: {body}"
    assert "DeploymentNotFound" in body, f"expected DeploymentNotFound in body, got: {body}"
