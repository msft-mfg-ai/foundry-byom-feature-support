"""AI Red Teaming with a BYOM target model.

Runs a real single-attack, single-objective scan against a BYOM-prefixed
target so we can see whether adversarial probes actually reach the gateway
model, or whether they fail auth/URL-construction the way the other
azure-ai-evaluation cards do.
"""

import json
import os
import pytest


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    reason="PyRit OpenAIChatTarget calls the BYOM target with the wrong audience and gets 401 for every prompt.",
)
def test_red_teaming(cfg, static_model, require_env, tmp_path):
    require_env("RED_TEAM_TARGET_MODEL")
    try:
        from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
        from azure.ai.evaluation import AzureOpenAIModelConfiguration
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    from azure.identity import DefaultAzureCredential

    target_config = AzureOpenAIModelConfiguration(
        azure_endpoint=cfg.project_endpoint,
        azure_deployment=static_model("RED_TEAM_TARGET_MODEL", "gpt-5-mini"),
        api_version="2025-04-01-preview",
    )

    output_dir = str(tmp_path)
    rt = RedTeam(
        azure_ai_project=cfg.project_endpoint,
        credential=DefaultAzureCredential(),
        risk_categories=[RiskCategory.HateUnfairness],
        num_objectives=1,
        output_dir=output_dir,
    )

    import asyncio
    asyncio.run(
        rt.scan(
            target=target_config,
            attack_strategies=[AttackStrategy.Base64],
            skip_upload=True,
            skip_evals=True,
            timeout=180,
            parallel_execution=False,
            max_parallel_tasks=1,
        )
    )

    results_files = list(tmp_path.rglob("final_results.json"))
    assert results_files, "scan did not produce final_results.json"
    payload = json.loads(results_files[0].read_text())
    total_attacks = payload.get("attack_details", {}).get("total_attacks", 0)
    assert total_attacks > 0, (
        f"scan completed but no attacks reached the target — likely 401 audience "
        f"mismatch (see stdout). final_results.json: {json.dumps(payload)[:500]}"
    )
