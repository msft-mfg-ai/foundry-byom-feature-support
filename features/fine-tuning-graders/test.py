"""Fine-tuning score_model grader with BYOM-prefixed judge model."""

import pytest


@pytest.mark.not_supported
@pytest.mark.xfail(
    strict=True,
    reason="Fine-tuning grader.model is expected NOT to route through the {conn}/{model} BYOM prefix.",
)
def test_fine_tuning_graders(aoai, static_model):
    raw = aoai.post(
        "/fine_tuning/alpha/graders/validate",
        body={
            "grader": {
                "type": "score_model",
                "name": "byom-probe",
                "model": static_model("EVAL_JUDGE_MODEL", "gpt-5-mini"),
                "input": [{"role": "user", "content": "Rate 0-1: {{sample.output_text}}"}],
            }
        },
        cast_to=object,
    )
    assert raw is not None
