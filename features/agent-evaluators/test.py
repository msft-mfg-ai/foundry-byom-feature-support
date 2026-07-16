"""Agent-quality evaluator with a BYOM-prefixed judge model.

Probes whether azure-ai-evaluation's agent-scoped evaluators
(IntentResolutionEvaluator etc.) accept a `{conn}/{model}` prefix on
model_config.azure_deployment. Expected to fail with the same URL-shape
regression that breaks the batch `evaluations` card.
"""

import pytest


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=True,
    reason="Agent evaluators use the same azure-ai-evaluation URL shape as batch evaluators, which Foundry doesn't route.",
)
def test_agent_evaluators(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation import AzureOpenAIModelConfiguration, IntentResolutionEvaluator
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=cfg.project_endpoint,
        azure_deployment=static_model("EVAL_JUDGE_MODEL", "gpt-4o-mini"),
        api_version="2025-04-01-preview",
    )
    evaluator = IntentResolutionEvaluator(model_config=model_config)
    result = evaluator(
        query="Book me a flight to Seattle next Tuesday.",
        response="I've searched flights to Seattle for next Tuesday. The best option is United 1234 departing at 8:15am.",
    )
    assert result
