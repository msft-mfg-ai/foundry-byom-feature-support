"""Evaluation with BYOM-prefixed judge model.

Documents whether azure-ai-evaluation's initialization_parameters.deployment_name
accepts the '{conn}/{model}' prefix. Research suggests it likely does not.
"""

import pytest


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=True,
    reason="azure-ai-evaluation builds `/openai/deployments/{apim-conn}/{model}/chat/completions` and Foundry does not route BYOM-prefixed judge deployment_name (400 'API version not supported').",
)
def test_evaluations(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation import AzureOpenAIModelConfiguration, RelevanceEvaluator
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=cfg.project_endpoint,
        azure_deployment=static_model("EVAL_JUDGE_MODEL", "gpt-5-mini"),
        api_version="2025-04-01-preview",
    )
    evaluator = RelevanceEvaluator(model_config=model_config)
    result = evaluator(query="What is 2+2?", response="4")
    assert result
