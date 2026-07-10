"""Shared pytest fixtures for every features/<slug>/test.py.

Design:
* Session-scoped Azure clients — one Foundry project + OpenAI client is enough
  for the whole suite because each test uses distinct agent/conversation names.
* Skip helpers (`require_env`, `require_gateway`) so tests self-skip when their
  optional env vars aren't provided; hard-required env (PROJECT_ENDPOINT,
  AI_GATEWAY_CONNECTION_STATIC) fails fast via `_shared.load_config()`.
* xfail conventions are implemented in each test file with pytest.mark.xfail;
  the shape is documented in the README.
"""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from typing import Optional

import pytest

# Make the sibling helper module importable without a sys.path shim in every test.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared import (  # noqa: E402
    Config,
    available_models,
    build_clients,
    gateway_model,
    load_config,
)


# ---------- session-scoped Azure clients ----------

@pytest.fixture(scope="session")
def cfg() -> Config:
    return load_config()


@pytest.fixture(scope="session")
def clients(cfg: Config):
    _, project, aoai = build_clients(cfg)
    return project, aoai


@pytest.fixture(scope="session")
def project(clients):
    return clients[0]


@pytest.fixture(scope="session")
def aoai(clients):
    return clients[1]


# ---------- model resolvers ----------

@pytest.fixture
def static_model(cfg: Config):
    """Return a factory: static_model(env_key='CHAT_MODEL', default='gpt-5-mini')."""

    def _resolve(env_key: str = "CHAT_MODEL", default: str = "gpt-5-mini") -> str:
        return gateway_model(os.environ.get(env_key, default), cfg, kind="static")

    return _resolve


@pytest.fixture
def dynamic_model(cfg: Config):
    def _resolve(env_key: str = "CHAT_MODEL", default: str = "gpt-5-mini") -> str:
        return gateway_model(os.environ.get(env_key, default), cfg, kind="dynamic")

    return _resolve


# ---------- env-driven skip helpers ----------

@pytest.fixture
def require_env():
    """Usage:  server = require_env('MCP_SERVER_URL')  -> value or pytest.skip."""

    def _require(name: str) -> str:
        val = os.environ.get(name)
        if not val:
            pytest.skip(f"{name} not set; skipping")
        return val

    return _require


@pytest.fixture
def require_gateway(cfg: Config):
    """Skip a test if the requested AI_GATEWAY_CONNECTION_* env var isn't set."""

    def _require(kind: str) -> str:
        try:
            return cfg.resolve_gateway(kind)
        except RuntimeError as e:
            pytest.skip(str(e))

    return _require


# ---------- naming ----------

@pytest.fixture
def unique_agent_name():
    """Return a per-test agent name to avoid collisions between concurrent runs."""

    def _name(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:8]}"

    return _name


# ---------- model availability ----------

@pytest.fixture
def require_model(project, cfg):
    """Skip the test when a required model is not deployed on the target gateway.

    Usage:  require_model('o3-mini', kind='static')
    """
    def _require(model_name: str, kind: str = "static") -> str:
        if not model_name:
            pytest.skip("no model specified")
        models = available_models(project, cfg, kind=kind)  # type: ignore[arg-type]
        if models and model_name not in models:
            pytest.skip(f"model {model_name!r} not deployed on {kind} gateway; available: {sorted(models)[:5]}...")
        return model_name

    return _require


@pytest.fixture
def skip_on_missing_model():
    """Context-manager fixture that converts 'model/deployment not found' 404s
    from the OpenAI client into pytest.skip so we only xfail real BYOM
    regressions (not misconfigured deployments).

    Usage:
        with skip_on_missing_model():
            resp = aoai.responses.create(model=..., input=...)
    """
    import contextlib

    from openai import NotFoundError

    @contextlib.contextmanager
    def _cm():
        try:
            yield
        except NotFoundError as e:
            msg = str(e).lower()
            if "deployment" in msg or "model" in msg or "not found" in msg:
                pytest.skip(f"model not deployed on gateway: {e}")
            raise

    return _cm
