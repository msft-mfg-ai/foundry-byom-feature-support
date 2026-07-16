#!/usr/bin/env python3
"""Resolve everything needed to run the BYOM suite from just a Foundry
project resource ID.

Given:  /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account>/projects/<project>

Emits (as GITHUB_OUTPUT lines) the values the caller workflow needs:
  account_resource_id  -- strip /projects/<name>
  account_name         -- last segment before /projects/
  project_name
  project_endpoint     -- https://<account>.services.ai.azure.com/api/projects/<project>
  ai_gateway_connection_static   -- first APIM connection with metadata.models set
  ai_gateway_connection_dynamic  -- first APIM connection WITHOUT metadata.models
  ai_gateway_connection_anthropic -- first APIM connection whose name contains 'anthropic'
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys


PROJECT_ID_RE = re.compile(
    r"^/subscriptions/(?P<sub>[^/]+)"
    r"/resourceGroups/(?P<rg>[^/]+)"
    r"/providers/Microsoft\.CognitiveServices"
    r"/accounts/(?P<account>[^/]+)"
    r"/projects/(?P<project>[^/]+)/?$",
    re.IGNORECASE,
)


def az(*args: str) -> str:
    return subprocess.check_output(["az", *args], text=True).strip()


def emit(key: str, value: str) -> None:
    line = f"{key}={value}"
    print(line, file=sys.stderr)
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(line + "\n")


def main() -> int:
    project_id = os.environ.get("PROJECT_RESOURCE_ID", "").strip()
    if not project_id:
        print("::error::PROJECT_RESOURCE_ID env var is required", file=sys.stderr)
        return 2

    m = PROJECT_ID_RE.match(project_id)
    if not m:
        print(f"::error::Not a Foundry project resource ID: {project_id}", file=sys.stderr)
        return 2

    account_name = m.group("account")
    project_name = m.group("project")
    account_id = project_id[: project_id.lower().index("/projects/")]
    project_endpoint = f"https://{account_name}.services.ai.azure.com/api/projects/{project_name}"

    emit("account_resource_id", account_id)
    emit("account_name", account_name)
    emit("project_name", project_name)
    emit("project_endpoint", project_endpoint)

    api_version = "2025-04-01-preview"
    url = f"https://management.azure.com{project_id}/connections?api-version={api_version}"
    conns = json.loads(az("rest", "--method", "get", "--url", url)).get("value", [])
    apim = [c for c in conns if (c.get("properties") or {}).get("category") == "ApiManagement"]

    static, dynamic, anthropic = None, None, None
    for c in apim:
        name = c["name"]
        meta = (c.get("properties") or {}).get("metadata") or {}
        lname = name.lower()
        if "anthropic" in lname:
            anthropic = anthropic or name
            continue
        has_models = bool(meta.get("models"))
        if has_models and static is None:
            static = name
        elif not has_models and dynamic is None:
            dynamic = name

    # Fallbacks based on the -s- / -d- naming convention.
    for c in apim:
        n = c["name"]
        ln = n.lower()
        if "anthropic" in ln:
            continue
        if static is None and "-s-" in ln:
            static = n
        if dynamic is None and "-d-" in ln:
            dynamic = n

    if not static:
        print("::error::No static ApiManagement connection discovered", file=sys.stderr)
        return 3

    emit("ai_gateway_connection_static", static)
    emit("ai_gateway_connection_dynamic", dynamic or "")
    emit("ai_gateway_connection_anthropic", anthropic or "")

    print(
        f"::notice::project={project_name} account={account_name} "
        f"static={static} dynamic={dynamic} anthropic={anthropic}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
