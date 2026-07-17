"""Chat Completions on the project-scoped OpenAI client, stream + non-stream.

Positive-assertion probes for a `not_supported` endpoint: these tests PASS
when Foundry treats the BYOM-prefixed model as a local deployment name and
rejects it with DeploymentNotFound. If Chat Completions starts honoring the
BYOM prefix, the tests fail RED and the card must be promoted.
"""
import openai
import pytest


@pytest.mark.not_supported
def test_chat_completions_nonstream(aoai, static_model):
    with pytest.raises(openai.NotFoundError) as exc_info:
        aoai.chat.completions.create(
            model=static_model(),
            messages=[{"role": "user", "content": "Say hi in three words."}],
        )

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code == 404, f"expected HTTP 404, got {err.status_code}: {body_text[:400]}"
    assert "DeploymentNotFound" in body_text


@pytest.mark.not_supported
def test_chat_completions_stream(aoai, static_model):
    with pytest.raises(openai.NotFoundError) as exc_info:
        stream = aoai.chat.completions.create(
            model=static_model(),
            messages=[{"role": "user", "content": "Count 1 to 3."}],
            stream=True,
        )
        list(stream)

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code == 404, f"expected HTTP 404, got {err.status_code}: {body_text[:400]}"
    assert "DeploymentNotFound" in body_text
