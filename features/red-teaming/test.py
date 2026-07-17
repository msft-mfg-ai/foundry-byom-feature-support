"""AI Red Teaming with a BYOM target model.

The stock `azure-ai-evaluation.red_team` path fails against BYOM in two
stacked ways: (1) the SDK asks Entra for `https://cognitiveservices.azure.com/.default`
but the Foundry BYOM endpoint requires `https://ai.azure.com/.default`,
and (2) PyRit's `OpenAIChatTarget` calls `chat/completions` but BYOM
routing is only exposed on `/openai/v1/responses`. Passing a plain
callable target lets us bypass both.
"""

import json
import os
import pathlib
import pytest


@pytest.mark.supported
@pytest.mark.needs_env
@pytest.mark.slow
def test_red_teaming(cfg, static_model, require_env, tmp_path):
    require_env("RED_TEAM_TARGET_MODEL")
    try:
        from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    endpoint = cfg.project_endpoint.rstrip("/") + "/openai/v1"
    wire_model = static_model("RED_TEAM_TARGET_MODEL", "gpt-5-mini")

    async def target_callback(messages, **_):
        import openai
        client = openai.AsyncOpenAI(
            base_url=endpoint,
            api_key=credential.get_token("https://ai.azure.com/.default").token,
        )
        r = await client.responses.create(model=wire_model, input=messages[-1]["content"])
        text = r.output[0].content[0].text if getattr(r, "output", None) else str(r)
        return {"role": "assistant", "content": text}

    rt = RedTeam(
        azure_ai_project=cfg.project_endpoint,
        credential=credential,
        risk_categories=[RiskCategory.HateUnfairness],
        num_objectives=1,
        output_dir=str(tmp_path),
    )

    import asyncio
    asyncio.run(
        rt.scan(
            target=target_callback,
            attack_strategies=[AttackStrategy.Base64],
            skip_upload=True,
            skip_evals=True,
            timeout=180,
            parallel_execution=False,
            max_parallel_tasks=1,
        )
    )

    results = list(tmp_path.rglob("final_results.json"))
    assert results, "scan did not produce final_results.json"
    payload = json.loads(results[0].read_text())
    total = 0
    if isinstance(payload, dict):
        card = payload.get("scorecard", {}) or {}
        summary = (card.get("risk_category_summary") or [{}])[0]
        total = summary.get("overall_total", 0)
    assert total > 0, f"scan completed but no attacks reached the target: {str(payload)[:400]}"
