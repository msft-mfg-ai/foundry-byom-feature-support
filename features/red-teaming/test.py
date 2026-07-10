"""AI Red Teaming with a BYOM target model."""

import pytest


@pytest.mark.supported
@pytest.mark.needs_env
def test_red_teaming(cfg, static_model, require_env):
    require_env("RED_TEAM_TARGET_MODEL")
    try:
        from azure.ai.evaluation.red_team import RedTeam, RiskCategory
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    from azure.identity import DefaultAzureCredential
    target_model = static_model("RED_TEAM_TARGET_MODEL", "gpt-5-mini")
    rt = RedTeam(
        azure_ai_project=cfg.project_endpoint,
        credential=DefaultAzureCredential(),
        risk_categories=[RiskCategory.HateUnfairness],
        num_objectives=1,
    )
    assert target_model.startswith(f"{cfg.resolve_gateway('static')}/")
    assert rt
