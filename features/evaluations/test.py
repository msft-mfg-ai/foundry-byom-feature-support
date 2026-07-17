"""Evaluation with BYOM-prefixed judge model.

Positive-assertion probe for a `not_supported` evaluator path: the test
PASSES when azure-ai-evaluation keeps building a URL shape that Foundry
cannot route. If Foundry starts accepting the BYOM-prefixed judge deployment,
or the error shape changes, this test fails RED and the card must be promoted
or updated.
"""

import openai
import pytest


@pytest.mark.not_supported
@pytest.mark.needs_env
def test_evaluations(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation import AzureOpenAIModelConfiguration, RelevanceEvaluator
        from azure.ai.evaluation._legacy.prompty._exceptions import WrappedOpenAIError
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    model_config = AzureOpenAIModelConfiguration(
        azure_endpoint=cfg.project_endpoint,
        azure_deployment=static_model("EVAL_JUDGE_MODEL", "gpt-5-mini"),
        api_version="2025-04-01-preview",
    )
    evaluator = RelevanceEvaluator(model_config=model_config)

    with pytest.raises(WrappedOpenAIError) as exc_info:
        evaluator(query="What is 2+2?", response="4")

    err = exc_info.value.__cause__
    assert isinstance(err, openai.APIStatusError)
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code == 400, f"expected HTTP 400, got {err.status_code}: {body_text[:400]}"
    assert "API version not supported" in body_text
