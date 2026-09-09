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

import json
import tempfile
import time
from pathlib import Path

import pytest
from azure.identity import DefaultAzureCredential


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


@pytest.mark.supported
@pytest.mark.needs_env
def test_evaluations_cloud_job(cfg, project, static_model, require_env, unique_agent_name):
    """Cloud-submitted evaluation job (`project.evaluations.create`) with a
    BYOM-prefixed `initialization_parameters.deployment_name` -- the mechanism
    the original card described, distinct from the local synchronous
    evaluator covered by `test_evaluations` above. Both use the same admin-
    connected judge-model routing under the hood, but this exercises the
    server-side evaluation service (dataset upload -> job submission ->
    poll -> metrics), not the local prompty client.
    """
    require_env("EVAL_JUDGE_MODEL")
    try:
        from azure.ai.evaluation._common.onedp import ProjectsClient
        from azure.ai.evaluation._common.onedp.models import (
            Evaluation,
            EvaluatorConfiguration,
            InputDataset,
        )
    except ImportError:
        pytest.skip("azure-ai-evaluation not installed")

    judge_model = static_model("EVAL_JUDGE_MODEL", "gpt-5-mini")
    name = unique_agent_name("byom-eval-cloud")

    with tempfile.TemporaryDirectory() as tmp:
        data_path = Path(tmp) / "data.jsonl"
        data_path.write_text(json.dumps({"query": "What is 2+2?", "response": "4"}) + "\n")
        dataset = project.datasets.upload_file(name=name, version="1", file_path=str(data_path))

    onedp_client = ProjectsClient(endpoint=cfg.project_endpoint, credential=DefaultAzureCredential())
    evaluation = Evaluation(
        display_name=name,
        data=InputDataset(id=dataset.id),
        evaluators={
            "relevance": EvaluatorConfiguration(
                id="azureml://registries/azureml/evaluators/builtin.relevance/versions/12",
                init_params={"deployment_name": judge_model},
                data_mapping={"query": "${data.query}", "response": "${data.response}"},
            )
        },
    )
    submitted = onedp_client.evaluations.create(evaluation)

    terminal_states = {"Completed", "Failed", "Canceled"}
    eval_id = submitted.name
    result = submitted
    for _ in range(18):  # ~3 minutes
        if result.status in terminal_states:
            break
        time.sleep(10)
        result = onedp_client.evaluations.get(eval_id)
    else:
        pytest.fail(f"evaluation job {eval_id} did not reach a terminal state: {result.status}")

    metrics = json.loads(result["outputs"].get("evaluationMetrics") or "{}")
    assert result.status == "Completed", (
        f"cloud evaluation job failed with status {result.status!r} using "
        f"deployment_name={judge_model!r}: {metrics}"
    )
    assert "relevance.relevance_score" in metrics, f"expected relevance metrics, got: {metrics}"
