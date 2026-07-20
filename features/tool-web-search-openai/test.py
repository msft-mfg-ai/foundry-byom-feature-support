"""OpenAI built-in web_search tool through a BYOM-prefixed model.

No Bing connection required. Uses the Responses API's native tool. Foundry
accepts the GA `web_search` tool but rejects the older `web_search_preview`
variants — see feature.json for the exact error and covered variants.
"""
import os
import openai
import pytest


@pytest.mark.supported
def test_tool_web_search_openai_single(aoai, static_model):
    """GA `web_search` tool succeeds end-to-end with a BYOM-prefixed model."""
    resp = aoai.responses.create(
        model=static_model(),
        tools=[{"type": "web_search"}],
        input="Search the web for one current headline about AI. Reply in one sentence.",
    )
    assert (resp.output_text or "").strip()
    types = [it.type for it in resp.output]
    assert "web_search_call" in types, f"expected a web_search_call in output, got {types}"


@pytest.mark.supported
def test_tool_web_search_openai_two_in_one_turn(aoai, static_model):
    """Historical regression: two searches in a single turn used to fail. Now works."""
    resp = aoai.responses.create(
        model=static_model(),
        tools=[{"type": "web_search"}],
        input=(
            "Do two separate web searches — one for a current AI headline and one for a "
            "current cloud-computing headline — then combine in one reply."
        ),
    )
    text = (resp.output_text or "").strip().lower()
    assert text
    assert ("ai" in text or "artificial" in text) and "cloud" in text


@pytest.mark.supported
def test_tool_web_search_openai_two_turns_same_conversation(aoai, static_model):
    """Historical regression: 2 requests with web_search into the same conversation."""
    model = static_model()
    tool = {"type": "web_search"}
    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": "Let's do some web searches."}]
    )
    r1 = aoai.responses.create(
        model=model, tools=[tool], conversation=conv.id,
        input="Search the web for one current headline about AI. Reply in one sentence.",
    )
    assert (r1.output_text or "").strip()
    assert any(it.type == "web_search_call" for it in r1.output)

    r2 = aoai.responses.create(
        model=model, tools=[tool], conversation=conv.id,
        input="Now search for one current headline about cloud computing. One sentence.",
    )
    assert (r2.output_text or "").strip()
    assert any(it.type == "web_search_call" for it in r2.output), (
        "second request to same conversation should still trigger web_search"
    )


@pytest.mark.not_supported
@pytest.mark.parametrize("tool_type", [
    "web_search_preview",
    "web_search_preview_2025_03_11",
    "web_search_2025_08_26",
])
def test_tool_web_search_preview_variants_rejected(aoai, static_model, tool_type):
    """Older/newer versioned tool names are still rejected by BYOM.

    Verbatim: 'The following tools are not supported with BYO model: <tool_type>.'
    """
    with pytest.raises(openai.BadRequestError, match=tool_type):
        aoai.responses.create(
            model=static_model(),
            tools=[{"type": tool_type}],
            input="one AI headline.",
        )
