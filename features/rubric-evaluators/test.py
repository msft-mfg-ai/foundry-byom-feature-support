"""Rubric evaluator BYOM probe.

The rubric-evaluator preview surface has no SDK yet and its REST endpoints
are not exposed on the Foundry project endpoint. This probe walks a
plausible set of paths + api-versions so the failure mode is captured
verbatim on the card, and future SDK/preview releases can flip the status
by removing the xfail once the endpoint responds with anything other than
`400 API version not supported`.
"""

import json
import os
import urllib.request
import urllib.error
import pytest


CANDIDATE_PATHS = [
    "evaluations/rubrics",
    "evaluations/rubric-evaluators",
    "evaluators/rubric",
    "rubrics",
    "rubric-evaluators",
]
CANDIDATE_API_VERSIONS = [
    "v1",
    "2025-04-01-preview",
    "2025-05-01",
    "2025-05-01-preview",
    "2025-10-01-preview",
    "2025-11-15-preview",
    "2026-04-01-preview",
]


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(
    strict=True,
    reason="Rubric-evaluator REST is not exposed on the Foundry project endpoint yet; every path/api-version combo returns 400 or 404.",
)
def test_rubric_evaluators(cfg, static_model, require_env):
    require_env("EVAL_JUDGE_MODEL")
    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token
    endpoint = cfg.project_endpoint.rstrip("/")

    body = json.dumps(
        {
            "name": "byom-rubric-probe",
            "judge": {"model": static_model("EVAL_JUDGE_MODEL", "gpt-5-mini")},
            "criteria": [
                {"id": "helpfulness", "description": "Is the response useful?", "weight": 5}
            ],
        }
    ).encode("utf-8")

    responses = []
    for api in CANDIDATE_API_VERSIONS:
        for path in CANDIDATE_PATHS:
            url = f"{endpoint}/{path}?api-version={api}"
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    txt = resp.read().decode("utf-8", errors="replace")
                    responses.append((resp.status, path, api, txt[:200]))
            except urllib.error.HTTPError as e:
                responses.append((e.code, path, api, e.read().decode("utf-8", errors="replace")[:200]))
            except Exception as e:
                responses.append((-1, path, api, str(e)[:200]))

    reachable = [r for r in responses if r[0] not in (400, 404, -1)]
    assert reachable, (
        "No rubric-evaluator endpoint responded with anything other than 400/404. "
        f"First few: {responses[:3]}"
    )
