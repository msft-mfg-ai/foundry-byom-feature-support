"""Assistants v2 (beta): create assistant + run with BYOM-prefixed model."""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Assistants v2 is expected not to parse the {conn}/{model} BYOM prefix.",
)
def test_assistants_v2(aoai, static_model):
    model = static_model()
    assistant = aoai.beta.assistants.create(
        name="byom-probe",
        model=model,
        instructions="Be terse.",
    )
    assert assistant.id
    try:
        thread = aoai.beta.threads.create(messages=[{"role": "user", "content": "Say hi."}])
        run = aoai.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant.id,
        )
        assert run.status == "completed"
    finally:
        aoai.beta.assistants.delete(assistant.id)
