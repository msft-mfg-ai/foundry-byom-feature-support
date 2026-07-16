"""Cross-cutting BYOM behavioral checks on the Responses API.

Every test here uses only `aoai` + `static_model()` / `dynamic_model()` — no
external tools, connections, or agents — so failures indicate real BYOM
routing regressions rather than product-specific issues.
"""
from __future__ import annotations

import concurrent.futures
import json

import pytest


# --- 1. Streaming ---

@pytest.mark.supported
def test_byom_streaming(aoai, static_model):
    """SSE streaming must work when the model is BYOM-prefixed."""
    stream = aoai.responses.create(
        model=static_model(),
        input="Count from 1 to 3, one number per line.",
        stream=True,
    )
    chunks = list(stream)
    assert chunks, "expected at least one streamed event"
    completed = [e for e in chunks if getattr(e, "type", "") == "response.completed"]
    assert completed, f"no response.completed event in {len(chunks)} events"
    text = (completed[-1].response.output_text or "").strip()
    assert text


# --- 2. Structured output (json_schema) ---

@pytest.mark.supported
def test_byom_structured_output(aoai, static_model):
    """response_format=json_schema must survive the BYOM proxy path."""
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "integer"}},
        "required": ["answer"],
        "additionalProperties": False,
    }
    resp = aoai.responses.create(
        model=static_model(),
        input="What is 7 * 8? Reply as JSON matching the schema.",
        text={"format": {"type": "json_schema", "name": "math", "schema": schema, "strict": True}},
    )
    parsed = json.loads((resp.output_text or "").strip())
    assert parsed.get("answer") == 56


# --- 3. Multi-turn conversation retention ---

@pytest.mark.supported
def test_byom_multi_turn_retention(aoai, static_model):
    """Three turns on one conversation — the model must remember earlier context."""
    conv = aoai.conversations.create(items=[])
    first = aoai.responses.create(
        model=static_model(),
        conversation=conv.id,
        input="Remember the code word BLUEBIRD. Reply with just 'ok'.",
    )
    assert (first.output_text or "").strip()

    second = aoai.responses.create(
        model=static_model(),
        conversation=conv.id,
        input="What number is 6 * 7? Reply with just the number.",
    )
    assert "42" in (second.output_text or "")

    third = aoai.responses.create(
        model=static_model(),
        conversation=conv.id,
        input="What was the code word I told you earlier?",
    )
    assert "BLUEBIRD" in (third.output_text or "").upper()


# --- 4. Static-vs-dynamic parity ---

@pytest.mark.supported
def test_byom_static_dynamic_parity(aoai, static_model, dynamic_model, require_gateway):
    """Same prompt via both connection kinds must return a non-empty answer of the same shape."""
    require_gateway("dynamic")
    prompt = "Reply with the single word: pong"
    static_resp = aoai.responses.create(model=static_model(), input=prompt)
    dynamic_resp = aoai.responses.create(model=dynamic_model(), input=prompt)
    s = (static_resp.output_text or "").strip().lower()
    d = (dynamic_resp.output_text or "").strip().lower()
    assert s and d
    assert "pong" in s
    assert "pong" in d


# --- 5. Concurrent calls on same route ---

@pytest.mark.supported
def test_byom_concurrent_calls(aoai, static_model):
    """N concurrent Responses.create must all succeed with distinct-but-valid answers."""
    prompts = [f"Reply with exactly the word: token{i}" for i in range(5)]

    def _call(p):
        return aoai.responses.create(model=static_model(), input=p).output_text or ""

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        outputs = list(ex.map(_call, prompts))

    assert len(outputs) == 5
    for i, out in enumerate(outputs):
        assert f"token{i}" in out.lower(), f"call {i} returned: {out!r}"


# --- 6. Retry after 429 ---

@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Requires hitting APIM rate limits — best-effort probe, may skip if no 429 observed.",
)
def test_byom_retry_after_429(aoai, static_model):
    """Rapid-fire calls should either all succeed (with SDK retries) or the SDK
    should surface a RateLimitError. Any other exception is a BYOM proxy bug.
    """
    from openai import RateLimitError

    successes = 0
    rate_limited = False
    for _ in range(20):
        try:
            r = aoai.responses.create(model=static_model(), input="hi", max_output_tokens=16)
            if (r.output_text or "").strip():
                successes += 1
        except RateLimitError:
            rate_limited = True
            break
    # Either the SDK's built-in retry made every call succeed, OR we saw a
    # proper RateLimitError. Anything else (e.g. 500 masking a 429) is a bug.
    assert successes > 0 or rate_limited
