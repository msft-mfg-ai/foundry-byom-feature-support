"""Chat Completions with the web-search model variant (gpt-5-search-api)."""
import pytest


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Search chat model may not be routable via the BYOM prefix.",
)
def test_chat_completions_web_search(aoai, static_model, require_model):
    import os
    require_model(os.environ.get("WEB_SEARCH_MODEL", "gpt-5-search-api"), kind="static")
    model = static_model("WEB_SEARCH_MODEL", "gpt-5-search-api")
    resp = aoai.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "What day is it today? One short sentence."}],
    )
    content = resp.choices[0].message.content
    assert content and content.strip()
