"""Agent-quality evaluator with a BYOM-prefixed judge model.

Same fix as `features/evaluations`: `azure-ai-evaluation` 1.18.2 added an
admin-connected (BYO) judge model path for prompty-based evaluators --
`model_config={"byo_model": "{connection}/{deployment}", "project_endpoint":
"..."}` routes the judge call through the Foundry project Responses API.
`IntentResolutionEvaluator` (like `RelevanceEvaluator`) is prompty-based, so
it picks up the same fix. The old `AzureOpenAIModelConfiguration(azure_deployment=...)`
shape is still broken (`400 'API version not supported'`) -- see
`features/evaluations/feature.json` notes for the side-by-side evidence.
"""

import pytest


@pytest.mark.supported
@pytest.mark.needs_env
def test_agent_evaluators(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation import IntentResolutionEvaluator
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    judge_model = static_model("EVAL_JUDGE_MODEL", "gpt-5-mini")
    model_config = {"byo_model": judge_model, "project_endpoint": cfg.project_endpoint}

    evaluator = IntentResolutionEvaluator(model_config=model_config)
    result = evaluator(
        query="Book me a flight to Seattle next Tuesday.",
        response="I've searched flights to Seattle for next Tuesday. The best option is United 1234 departing at 8:15am.",
    )

    assert result.get("intent_resolution_result") in ("pass", "fail"), f"unexpected result: {result}"
    routed_model = result.get("intent_resolution_properties", {}).get("model")
    assert routed_model == judge_model, f"expected judge call routed as {judge_model!r}, got {routed_model!r}"
