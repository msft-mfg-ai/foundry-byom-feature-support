"""Direct Responses API call with BYOM model, no agent.

Reference conversion for a "supported" endpoint probe. Also asserts Foundry's
Responses state layer (retrieve, previous_response_id, input_items, delete) works
with a BYOM-prefixed model, even though the upstream call is downconverted to
chat/completions (see feature.json for APIM-side capture).
"""
import pytest


@pytest.mark.supported
def test_responses_direct(aoai, static_model):
    model = static_model()
    resp = aoai.responses.create(
        model=model,
        input="Say hello in one short sentence.",
    )
    assert resp.output_text and resp.output_text.strip()


@pytest.mark.supported
def test_responses_state_layer(aoai, static_model):
    """Foundry stores Responses state pre-translation and exposes retrieve /
    previous_response_id / input_items / delete for BYOM-prefixed responses."""
    model = static_model()
    marker = "STATE-PROBE-42"
    created = aoai.responses.create(
        model=model,
        instructions=f"You are a marker echoer. Reply with exactly: {marker}",
        input="what is the marker?",
    )
    assert marker in created.output_text

    got = aoai.responses.retrieve(created.id)
    assert got.id == created.id
    # State is stored pre-translation: instructions is preserved as a top-level
    # Responses field (not flattened to a system message) and model retains the
    # full BYOM {conn}/{deployment} prefix.
    assert got.instructions and marker in got.instructions
    assert "/" in (got.model or ""), f"expected BYOM prefix in stored model, got {got.model!r}"

    items = aoai.responses.input_items.list(created.id)
    assert any("what is the marker" in (getattr(c, "text", "") or "")
               for it in items.data for c in it.content), "input_items missing original user turn"

    chained = aoai.responses.create(
        model=model,
        input="repeat the marker you just gave.",
        previous_response_id=created.id,
    )
    assert marker in chained.output_text, "previous_response_id did not carry conversation state"

    aoai.responses.delete(created.id)
    import openai
    with pytest.raises(openai.APIStatusError) as exc:
        aoai.responses.retrieve(created.id)
    assert exc.value.status_code == 404

