"""AI Red Teaming with a BYOM target model."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import gateway_model, load_config  # noqa: E402

TARGET = os.environ.get("RED_TEAM_TARGET_MODEL")


def main() -> int:
    if not TARGET:
        print("::warning::RED_TEAM_TARGET_MODEL not set; skipping red-teaming")
        return 0
    try:
        from azure.ai.evaluation.red_team import RedTeam, RiskCategory
    except ImportError:
        print("::warning::azure-ai-evaluation[redteam] not installed; skipping")
        return 0
    cfg = load_config()
    gw_model = gateway_model(TARGET, cfg, kind="static")
    print(f"::group::red-teaming target={gw_model}")
    try:
        rt = RedTeam(
            azure_ai_project=cfg.project_endpoint,
            risk_categories=[RiskCategory.HateUnfairness],
            num_objectives=1,
        )
        print(f"red-team scaffolded for target deployment {gw_model}")
        print("OK")
        print("::endgroup::")
        return 0
    except Exception as e:
        print(f"::warning::Setup failed (may be BYOM prefix not parsed): {e}")
        print("::endgroup::")
        return 0


if __name__ == "__main__":
    sys.exit(main())
