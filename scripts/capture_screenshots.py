"""Interactive Playwright screenshot capture using your real managed Edge profile.

Run this from **Windows PowerShell** (not WSL) so the script can open the
managed Edge profile and satisfy any conditional-access / device-compliance
checks. Screenshots are saved directly into the correct
``features/<slug>/screenshots/`` folders described in each ``screenshots/README.md``.

Prereqs (Windows PowerShell)::

    py -3.12 -m pip install --user playwright
    # Playwright ships its own Chromium; we tell it to use MS Edge instead:
    py -3.12 -m playwright install msedge
    # Close every Edge window first — Chromium locks user-data-dir.

Then::

    cd C:\\path\\to\\byom-feature-support
    py -3.12 scripts\\capture_screenshots.py

Flow:
* For each planned screenshot, the browser navigates to the target URL.
* You interact with the page (open the dropdown, click "Edit", whatever the
  README asks). When the frame looks right, press ENTER in the terminal.
* The script saves a PNG at the exact target path, then moves to the next.
* Press ``s`` + ENTER to skip a shot; ``q`` + ENTER to quit early.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


REPO_ROOT = Path(__file__).resolve().parent.parent
FEATURES = REPO_ROOT / "features"


# Windows Edge profile lives at:
#   C:\Users\<you>\AppData\Local\Microsoft\Edge\User Data
# Override with EDGE_USER_DATA_DIR env var if yours differs.
DEFAULT_USER_DATA_DIR = str(
    Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Piotr Karpala\AppData\Local"))
    / "Microsoft"
    / "Edge"
    / "User Data"
)

USER_DATA_DIR = os.environ.get("EDGE_USER_DATA_DIR", DEFAULT_USER_DATA_DIR)
PROFILE_DIR = os.environ.get("EDGE_PROFILE_DIR", "Default")


# Planned captures. Path is relative to the repo root and MUST match the target
# in the corresponding features/<slug>/screenshots/README.md.
Shot = tuple[str, str, str]  # (target_path, landing_url, human_prompt)

PLAN: list[Shot] = [
    (
        "features/rubric-evaluators/screenshots/01-model-dropdown-native-only.png",
        "https://ai.azure.com/",
        "Go to Evaluate -> Evaluators -> New rubric evaluator. Open the Model dropdown so it lists gpt-5.5 etc.",
    ),
    (
        "features/rubric-evaluators/screenshots/02-authorization-failed-deployments-write.png",
        "https://ai.azure.com/",
        "Same dialog: pick a model that triggers the AuthorizationFailed deployments/write banner.",
    ),
    (
        "features/synthetic-data-generation/screenshots/01-generator-model-dropdown.png",
        "https://ai.azure.com/",
        "Go to Data -> Generate synthetic data. Open the generator-model dropdown.",
    ),
    (
        "features/portal-playground-models/screenshots/01-models-endpoints-list.png",
        "https://ai.azure.com/",
        "Management center -> Models + endpoints. Show the full list.",
    ),
    (
        "features/portal-playground-models/screenshots/02-playground-model-picker.png",
        "https://ai.azure.com/",
        "Playground (Chat or Agents) -> open the model picker dropdown.",
    ),
    (
        "features/portal-ui-parity-providers/screenshots/01-add-connection-provider-list.png",
        "https://ai.azure.com/",
        "Management center -> Connections -> New connection. Show the provider tile grid.",
    ),
    (
        "features/portal-ui-parity-providers/screenshots/02-apim-v2-only-endpoint-shape.png",
        "https://ai.azure.com/",
        "Open an existing APIM connection (edit view). Show endpoint field + model list.",
    ),
    (
        "features/continuous-agent-evaluation/screenshots/01-judge-model-picker.png",
        "https://ai.azure.com/",
        "Observability -> Continuous evaluation -> new rule. Open judge-model dropdown.",
    ),
    (
        "features/agent-evaluators/screenshots/01-portal-evaluation-model-config.png",
        "https://ai.azure.com/",
        "Cloud-evaluation wizard, model_config step. Open the deployment dropdown.",
    ),
    (
        "features/knowledge-bases/screenshots/01-foundry-iq-kb-model-config.png",
        "https://ai.azure.com/",
        "Knowledge -> Foundry IQ knowledge base. Open the model / azureOpenAIParameters section.",
    ),
    (
        "features/tool-memory/screenshots/01-memory-store-chat-model.png",
        "https://ai.azure.com/",
        "Memory stores -> create/edit dialog. Show the chat_model field (skip if UI missing).",
    ),
    (
        "features/publish-to-teams/screenshots/01-publish-to-teams-flow.png",
        "https://ai.azure.com/",
        "Open a BYOM Prompt Agent -> Publish -> Microsoft Teams. Capture the publish dialog.",
    ),
    (
        "features/content-understanding/screenshots/01-defaults-model-picker.png",
        "https://contentunderstanding.ai.azure.com/settings",
        "Content Understanding settings -> default model deployments picker.",
    ),
    (
        "features/routing-static-vs-dynamic-discovery/screenshots/01-connection-metadata-models.png",
        "https://ai.azure.com/",
        "Management center -> Connections -> open the STATIC APIM connection. Show the models[] metadata.",
    ),
    (
        "features/tools-supported-with-byom/screenshots/01-agent-tools-picker.png",
        "https://ai.azure.com/",
        "Open a Prompt Agent -> Tools panel -> Add tool. Expand the list.",
    ),
    (
        "features/hosted-agents-canary/screenshots/01-hosted-agent-versions.png",
        "https://ai.azure.com/",
        "Agents -> canary hosted agent -> Versions tab. Show at least one active version.",
    ),
    (
        "features/private-foundry/screenshots/01-networking-blade.png",
        "https://portal.azure.com/",
        "Azure portal -> Foundry account -> Networking blade. publicNetworkAccess=Disabled + PE list.",
    ),
    (
        "features/private-apim/screenshots/01-apim-vnet-integration.png",
        "https://portal.azure.com/",
        "Azure portal -> APIM service -> Virtual network blade. Show VNet mode + PE list.",
    ),
]


def main() -> int:
    profile_path = Path(USER_DATA_DIR)
    if not profile_path.exists():
        print(f"ERROR: Edge user-data-dir not found: {profile_path}", file=sys.stderr)
        print("Set EDGE_USER_DATA_DIR env var to the correct path.", file=sys.stderr)
        return 2

    print(f"Using Edge profile: {profile_path} (profile={PROFILE_DIR!r})")
    print("Make sure ALL Edge windows are closed before continuing.")
    input("Press ENTER when ready...")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_path),
            channel="msedge",
            headless=False,
            viewport={"width": 1920, "height": 1080},
            args=[f"--profile-directory={PROFILE_DIR}"],
        )
        page = context.pages[0] if context.pages else context.new_page()

        try:
            for idx, (target_rel, url, prompt) in enumerate(PLAN, 1):
                target = REPO_ROOT / target_rel
                if target.exists():
                    print(f"[{idx}/{len(PLAN)}] SKIP (exists): {target_rel}")
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                print(f"\n[{idx}/{len(PLAN)}] {target_rel}")
                print(f"  -> {prompt}")
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                except Exception as e:
                    print(f"  ! navigate failed: {e}")
                choice = input("  Press ENTER to capture, 's' to skip, 'q' to quit: ").strip().lower()
                if choice == "q":
                    break
                if choice == "s":
                    continue
                page.screenshot(path=str(target), full_page=False)
                print(f"  saved -> {target}")
        finally:
            context.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
