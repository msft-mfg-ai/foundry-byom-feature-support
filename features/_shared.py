"""Shared helpers used by every feature test.

Reads configuration from environment variables (.env locally, GitHub
environment variables in CI) and exposes a configured AIProjectClient +
OpenAI client routed through the AI Gateway connection.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    project_endpoint: str
    gateway_static: Optional[str]
    gateway_dynamic: Optional[str]

    @property
    def gateway(self) -> str:
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
    cfg = cfg or load_config()
    cred = DefaultAzureCredential()
    project = AIProjectClient(endpoint=cfg.project_endpoint, credential=cred)
    aoai = project.get_openai_client()
    return cfg, project, aoai


def gateway_model(model_name: str, cfg: Optional[Config] = None) -> str:
    """Return ``{gateway-connection-name}/{model_name}`` so Foundry routes
    the request through the AI Gateway (APIM) connection rather than looking
    for a local deployment on the Foundry account."""
    cfg = cfg or load_config()
    return f"{cfg.gateway}/{model_name}"
