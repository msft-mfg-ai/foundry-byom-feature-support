# Copilot instructions — byom-feature-support

Live support matrix for **bring-your-own-model** features when invoking Azure AI Foundry projects through an **APIM AI Gateway** connection in a **private-networked** environment. Each feature is either a self-contained Python test script run by a GitHub Actions workflow, or a status-only card describing an infrastructure prerequisite. Cards are rendered on a static Astro site (GitHub Pages).

## Repo layout (the parts that matter)

```
features/<slug>/feature.json   Metadata + status fields rendered on the site
features/<slug>/test.py        (Optional) runnable, self-contained test for that feature
features/_shared.py            Client builder + gateway_model() helper
.github/workflows/
  _feature-test.yml            Reusable workflow: checkout → uv → az login (OIDC) → run test.py
  feature-<slug>.yml           Per-feature wrapper that calls _feature-test.yml (only for features with a test.py)
  deploy-site.yml              Builds the Astro site and deploys to GitHub Pages
site/                          Astro + Tailwind static site; reads features/ at build time
```

The site is generated from `features/*/feature.json` + `features/*/test.py` via `site/src/data/features.ts` (`loadFeatures()`). Code samples shown on the site are the literal `test.py` files, so the docs cannot drift from what CI runs. Features without a `test_file` in their JSON are rendered as **status-only cards** — no workflow, no code sample, no badge.

## Feature taxonomy

The matrix is **use-case-oriented**, not API-primitive-oriented. Cards are grouped into 6 categories on the site (`Category` type in `site/src/data/features.ts`):

- **agents** — Foundry v2 Prompt / Hosted / Connected agents (`PromptAgentDefinition`, `HostedAgentDefinition`, RemoteA2A) with the BYOM model passed as `model="{conn}/{deployment}"`. Static + dynamic gateway pairs for prompt and hosted.
- **endpoints** — Direct (non-agent) API surfaces probed with a BYOM-prefixed model: `image-generation-direct`, `image-generation-tool`, `llm-translation` (Translator API `targets[].deploymentName`), `reasoning-models-byom`, `responses-direct`.
- **routing** — Different connection categories and upstream providers: `ApiManagement` vs `ModelGateway` vs `Serverless` × OpenAI / Anthropic / OpenRouter-LiteLLM-DeepSeek / Foundry catalog. The `static-vs-dynamic-discovery` card documents the difference between `models[]` arrays in metadata vs `modelDiscovery` runtime calls.
- **tools** — Tools attached to a Prompt Agent whose orchestrator model is BYOM-routed. The tool itself has no model param. Covers web search, code interpreter, file search, Azure AI Search, SharePoint OBO, Fabric, A2A, three MCP variants (Entra project identity, Entra agent identity, OAuth passthrough), four 1P MCP servers (Foundry IQ, Work IQ, Web IQ, Fabric IQ), Logic Apps, computer use, memory.
- **quality** — `evaluations` (judge LLM via `initialization_parameters.deployment_name`) and `red-teaming` (target model via BYOM).
- **infrastructure** — Status-only cards: `private-foundry`, `private-apim`, `publish-to-teams`, `portal-ui-parity-providers` (UI only creates AzureOpenAI/OpenAI; APIM/ModelGateway are code-only), `sdk-enum-coverage` (`ConnectionType` enum missing ApiManagement/ModelGateway), `byom-incompatible-endpoints` (rollup for embeddings/TTS/STT/batch/fine-tuning/realtime).

When adding new use cases, follow the **static + dynamic pair** convention if the case depends on a gateway connection type. Tool tests default to `kind="static"` unless the tool is specifically about dynamic discovery.

## Build / test / run

Python tests (use `uv`, never bare `pip`):

```bash
uv sync
cp .env.example .env          # fill in real values
az login                      # DefaultAzureCredential picks this up locally
uv run python features/<slug>/test.py
```

A "single test" in this repo == one feature's `test.py`. There is no pytest layer; each script returns an exit code and is the unit of CI. Tests must **exit 0 with a `::warning::` log line** when an optional prerequisite is missing (see `hosted-agents-*/test.py` for the pattern) rather than failing the workflow.

Site:

```bash
cd site
npm install
npm run dev        # local preview
npm run build      # what CI runs before publishing to Pages
```

