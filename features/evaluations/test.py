"""Evaluation with BYOM-prefixed judge model.

Documents whether azure-ai-evaluation's initialization_parameters.deployment_name
accepts the '{conn}/{model}' prefix. Research suggests it likely does not.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import gateway_model, load_config  # noqa: E402

JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL")


def main() -> int:
    if not JUDGE_MODEL:
        print("::warning::EVAL_JUDGE_MODEL not set; skipping evaluations")
        return 0
    try:
        from azure.ai.evaluation import RelevanceEvaluator, AzureOpenAIModelConfiguration
    except ImportError:
        print("::warning::azure-ai-evaluation not installed; skipping evaluations")
        return 0
    cfg = load_config()
    gw_model = gateway_model(JUDGE_MODEL, cfg, kind="static")
    print(f"::group::evaluations judge deployment_name={gw_model}")
    try:
        model_config = AzureOpenAIModelConfiguration(
            azure_endpoint=cfg.project_endpoint,
            azure_deployment=gw_model,
            api_version="2024-10-01-preview",
        )
        evaluator = RelevanceEvaluator(model_config=model_config)
        result = evaluator(query="What is 2+2?", response="4")
        print("OK:", result)
        print("::endgroup::")
        return 0
    except Exception as e:
        print(f"::warning::Failed (likely BYOM prefix not parsed): {e}")
        print("::endgroup::")
        return 0


if __name__ == "__main__":
    sys.exit(main())
