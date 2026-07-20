"""Fine-tuning score_model grader with BYOM-prefixed judge model.

Positive-assertion probe for a `not_supported` nested judge slot: the test
PASSES when the fine-tuning grader validation endpoint rejects the BYOM-prefixed
`grader.model`. If the grader starts honoring the prefix, or the error shape
changes, this test fails RED and the card must be promoted or updated.
"""

import openai
import pytest


@pytest.mark.not_supported
def test_fine_tuning_graders(aoai, static_model):
    with pytest.raises(openai.APIStatusError) as exc_info:
        aoai.post(
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

    err = exc_info.value
    body = getattr(err, "response", None)
    body_text = body.text if body is not None else str(err)
    assert err.status_code >= 400, (
        f"expected BYOM prefix to be rejected, got HTTP {err.status_code}: {body_text[:400]}"
    )
