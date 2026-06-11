"""Shared helpers used by every feature test.

Reads configuration from environment variables (.env locally, GitHub
environment variables in CI) and exposes a configured AIProjectClient +
OpenAI client routed through the AI Gateway connection.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Literal, Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

GatewayKind = Literal["static", "dynamic"]


@dataclass
class Config:
    project_endpoint: str
    gateway_static: Optional[str]
    gateway_dynamic: Optional[str]

    def resolve_gateway(self, kind: Optional[GatewayKind] = None) -> str:
        if kind == "static":
            if not self.gateway_static:
                raise RuntimeError("AI_GATEWAY_CONNECTION_STATIC is not set")
            return self.gateway_static
        if kind == "dynamic":
            if not self.gateway_dynamic:
                raise RuntimeError("AI_GATEWAY_CONNECTION_DYNAMIC is not set")
            return self.gateway_dynamic
        gw = self.gateway_static or self.gateway_dynamic
        if not gw:
            raise RuntimeError("No AI_GATEWAY_CONNECTION_* env var set")
        return gw


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        print(f"::error::Missing required env var {name}", file=sys.stderr)
        sys.exit(2)
    return val


def load_config() -> Config:
    return Config(
        project_endpoint=_require("PROJECT_ENDPOINT"),
        gateway_static=os.environ.get("AI_GATEWAY_CONNECTION_STATIC"),
        gateway_dynamic=os.environ.get("AI_GATEWAY_CONNECTION_DYNAMIC"),
    )


def build_clients(cfg: Optional[Config] = None):
    """Returns (cfg, AIProjectClient, OpenAI client routed at the project)."""
    cfg = cfg or load_config()
    cred = DefaultAzureCredential()
    project = AIProjectClient(endpoint=cfg.project_endpoint, credential=cred)
    aoai = project.get_openai_client()
    return cfg, project, aoai


def gateway_model(model_name: str, cfg: Optional[Config] = None, kind: Optional[GatewayKind] = None) -> str:
    """Return ``{gateway-connection-name}/{model_name}`` so Foundry routes
    the request through the AI Gateway (APIM) connection rather than looking
    for a local deployment on the Foundry account."""
    cfg = cfg or load_config()
    return f"{cfg.resolve_gateway(kind)}/{model_name}"


def make_prompt_agent_with_tools(
    project,
    name: str,
    tools: list,
    instructions: str = "You are a helpful assistant.",
    model: Optional[str] = None,
    cfg: Optional[Config] = None,
    kind: GatewayKind = "static",
):
    """Convenience wrapper used by tool tests: create/update a Foundry Prompt
    Agent whose orchestrator model is BYOM-routed through the requested gateway.

    Used so each tool test reduces to: build the tool, call this helper, invoke
    the agent through the Responses API.
    """
    from azure.ai.projects.models import PromptAgentDefinition

    chat_model = model or os.environ.get("CHAT_MODEL", "gpt-5-mini")
    gw_model = gateway_model(chat_model, cfg, kind=kind)
    return project.agents.create_version(
        agent_name=name,
        definition=PromptAgentDefinition(model=gw_model, instructions=instructions, tools=tools),
    )


def invoke_agent(aoai, agent, user_message: str):
    """Open a conversation and call the Responses API targeting the given agent."""
    conv = aoai.conversations.create(
        items=[{"type": "message", "role": "user", "content": user_message}],
    )
    return aoai.responses.create(
        conversation=conv.id,
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        input="",
    )


def require_env(name: str, feature: str) -> Optional[str]:
    """Return env var value, or print a skip warning and return None.

    Tool tests use this so missing optional connection IDs (e.g. SharePoint,
    Fabric) cause the test to exit 0 with a ``::warning::`` rather than fail.
    """
    val = os.environ.get(name)
    if not val:
        print(f"::warning::{name} not set; skipping {feature}")
    return val


def account_endpoint() -> Optional[str]:
    """Foundry/Cognitive Services account endpoint, e.g. for the Translator
    BYOM API which sits at the account level rather than the project."""
    return os.environ.get("FOUNDRY_ACCOUNT_ENDPOINT")


def aad_token(scope: str = "https://cognitiveservices.azure.com/.default") -> str:
    """Get a bearer token for direct-HTTP tests that bypass the SDK."""
    return DefaultAzureCredential().get_token(scope).token


def make_mcp_tool(server_url: str, server_label: str, auth: str = "AgenticIdentity"):
    """Build an MCPTool for a 1P MCP server (Foundry IQ / Work IQ / Web IQ /
    Fabric IQ) or any third-party MCP endpoint.

    auth is the MCPTool authType: 'AgenticIdentity' (project or agent identity),
    'UserEntraToken' (OAuth on-behalf-of passthrough), or 'None'.
    """
    from azure.ai.projects.models import MCPTool

    return MCPTool(server_url=server_url, server_label=server_label, auth_type=auth)

