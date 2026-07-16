"""OpenAI built-in web_search_preview tool through a BYOM-prefixed model.

No Bing connection required. Uses the Responses API's native tool.
"""
import pytest


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="APIM/Foundry routing of the OpenAI built-in web_search tool is not confirmed.",
)
def test_tool_web_search_openai_single(aoai, static_model):
    resp = aoai.responses.create(
        model=static_model(),
        tools=[{"type": "web_search_preview"}],
        input="Search the web for one current headline about AI. Reply in one sentence.",
    )
    assert (resp.output_text or "").strip()


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Same intra-turn multi-search regression suspected for the built-in tool.",
)
def test_tool_web_search_openai_two_in_one_turn(aoai, static_model):
    resp = aoai.responses.create(
        model=static_model(),
        tools=[{"type": "web_search_preview"}],
        input=(
            "Perform two separate web searches — one for a current AI headline "
            "and one for a current cloud-computing headline — then combine the "
            "findings in a single reply."
        ),
    )
    text = (resp.output_text or "").strip().lower()
    assert text
    assert ("ai" in text or "artificial" in text) and "cloud" in text
