"""Evals with BYOM-prefixed generative model (data_source.model), not the judge."""

import pytest


@pytest.mark.not_confirmed
@pytest.mark.xfail(
    strict=False,
    reason="Eval run data_source.model BYOM routing is not yet confirmed.",
)
def test_evals_generative_model(aoai, static_model):
    eval_obj = aoai.evals.create(
        name="byom-generative-probe",
        data_source_config={
            "type": "custom",
            "item_schema": {"type": "object", "properties": {"q": {"type": "string"}}},
        },
        testing_criteria=[
            {
                "type": "string_check",
                "name": "nonempty",
                "input": "{{sample.output_text}}",
                "operation": "like",
                "reference": "%",
            }
        ],
    )
    assert eval_obj.id

    run = aoai.evals.runs.create(
        eval_id=eval_obj.id,
        data_source={
            "type": "responses",
            "model": static_model(),
            "input_messages": {"type": "template", "template": [{"role": "user", "content": "{{item.q}}"}]},
            "source": {"type": "file_content", "content": [{"item": {"q": "Say hi."}}]},
        },
    )
    assert run.id