There is no lint or formatter configured — do not add one unless asked.

## How a feature test is wired

1. `_shared.build_clients()` returns `(cfg, AIProjectClient, OpenAI)`. The OpenAI client comes from `project.get_openai_client()` so it is already pointed at `{PROJECT_ENDPOINT}/openai/v1/`.
2. **Always** pass `gateway_model(MODEL, cfg, kind="static" | "dynamic")` (not the bare model name) when constructing a `PromptAgentDefinition.model` or when calling `aoai.responses.create(model=...)` directly. It returns `"{AI_GATEWAY_CONNECTION_*}/{model}"`, which tells Foundry to forward the call to the APIM connection instead of looking for a local deployment on the Foundry account. This prefix is the whole point of the repo.
3. The `kind=` argument is **mandatory in practice** — features come in static/dynamic pairs and must pin which gateway they exercise. `kind=None` falls back to static-then-dynamic and is only there for ad-hoc local use.
4. Prompt Agents are created with `project.agents.create_version(agent_name=..., definition=PromptAgentDefinition(model=..., instructions=..., tools=[]))` and then invoked through the Responses API with `extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}}` and `input=""`. The conversation is created separately via `aoai.conversations.create(...)`.
5. Wrap the actual call in `::group::` / `::endgroup::` log markers and exit non-zero on failure — that is how the workflow surfaces pass/fail.
6. `_shared.py` is imported via a `sys.path.insert(0, parent)` shim from inside each `test.py`; keep that shim when adding a new feature so the script stays runnable directly (`python features/<slug>/test.py`) without packaging.

## Adding a new feature (checklist)

1. `mkdir features/<slug>` with `feature.json` and (optionally) `test.py`. Copy `features/prompt-agents-static/` as the template for an automated feature, or `features/private-foundry/` for a status-only card.
2. `feature.json` fields are typed in `site/src/data/features.ts` — `support_status` ∈ `supported | partial | not_supported | not_confirmed`, `implementation_status` ∈ `ga | preview | in_progress | not_confirmed`. The site will fail to type-check if you invent new values. Omit `test_file` for a status-only card.
3. If you added a `test.py`, copy `.github/workflows/feature-prompt-agents-static.yml` → `feature-<slug>.yml`. Update **both** the `paths:` filter and the `with.feature:` input. Keep the weekly cron so the matrix stays "live".
4. If the feature needs a new env var, add it to `.env.example`, the `env:` block of `_feature-test.yml`, **and** document it in `README.md` under the GitHub environment section.
5. Folders prefixed with `_` (e.g. `_shared.py`) are skipped by `loadFeatures()` — use that prefix for any non-feature helpers.

## Auth, environment, runners

- CI auth is **OIDC only** via `azure/login@v2`; the SP needs the `Azure AI User` role on the Foundry project. Do not introduce client secrets.
- All workflow inputs come from the GitHub Environment named `byom` (default in `_feature-test.yml`). Secrets: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`. The full list of `vars.*` keys lives in the `env:` block of `_feature-test.yml` and in `.env.example`. Add new vars to **both** of those when wiring a new feature.
- Tests must **exit 0 with a `::warning::`** when an optional env var is unset (see any `tool-*/test.py` for the pattern). Hard failures (exit non-zero) are reserved for genuine BYOM regressions.
- `Config.resolve_gateway(kind)` will raise if the requested connection is unset; the older property-style `cfg.gateway` is gone, use `resolve_gateway` or `gateway_model(..., kind=...)`.
- Helpers in `_shared.py` worth knowing: `build_clients()`, `gateway_model(..., kind=)`, `make_prompt_agent_with_tools(...)`, `invoke_agent(...)`, `make_mcp_tool(url, label, auth=)`, `account_endpoint()` (account-level endpoint for the translator API), `aad_token(scope)` (raw bearer for direct-HTTP tests).
- The target environment is **privately networked**, so `ubuntu-latest` GitHub-hosted runners cannot reach the Foundry / APIM private endpoints. The reusable workflow accepts a `runner` input — set it to a self-hosted runner label with VNet line-of-sight when wiring up CI for real. (Don't rename it back to `runs-on`: expression syntax `${{ inputs.runs-on }}` parses the hyphen as subtraction and the workflow fails at startup.)

