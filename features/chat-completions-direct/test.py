"""Chat Completions on the project-scoped OpenAI client, stream + non-stream.

The project's OpenAI client (from `project.get_openai_client()`) is pointed
at `{PROJECT_ENDPOINT}/openai/v1/`. The Responses API on that client honours
BYOM prefixes; Chat Completions currently does not — the proxy resolves
the model locally on the Foundry account and 404s before ever routing to
the APIM gateway.
"""
import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(strict=True, reason="chat.completions on project OpenAI client returns 404 DeploymentNotFound for BYOM-prefixed models.")
def test_chat_completions_nonstream(aoai, static_model):
    r = aoai.chat.completions.create(
        model=static_model(),
        messages=[{"role": "user", "content": "Say hi in three words."}],
    )
    assert r.choices and (r.choices[0].message.content or "").strip()


@pytest.mark.not_supported
@pytest.mark.xfail(strict=True, reason="chat.completions on project OpenAI client returns 404 DeploymentNotFound for BYOM-prefixed models (stream mode).")
def test_chat_completions_stream(aoai, static_model):
    stream = aoai.chat.completions.create(
        model=static_model(),
        messages=[{"role": "user", "content": "Count 1 to 3."}],
        stream=True,
    )
    parts = [c.choices[0].delta.content or "" for c in stream if c.choices]
    assert "".join(parts).strip()
