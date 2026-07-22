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


_MODELS_CACHE: dict[str, list[str]] = {}


def available_models(project, cfg: Optional[Config] = None, kind: GatewayKind = "static") -> list[str]:
    """Return the list of model deployment names advertised by the gateway
    connection's `metadata.models` array. Empty list means dynamic discovery
    (metadata absent) — in which case we can't statically know what's
    available and the test should try and let the API 404 speak.
    """
    cfg = cfg or load_config()
    conn_name = cfg.resolve_gateway(kind)
    if conn_name in _MODELS_CACHE:
        return _MODELS_CACHE[conn_name]
    try:
        conn = project.connections.get(name=conn_name, include_credentials=False)
        # SDK exposes metadata as a nested dict or object.
        meta = getattr(conn, "metadata", None) or {}
        if hasattr(meta, "get"):
            models_raw = meta.get("models") or []
        else:
            models_raw = []
        if isinstance(models_raw, str):
            import json as _json
            models_raw = _json.loads(models_raw)
        names = []
        for m in models_raw:
            if isinstance(m, dict):
                n = m.get("name") or (m.get("properties") or {}).get("model", {}).get("name")
                if n:
                    names.append(n)
        _MODELS_CACHE[conn_name] = names
        return names
    except Exception as e:  # pragma: no cover
        print(f"::warning::available_models({conn_name}) failed: {e}", file=sys.stderr)
        _MODELS_CACHE[conn_name] = []
        return []


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
    project = AIProjectClient(endpoint=cfg.project_endpoint, credential=cred, allow_preview=True)
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
    BYOM API which sits at the account level rather than the project.

    Derived from PROJECT_ENDPOINT when FOUNDRY_ACCOUNT_ENDPOINT isn't set:
    ``https://{account}.services.ai.azure.com/api/projects/{proj}`` ->
    ``https://{account}.services.ai.azure.com``.
    """
    explicit = os.environ.get("FOUNDRY_ACCOUNT_ENDPOINT")
    if explicit:
        return explicit
    proj = os.environ.get("PROJECT_ENDPOINT")
    if not proj:
        return None
    # Strip trailing "/api/projects/<name>" if present.
    marker = "/api/projects/"
    idx = proj.find(marker)
    return proj[:idx] if idx > 0 else proj


def aad_token(scope: str = "https://cognitiveservices.azure.com/.default") -> str:
    """Get a bearer token for direct-HTTP tests that bypass the SDK."""
    return DefaultAzureCredential().get_token(scope).token


def attach_agent_card(cfg: "Config", agent_name: str, description: str = "BYOM A2A test agent", enable_protocols: Optional[list[str]] = None) -> str:
    """PATCH `/agents/{name}` to attach a minimal AgentCard, which is
    prerequisite for the A2A protocol endpoint at
    `/agents/{name}/endpoint/protocols/a2a`.

    If `enable_protocols` is provided (e.g. `['a2a', 'responses']`) it is
    also PATCHed onto `agent_endpoint.protocols`. Foundry requires BOTH
    'a2a' and 'responses' on the endpoint to answer A2A JSON-RPC calls;
    an A2A-only endpoint responds with `EndpointProtocolNotEnabled`.

    There is no SDK method for either PATCH (AgentsOperations only exposes
    GET/DELETE on `/agents/{name}`), even though AgentDetails.agent_card
    and AgentDetails.agent_endpoint are read/create/update fields. Returns
    the a2a base URL.
    """
    import requests

    token = aad_token("https://ai.azure.com/.default")
    base = cfg.project_endpoint.rstrip("/")
    url = f"{base}/agents/{agent_name}?api-version=v1"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/merge-patch+json",
    }
    body: dict = {
        "agent_card": {
            "version": "1.0.0",
            "description": description,
            "skills": [
                {
                    "id": "summarize",
                    "name": "summarize",
                    "description": "Produce a one-sentence summary.",
                    "tags": ["text", "summary"],
                    "examples": ["Summarize this paragraph in one sentence."],
                }
            ],
        }
    }
    if enable_protocols:
        body["agent_endpoint"] = {"protocols": list(enable_protocols)}
    r = requests.patch(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return f"{base}/agents/{agent_name}/endpoint/protocols/a2a"


def a2a_send_and_wait(a2a_url: str, text: str, timeout_s: int = 60) -> str:
    """Send an A2A JSON-RPC `message/send` to `a2a_url` and poll `tasks/get`
    until the task completes. Returns the concatenated text of the response
    artifacts. Uses DefaultAzureCredential for the `ai.azure.com` scope,
    which is the only scope the A2A endpoint accepts.
    """
    import time
    import uuid

    import requests

    token = aad_token("https://ai.azure.com/.default")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    send = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
            }
        },
    }
    resp = requests.post(a2a_url, headers=headers, json=send, timeout=30).json()
    if "error" in resp:
        raise RuntimeError(f"A2A message/send error: {resp['error']}")
    task_id = resp["result"]["id"]

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        poll = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": "tasks/get", "params": {"id": task_id}}
        pr = requests.post(a2a_url, headers=headers, json=poll, timeout=30).json()
        state = pr["result"]["status"]["state"]
        if state == "completed":
            parts = []
            for art in pr["result"].get("artifacts", []) or []:
                for p in art.get("parts", []) or []:
                    if p.get("kind") == "text":
                        parts.append(p.get("text", ""))
            return "".join(parts)
        if state in ("failed", "canceled", "rejected"):
            raise RuntimeError(f"A2A task ended in state={state}: {pr['result']}")
        time.sleep(2)
    raise TimeoutError(f"A2A task {task_id} did not complete within {timeout_s}s")


def make_mcp_tool(
    server_url: str,
    server_label: str,
    auth: str = "AgenticIdentity",
    headers: Optional[dict] = None,
):
    """Build an MCPTool for a 1P MCP server (Foundry IQ / Work IQ / Web IQ /
    Fabric IQ) or any third-party MCP endpoint.

    auth is the MCPTool authType: 'AgenticIdentity' (project or agent identity),
    'UserEntraToken' (OAuth on-behalf-of passthrough), or 'None'.

    headers is an optional dict of custom HTTP headers to forward on every
    MCP call (e.g. {'x-apikey': '...'} for WebIQ).
    """
    from azure.ai.projects.models import MCPTool

    kwargs = {"server_url": server_url, "server_label": server_label}
    if headers:
        kwargs["headers"] = headers
    try:
        return MCPTool(**kwargs, auth_type=auth)
    except TypeError:
        # azure-ai-projects >= 2.2.0 dropped the `auth_type` kwarg. Auth is now
        # driven by `authorization` (OAuth bearer) or `project_connection_id`.
        # For MCP servers that don't need auth (auth="None") we can just omit;
        # for AgenticIdentity/UserEntraToken the test will fail at invocation
        # time with a clear server-side error, which is what we want.
        return MCPTool(**kwargs)


# ---------------------------------------------------------------------------
# Hosted-agent packaging (used by features/hosted-agents-*)
# ---------------------------------------------------------------------------


_HOSTED_AGENT_MAIN = '''\
"""Tiny BYOM smoke agent (Invocations protocol).

