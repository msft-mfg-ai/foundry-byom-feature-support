# BYOM Feature Support

Live support matrix for **bring-your-own-model** features when calling Azure AI Foundry projects backed by an **APIM AI Gateway** connection, run against a **private-networked** Foundry + APIM environment.

The matrix lives at: `https://<org>.github.io/byom-feature-support/` (publish via GitHub Pages).

## What the matrix covers

The matrix is grouped into 6 categories on the site:

| Category | Cards | Highlights |
| --- | --- | --- |
| **Agents** (5) | `prompt-agents-static`, `prompt-agents-dynamic`, `hosted-agents-static`, `hosted-agents-dynamic`, `agent-a2a-connected` | `PromptAgentDefinition(model="{conn}/{deployment}")` invoked through the Responses API with `extra_body.agent_reference`. |
| **Direct API endpoints** (5) | `image-generation-direct`, `image-generation-tool`, `llm-translation`, `reasoning-models-byom`, `responses-direct` | Probes whether non-agent endpoints (image gen, translator with `deploymentName`, reasoning param forwarding, raw Responses) parse the BYOM prefix. |
| **Routing & providers** (5) | `routing-apim-openai`, `routing-apim-anthropic`, `routing-modelgateway-non-openai`, `routing-serverless-catalog`, `routing-static-vs-dynamic-discovery` | The different connection categories: `ApiManagement` vs `ModelGateway` vs `Serverless`, and providers fronted by each (AOAI, Anthropic, OpenRouter/LiteLLM/DeepSeek, Foundry catalog). |
| **Agent tools** (17) | web search, code interpreter, file search, Azure AI Search, SharePoint OBO, Fabric, A2A, MCP (Entra project / Entra agent / OAuth passthrough), 1P MCP (Foundry IQ / Work IQ / Web IQ / Fabric IQ), Logic Apps, computer use, memory | Each tool is attached to a Prompt Agent whose orchestrator model is BYOM-routed. The tool itself has no model param. |
| **Quality & safety** (2) | `evaluations`, `red-teaming` | Tests whether judge / target models accept the BYOM prefix. |
| **Infrastructure & publishing** (6) | `private-foundry`, `private-apim`, `publish-to-teams`, `portal-ui-parity-providers`, `sdk-enum-coverage`, `byom-incompatible-endpoints` | Mostly status-only cards documenting infra prerequisites and known gaps. |

Total: 40 cards (31 with an automated test, 9 status-only).

## How it works

```
site/                     Astro + Tailwind static site (GitHub Pages)
features/<slug>/          One folder per feature
  feature.json            Metadata: name, description, PM, support status, impl status
  test.py                 (Optional) self-contained, runnable test script
features/_shared.py       Shared client builder + `gateway_model(model, kind=...)` helper
.github/workflows/
  feature-<slug>.yml      One workflow per feature with a test.py
  _feature-test.yml       Reusable workflow (auth + uv setup)
  deploy-site.yml         Builds the Astro site and deploys to GitHub Pages
```

Status-only features (no `test_file` in `feature.json`) render as cards on the site but have no workflow. The site reads `features/*/feature.json` + `features/*/test.py` at build time, so the code samples are always in sync with what the workflows actually run.

## Status taxonomy

| Field | Values |
| --- | --- |
| `support_status` | `supported`, `partial`, `not_supported`, `not_confirmed` |
| `implementation_status` | `ga`, `preview`, `in_progress`, `not_confirmed` |

## GitHub environment

Each feature workflow consumes a GitHub Environment (`byom` by default) containing:

**Secrets** (used by `azure/login@v2` OIDC):
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

**Variables** (each test skips cleanly with `::warning::` if its specific vars are unset):

- **Always needed:** `PROJECT_ENDPOINT`, `CHAT_MODEL`
- **Gateway connections:** `AI_GATEWAY_CONNECTION_{STATIC,DYNAMIC,ANTHROPIC,MODELGATEWAY,SERVERLESS}`
- **Provider models:** `ANTHROPIC_MODEL`, `MODELGATEWAY_MODEL`, `SERVERLESS_MODEL`, `REASONING_MODEL`, `IMAGE_MODEL`
- **Pre-deployed agents:** `PROMPT_AGENT_NAME_{STATIC,DYNAMIC}`, `HOSTED_AGENT_NAME_{STATIC,DYNAMIC}`
- **Tool connections:** `BING_CONNECTION_ID`, `FILE_SEARCH_VECTOR_STORE_ID`, `AZURE_AI_SEARCH_{CONNECTION_ID,INDEX_NAME}`, `SHAREPOINT_CONNECTION_ID`, `FABRIC_CONNECTION_ID`, `A2A_REMOTE_AGENT_ENDPOINT`, `LOGIC_APP_{RESOURCE_ID,WORKFLOW_NAME}`, `COMPUTER_USE_ENVIRONMENT`, `IMAGE_DEPLOYMENT_NAME`
- **MCP servers:** `MCP_SERVER_URL`, `MCP_SERVER_URL_AGENT_IDENTITY`, `MCP_SERVER_URL_OAUTH`, `FOUNDRY_IQ_MCP_URL`, `WORK_IQ_MCP_URL`, `WEB_IQ_MCP_URL`, `FABRIC_IQ_MCP_URL`
- **Quality / safety:** `EVAL_JUDGE_MODEL`, `RED_TEAM_TARGET_MODEL`
- **Translator (account-level):** `FOUNDRY_ACCOUNT_ENDPOINT`, `FOUNDRY_REGION`

See `.env.example` for the full list with example values.

The OIDC service principal must have the `Azure AI User` role on the Foundry project.

### Private-networked runners

Because the matrix runs against private endpoints, the GitHub-hosted `ubuntu-latest` runner cannot reach them. Call each feature workflow with a self-hosted runner label that has line-of-sight to the private VNet by overriding the reusable workflow input, for example:

```yaml
jobs:
  run:
    uses: ./.github/workflows/_feature-test.yml
    with:
      feature: prompt-agents-static
      runner: self-hosted   # or your own label
    secrets: inherit
```

## Running locally

```bash
uv sync
cp .env.example .env   # then fill in your values
az login
uv run python features/prompt-agents-static/test.py
```

You need to be on a network that can resolve the private Foundry + APIM endpoints (VPN, jump host, etc.).

## Building the site locally

```bash
cd site
npm install
npm run dev
```

## Adding a new feature

1. `mkdir features/<slug>`
2. Add `features/<slug>/feature.json`. Add `test.py` if the feature has an automated test; omit `test_file` from the JSON for a status-only card.
3. If you added a `test.py`, copy `.github/workflows/feature-prompt-agents-static.yml` to `feature-<slug>.yml` and update the `paths:` filter and the `with.feature:` input.
4. Push — the site rebuilds automatically and the new card appears.
