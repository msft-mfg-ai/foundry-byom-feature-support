"""Batch API with BYOM-prefixed model on each JSONL line.

Positive-assertion probe for a `not_supported` endpoint: the test PASSES when
Foundry rejects the Batch API path with 404, showing the BYOM-prefixed per-line
model is irrelevant because `/batches` is not exposed. If the endpoint appears
or the error shape changes, this test fails RED and the card must be promoted
or updated.
"""
import io
import json

import openai
import pytest


@pytest.mark.not_supported
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

    with pytest.raises(openai.APIStatusError) as exc_info:
        uploaded = aoai.files.create(file=buf, purpose="batch")
        aoai.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code == 404, f"expected HTTP 404, got {err.status_code}: {body_text[:400]}"