Reads the AI Gateway connection + model from custom env vars, calls the
Foundry Responses API from inside the hosted container, and returns the
answer as JSON. Used by the byom-feature-support matrix to prove that
BYOM routing works when the caller is a hosted agent (not a script).
"""
import json
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agentserver.invocations import InvocationAgentServerHost
from starlette.requests import Request
from starlette.responses import JSONResponse

_PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]  # platform-injected
_GATEWAY = os.environ["AI_GATEWAY_CONNECTION"]              # custom env var
_MODEL   = os.environ["CHAT_MODEL"]                         # custom env var

_project = AIProjectClient(endpoint=_PROJECT_ENDPOINT, credential=DefaultAzureCredential())
_aoai = _project.get_openai_client()

app = InvocationAgentServerHost()


@app.invoke_handler
async def handle(request: Request) -> JSONResponse:
    body = await request.body()
    payload = json.loads(body) if body else {}
    prompt = payload.get("prompt", "Say hello.")
    resp = _aoai.responses.create(model=f"{_GATEWAY}/{_MODEL}", input=prompt)
    return JSONResponse({"output_text": resp.output_text, "model": f"{_GATEWAY}/{_MODEL}"})


if __name__ == "__main__":
    app.run()
'''

_HOSTED_AGENT_REQUIREMENTS = """\
azure-ai-agentserver-invocations>=1.0.0b6
azure-ai-projects>=2.2.0
azure-identity>=1.19.0
openai>=2.0.0
"""


def _build_hosted_agent_zip() -> bytes:
    """Return a zip containing `main.py` + `requirements.txt` for remote_build."""
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("main.py", _HOSTED_AGENT_MAIN)
        zf.writestr("requirements.txt", _HOSTED_AGENT_REQUIREMENTS)
    return buf.getvalue()


def deploy_hosted_byom_probe(project, agent_name: str, gateway_conn: str, model: str, timeout_s: int = 600):
    """Deploy the tiny BYOM smoke agent as a Foundry hosted agent version.

    Uses `remote_build` \u2192 Foundry builds the container; no ACR/Dockerfile needed.
    Polls until the version is `active` (or `failed`). Returns the version id.
    Raises RuntimeError on failure/timeout.
    """
    import hashlib
    import time

    from azure.ai.projects.models import (
        CodeConfiguration,
        CreateAgentVersionFromCodeContent,
        CreateAgentVersionFromCodeMetadata,
        HostedAgentDefinition,
        ProtocolVersionRecord,
    )

    zip_bytes = _build_hosted_agent_zip()
    zip_sha = hashlib.sha256(zip_bytes).hexdigest()

    content = CreateAgentVersionFromCodeContent(
        metadata=CreateAgentVersionFromCodeMetadata(
            description="BYOM smoke probe (hosted agent, Invocations protocol)",
            definition=HostedAgentDefinition(
                cpu="0.5",
                memory="1Gi",
                code_configuration=CodeConfiguration(
                    runtime="python_3_13",
                    entry_point=["python", "main.py"],
                    dependency_resolution="remote_build",
                ),
                protocol_versions=[
                    ProtocolVersionRecord(protocol="invocations", version="1.0.0"),
                ],
                environment_variables={
                    "AI_GATEWAY_CONNECTION": gateway_conn,
                    "CHAT_MODEL": model,
                },
            ),
        ),
        code=("agent.zip", zip_bytes, "application/zip"),
    )

    created = project.beta.agents.create_version_from_code(
        agent_name=agent_name,
        content=content,
        code_zip_sha256=zip_sha,
    )

    deadline = time.monotonic() + timeout_s
    while True:
        version = project.agents.get_version(agent_name=agent_name, agent_version=created.version)
        status = version.get("status") if isinstance(version, dict) else getattr(version, "status", None)
        if status == "active":
            return created.version
        if status == "failed":
            err = version.get("error") if isinstance(version, dict) else getattr(version, "error", None)
            raise RuntimeError(f"Hosted-agent provisioning failed: {err}")
        if time.monotonic() > deadline:
            raise TimeoutError(f"Hosted-agent {agent_name}/{created.version} did not reach active in {timeout_s}s (last status={status!r})")
        time.sleep(10)


def invoke_hosted_agent(cfg, agent_name: str, prompt: str = "Say hello."):
    """POST to the hosted agent's Invocations endpoint with a bearer token."""
    import requests

    token = aad_token("https://ai.azure.com/.default")
    url = f"{cfg.project_endpoint}/agents/{agent_name}/endpoint/protocols/invocations?api-version=v1"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"message": prompt, "prompt": prompt},
        timeout=120,
    )
    if not r.ok:
        raise AssertionError(f"invoke_hosted_agent {agent_name} -> {r.status_code}: {r.text}")
    return r.json()
