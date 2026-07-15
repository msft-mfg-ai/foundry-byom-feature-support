"""Skills: BYOM rejects the toolbox delivery path used to attach skills."""
import time

import openai
import pytest
from azure.ai.projects.models import (
    MCPTool,
    PromptAgentDefinition,
    SkillInlineContent,
    ToolboxSearchPreviewTool,
    ToolboxSkillReference,
)
from azure.core.exceptions import ResourceExistsError


@pytest.mark.not_supported
@pytest.mark.needs_env
@pytest.mark.xfail(
    reason="SDK/service bug: skill create() succeeds but the returned version id is "
    "not addressable via `version='1'` on toolbox create_version (returns 'not found'). "
    "Even if that were fixed, the toolbox delivery is blocked by BYOM.",
    strict=False,
)
def test_skill_via_toolbox_rejected_by_byom(project, aoai, static_model, unique_agent_name, require_env):
    """Create an inline skill, attach it to a toolbox, then confirm BYOM rejects the delivery.

    The skill+toolbox provisioning itself works; the block is on the agent side,
    identical to the plain toolboxes card — the `toolbox_search_preview` tool is
    the only way to hand a skill to an agent, and it is not accepted with BYOM.
    """
    mcp_url = require_env("MCP_SERVER_URL")
    skill_name = unique_agent_name("byomskill").replace("-", "").lower()[:24]
    toolbox_name = unique_agent_name("byomtb").replace("-", "").lower()[:24]

    try:
        sv = project.beta.skills.create(
            name=skill_name,
            inline_content=SkillInlineContent(
                description="Reply with exactly one short sentence.",
                instructions="You MUST reply with exactly one short sentence.\n",
            ),
        )
    except ResourceExistsError:
        # SDK's LRO polling races with the async create; the resource actually exists.
        time.sleep(2)
        sv = project.beta.skills.get(name=skill_name)

    version = getattr(sv, "version", None) or getattr(sv, "default_version", "1")

    try:
        project.beta.toolboxes.create_version(
            name=toolbox_name,
            tools=[MCPTool(server_label="probe", server_url=mcp_url, require_approval="never")],
            skills=[ToolboxSkillReference(name=skill_name, version=version)],
        )
        agent = project.agents.create_version(
            agent_name=unique_agent_name("byom-skill"),
            definition=PromptAgentDefinition(
                model=static_model(),
                instructions="Follow the skill's instructions.",
                tools=[ToolboxSearchPreviewTool(name=toolbox_name)],
            ),
        )
        conv = aoai.conversations.create(
            items=[{"type": "message", "role": "user", "content": "Say hi."}]
        )
        with pytest.raises(openai.BadRequestError, match="toolbox_search_preview"):
            aoai.responses.create(
                conversation=conv.id,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
                input="",
            )
    finally:
        try:
            project.beta.toolboxes.delete(name=toolbox_name)
        except Exception:
            pass
        try:
            project.beta.skills.delete(name=skill_name)
        except Exception:
            pass
