"""Evaluation with a BYOM-prefixed judge model.

`azure-ai-evaluation` 1.18.2 added an admin-connected (BYO) judge model path:
prompty-based evaluators (Relevance, Coherence, Fluency, ...) accept a
``model_config`` shaped as ``{"byo_model": "{connection}/{deployment}",
"project_endpoint": "..."}``. When both keys are present the evaluator routes
`chat.completions.create(...)` through the Foundry project **Responses API**
instead of building a native `/openai/deployments/{deployment}/...` URL, so
the AI Gateway connection is resolved server-side (see
``azure/ai/evaluation/_byo_judge.py`` -> ``is_byo_model_config`` /
``AsyncByoProjectResponsesClient``). ``_BYOModelConfiguration`` isn't
exported as a public type yet (docstring: "not caller-facing... until the
feature reaches GA"), but a plain dict with those two keys works at runtime.

The *old* shape (``AzureOpenAIModelConfiguration(azure_deployment=...)``)
still fails: it builds `/openai/deployments/{conn}/{model}/chat/completions`,
which Foundry rejects with `400 'API version not supported'`. That's a
separate, still-broken path -- this test only asserts the new one.
"""

import pytest


@pytest.mark.supported
@pytest.mark.needs_env
def test_evaluations(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation import RelevanceEvaluator
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    judge_model = static_model("EVAL_JUDGE_MODEL", "gpt-5-mini")
    model_config = {"byo_model": judge_model, "project_endpoint": cfg.project_endpoint}

    evaluator = RelevanceEvaluator(model_config=model_config)
    result = evaluator(query="What is 2+2?", response="4")

    assert result.get("relevance_result") == "pass", f"unexpected relevance result: {result}"
    routed_model = result.get("relevance_properties", {}).get("model")
    assert routed_model == judge_model, f"expected judge call routed as {judge_model!r}, got {routed_model!r}"
