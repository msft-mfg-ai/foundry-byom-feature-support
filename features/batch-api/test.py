"""Batch API with BYOM-prefixed model on each JSONL line."""
import io
import json

import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=False,
    reason="Verified: Foundry project OpenAI client returns 404 NotFound on aoai.batches.create — /batches endpoint is not exposed by the Foundry Responses surface (BYOM prefix is irrelevant).",
)
def test_batch_api(aoai, static_model):
    model = static_model()
    line = {
        "custom_id": "req-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {"model": model, "messages": [{"role": "user", "content": "hi"}]},
    }
    buf = io.BytesIO(json.dumps(line).encode() + b"\n")
    buf.name = "batch.jsonl"

    uploaded = aoai.files.create(file=buf, purpose="batch")
    assert uploaded.id

    batch = aoai.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    assert batch.id
    assert batch.status
