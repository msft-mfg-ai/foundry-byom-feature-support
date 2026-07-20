"""Assistants v2 (beta): create assistant + run with BYOM-prefixed model.

Positive-assertion probe for a `not_supported` legacy agent path: the test
PASSES when Assistants rejects the BYOM-prefixed model before completing the
assistant run. If Assistants starts honoring the prefix, or the error shape
changes, this test fails RED and the card must be promoted or updated.
"""
import openai
import pytest


@pytest.mark.not_supported
def test_assistants_v2(aoai, static_model):
    model = static_model()
    assistant = None
    try:
        with pytest.raises(openai.APIStatusError) as exc_info:
            assistant = aoai.beta.assistants.create(
                name="byom-probe",
                model=model,
                instructions="Be terse.",
            )
            thread = aoai.beta.threads.create(messages=[{"role": "user", "content": "Say hi."}])
            aoai.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=assistant.id,
            )
    finally:
        if assistant is not None:
            aoai.beta.assistants.delete(assistant.id)

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code >= 400, (
        f"expected BYOM prefix to be rejected, got HTTP {err.status_code}: {body_text[:400]}"
    )
