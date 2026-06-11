# BYOM Feature Support

Live support matrix for **bring-your-own-model** features when calling Azure AI Foundry projects backed by an **APIM AI Gateway** connection.

The matrix lives at: `https://<org>.github.io/byom-feature-support/` (publish via GitHub Pages).

## How it works

```
site/                     Astro + Tailwind static site (GitHub Pages)
features/<slug>/          One folder per feature
  feature.json            Metadata: name, description, PM, support status, impl status
  test.py                 Self-contained, runnable test script
features/_shared.py       Shared client builder + `gateway_model()` helper
.github/workflows/
  feature-<slug>.yml      One workflow per feature, runs test.py against a real env
  _feature-test.yml       Reusable workflow (auth + uv setup)
  deploy-site.yml         Builds the Astro site and deploys to GitHub Pages
```

The site is generated from `features/*/feature.json` + `features/*/test.py` at build time, so the code samples are always in sync with what the workflows actually run.

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

**Variables**:
- `PROJECT_ENDPOINT` — e.g. `https://my-foundry.services.ai.azure.com/api/projects/my-project`
- `AI_GATEWAY_CONNECTION_STATIC` — name of the static ApiManagement connection on the project
- `AI_GATEWAY_CONNECTION_DYNAMIC` — name of the dynamic ApiManagement connection on the project
- Per-feature model overrides (`CHAT_MODEL`, `RESPONSES_MODEL`, `EMBEDDINGS_MODEL`, `IMAGE_MODEL`, `SPEECH_MODEL`, `TRANSCRIPTION_MODEL`)

The OIDC service principal must have the `Azure AI User` role on the Foundry project.

## Running locally

```bash
uv sync
cp .env.example .env   # then fill in your values
az login
uv run python features/responses/test.py
```

## Building the site locally

```bash
cd site
npm install
npm run dev
```

## Adding a new feature

1. `mkdir features/<slug>`
2. Add `features/<slug>/feature.json` and `features/<slug>/test.py`
3. Copy `.github/workflows/feature-responses.yml` to `feature-<slug>.yml` and update the `paths:` filter and the `with.feature:` input
4. Push — the site rebuilds automatically and the new card appears

## Known gaps

See the **Image Generation** card on the published site — as of 2026-06-10 Azure AI Foundry's `/openai/v1/images/generations` route does not parse the `{connection}/{model}` prefix used to route through ApiManagement connections, so calls never reach APIM.
