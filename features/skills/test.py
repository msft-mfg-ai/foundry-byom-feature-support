"""Foundry Skills — probe both the service-side create bug and the BYOM delivery path.

Follows the official sample: sample_agent_toolbox_skill.py in azure-sdk-for-python.
"""
import time
import uuid

import pytest
from azure.ai.projects.models import (
    MCPTool,
    PromptAgentDefinition,
    SkillInlineContent,
    ToolboxSearchPreviewToolboxTool,
    ToolboxSkillReference,
)
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.identity import DefaultAzureCredential


@pytest.mark.not_confirmed
@pytest.mark.needs_env
@pytest.mark.xfail(
    reason="Service-side bug: beta.skills.create leaves the skill in state='Creating' "
    "indefinitely; default_version='1' is claimed but list_versions() is empty and "
    "get_version(name, '1') returns 404. Repro'd in the Foundry portal too. Once the "
    "service is fixed, the toolbox+MCP delivery path is BYOM-supported so this should pass.",
    strict=False,
)
def test_skill_via_toolbox_with_byom(project, aoai, static_model, unique_agent_name, require_env):
    endpoint = require_env("PROJECT_ENDPOINT")
    skill_name = f"byomskill{uuid.uuid4().hex[:8]}"
    tb_name = f"byomtb{uuid.uuid4().hex[:8]}"

    try:
        try:
            sv = project.beta.skills.create(
                name=skill_name,
                inline_content=SkillInlineContent(
                    description="Reply with CANARY-42.",
                    instructions="When asked anything, reply with exactly: CANARY-42",
                ),
            )
        except ResourceExistsError:
            # SDK LRO polling races with the service's async create. Wait briefly
            # then read the skill; if the version never materializes this test xfails.
            for _ in range(20):
                time.sleep(3)
                versions = list(project.beta.skills.list_versions(name=skill_name))
                if versions:
                    sv = versions[0]
                    break
            else:
                pytest.xfail("Skill stuck in state='Creating', no version materialized")

        tbv = project.toolboxes.create_version(
            name=tb_name,
            description="skill delivery",
            tools=[ToolboxSearchPreviewToolboxTool()],
            skills=[ToolboxSkillReference(name=sv.name, version=sv.version)],
        )

        mcp_url = f"{endpoint}/toolboxes/{tb_name}/versions/{tbv.version}/mcp?api-version=v1"
        token = DefaultAzureCredential().get_token("https://ai.azure.com/.default").token

        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-skill"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Follow the skill instructions in your context. Do not call any tool.",
                tools=[
                    MCPTool(
                        server_label="skill-tb",
                        server_url=mcp_url,
                        authorization=token,
                        require_approval="never",
                    )
                ],
            ),
        )
        conv = aoai.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Say the magic word."}]
        )
        resp = aoai.responses.create(
            conversation=conv.id,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            input="",
        )
        assert "CANARY-42" in (resp.output_text or "")
    finally:
        for op in (
            lambda: project.toolboxes.delete(tb_name),
            lambda: project.beta.skills.delete(skill_name),
        ):
            try:
                op()
            except (ResourceNotFoundError, Exception):
                pass
