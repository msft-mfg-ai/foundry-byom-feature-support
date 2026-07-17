<div align="center">

# 🚀 BYOM Feature Support Matrix

### Live support tracker for **Bring-Your-Own-Model** features in Azure AI Foundry behind an **APIM AI Gateway**

<br>

# 👉 [**Open the live matrix**](https://msft-mfg-ai.github.io/foundry-byom-feature-support/) 👈

### https://msft-mfg-ai.github.io/foundry-byom-feature-support/

<br>

[![Deploy site](https://github.com/msft-mfg-ai/foundry-byom-feature-support/actions/workflows/deploy-site.yml/badge.svg)](https://github.com/msft-mfg-ai/foundry-byom-feature-support/actions/workflows/deploy-site.yml)
[![BYOM AI Gateway docs](https://img.shields.io/badge/docs-AI%20Gateway-blue?logo=microsoftazure)](https://learn.microsoft.com/azure/foundry/agents/how-to/ai-gateway?tabs=api-management&pivots=foundry-portal)
[![Azure AI Foundry](https://img.shields.io/badge/Azure-AI%20Foundry-0078d4?logo=microsoft)](https://learn.microsoft.com/azure/ai-foundry/)
[![Built with Astro](https://img.shields.io/badge/Built%20with-Astro-bc52ee?logo=astro&logoColor=white)](https://astro.build)

</div>

> [!IMPORTANT]
> The live site is the source of truth. Every card has its current support status, a runnable test, a link to the Microsoft Learn doc for that exact feature, and a direct link to a Microsoft sample.

---

## 🤔 What is this repo for?

This is the **source** for the matrix site — the per-feature tests, GitHub Actions workflows, and the Astro site itself. You only need to clone it if you want to:

- 🧪 **Run a feature test locally** against your own Foundry + APIM environment
- ➕ **Add a new feature card** to the matrix
- 🐛 **Fix a bug** in a test or the site

For everything else: just [**open the live matrix**](https://msft-mfg-ai.github.io/foundry-byom-feature-support/).

## 💻 Running a feature test locally

```bash
uv sync
cp .env.example .env   # then fill in your values
az login
uv run pytest features/<feature-slug>
```

You need a network path to the private Foundry + APIM endpoints (VPN, jump host, self-hosted runner, etc.). See [`.env.example`](.env.example) for the full list of variables and the `byom` GitHub Environment for how CI consumes them via OIDC.

## 🔐 Azure OIDC setup for CI

Workflows authenticate to Azure via **federated credentials** on `azure/login@v3` — **no client secrets**. You need one Entra ID app registration / service principal with narrowly-scoped roles.

### 1. Create the app + federated credential

```bash
# App + SP
APP_ID=$(az ad app create --display-name byom-ci --query appId -o tsv)
az ad sp create --id "$APP_ID"

# Federated credential for the `byom` GH Environment on this repo
az ad app federated-credential create --id "$APP_ID" --parameters '{
  "name": "byom-env",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:msft-mfg-ai/foundry-byom-feature-support:environment:byom",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

Set the three GitHub Environment secrets on the `byom` environment: `AZURE_CLIENT_ID` = `$APP_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`.

### 2. Assign roles — conditional and narrowly scoped

The SP does two very different things depending on which workflow runs. Grant the minimum set for the workflows you actually use.

| Workflow | Purpose | Roles required | Scope |
| --- | --- | --- | --- |
| `feature-matrix.yml`, `feature-<slug>.yml` | **Test-only** — talks to an already-provisioned Foundry project via the data plane. | `Azure AI User` | The Foundry **project** resource |
| `ephemeral-e2e.yml` | Full lifecycle: `azd up` → tests → `azd down --purge`. Creates/deletes RG, Foundry account, APIM, ACR, storage, etc. | `Contributor` **plus** `Role Based Access Control Administrator` **with an ABAC condition** restricting which roles it can grant (see below). | The **resource group** (or the whole subscription, if you let `azd up` create the RG for you) |
| `feature-hosted-agents-canary.yml` (+ `azd deploy` of the canary agent) | Builds a container image and registers a Hosted Agent version. | `AcrPush` on the ACR; `Azure AI User` on the Foundry project | ACR + Foundry project |
| `deploy-site.yml` | Publishes to GH Pages. | *none* — pure GitHub-side, no Azure login. | — |

> **Why not `User Access Administrator`?** UAA (or Owner) on the CI SP is a privilege-escalation footgun — the SP could grant itself Owner. Bicep still needs *some* identity that can create role assignments (Foundry MI → APIM, Foundry MI → storage). Two safe options:
>
> 1. **Preferred — `Role Based Access Control Administrator` with an ABAC condition** that pins the allowed `roleDefinitionId`s to only the ones bicep actually needs (e.g. `Cognitive Services OpenAI User`, `Storage Blob Data Contributor`, `AcrPull`). CI can no longer grant Owner/UAA/Contributor to anyone, including itself.
> 2. **Simpler — bootstrap once, then drop the role.** A human runs `azd up` with Owner the first time to seed the role assignments, then future CI runs use only `Contributor` (bicep will `if (!existing) …` those assignments away). Works because `guid(...)`-named role assignments are idempotent.

**Conditional role assignment via bicep** (recommended — keeps the role-graph in code, no click-ops):

```bicep
// param ciPrincipalId string  // objectId of the byom-ci SP (NOT the appId)
// param assignCiRoles bool = false
// param scope resourceGroup

var azureAIUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'  // Azure AI User
var acrPushRoleId     = '8311e382-0749-4cb8-b61a-304f252e45ec'  // AcrPush

resource aiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignCiRoles) {
  name: guid(subscription().id, ciPrincipalId, foundryProject.id, azureAIUserRoleId)
  scope: foundryProject
  properties: {
    principalId: ciPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAIUserRoleId)
  }
}
```

The infra repo ([`ai-gateway-pe-testing`](https://github.com/msft-mfg-ai/ai-foundry-deployment-options/tree/main/options-infra/ai-gateway-pe-testing)) already accepts a `ciPrincipalId` parameter; toggle `assignCiRoles=true` per environment.

**Granting `Role Based Access Control Administrator` with an ABAC condition** (option 1 above):

```bash
SP_OID=$(az ad sp show --id "$APP_ID" --query id -o tsv)
RG_ID=$(az group show -n rg-byom-e2e --query id -o tsv)

# Allowed roles: Azure AI User, Cognitive Services OpenAI User, AcrPull, AcrPush,
# Storage Blob Data Contributor. Anything else is denied by the condition.
CONDITION='(
  (
    !(ActionMatches{"Microsoft.Authorization/roleAssignments/write"})
  )
  OR
  (
    @Request[Microsoft.Authorization/roleAssignments:RoleDefinitionId] ForAnyOfAnyValues:GuidEquals {
      53ca6127-db72-4b80-b1b0-d745d6d5456d,
      5e0bd9bd-7b93-4f28-af87-19fc36ad61bd,
      7f951dda-4ed3-4680-a7ca-43fe172d538d,
      8311e382-0749-4cb8-b61a-304f252e45ec,
      ba92f5b4-2d11-453d-a403-e96b0029c9fe
    }
  )
)'

az role assignment create \
  --assignee "$SP_OID" --scope "$RG_ID" \
  --role "Role Based Access Control Administrator" \
  --condition "$CONDITION" \
  --condition-version "2.0" \
  --description "byom-ci: allow granting only Foundry/ACR/storage data-plane roles"
```

**Alternative — pure `az cli` idempotent assignment** (skips if already present):

```bash
SP_OID=$(az ad sp show --id "$APP_ID" --query id -o tsv)
PROJECT_ID=$(az resource show --ids "$AZURE_AI_PROJECT_ID" --query id -o tsv)

# idempotent: skip if role already assigned
if ! az role assignment list --assignee "$SP_OID" --scope "$PROJECT_ID" \
       --role "Azure AI User" --query "[0].id" -o tsv | grep -q .; then
  az role assignment create --assignee "$SP_OID" --scope "$PROJECT_ID" --role "Azure AI User"
fi
```

### 3. Why *not* Owner / Subscription-scoped Contributor

- **`Azure AI User`** (not Contributor) on the Foundry project is enough for the test-only path — it grants data-plane access to agents / connections / responses without the ability to mutate the resource itself.
- `Contributor` (+ the constrained RBAC Admin role above) is only needed for the ephemeral E2E path, and should be **scoped to the RG** the ephemeral env lives in. Never grant subscription-scope unless `azd up` needs to create the RG.
- Never grant `Owner` or unconstrained `User Access Administrator` — either lets the SP escalate itself to full control of the subscription.
- The canary agent needs `AcrPush` only — Foundry pulls the image via its own managed identity.

## ▶️ Running the matrix in GitHub

Tests run in CI **independently of provisioning**. Because the
[`ai-gateway-pe-testing`](https://github.com/msft-mfg-ai/ai-foundry-deployment-options/tree/main/options-infra/ai-gateway-pe-testing)
bicep uses `uniqueString(resourceGroup().id, location)` for its naming token,
the deployment output names are **deterministic per RG + location**. That
means you can sync once and then re-run tests as many times as you want
against the same underlying resources.

### One-time environment setup

```bash
# 1. Provision (or reuse) the infra — locally, or via ephemeral-e2e.yml
cd ai-foundry-deployment-options/options-infra/ai-gateway-pe-testing
azd up

# 2. Copy the resulting bicep outputs + model choices into your local .env
#    (see .env.example)

# 3. Push every workflow-consumed key from .env into the `byom` GitHub Env
./scripts/sync_gh_env.sh .env
#    or, pointing at an azd env directly:
./scripts/sync_gh_env.sh ~/.../options-infra/ai-gateway-pe-testing/.azure/testing-byom
```

`sync_gh_env.sh` only pushes keys the reusable
[`_feature-test.yml`](.github/workflows/_feature-test.yml) actually consumes.
Keys not present in your `.env` are skipped — tests that need them will
`::warning::` and skip in CI, exactly like they do locally.

### Trigger the matrix

| Workflow | Purpose |
| --- | --- |
| [`feature-matrix.yml`](.github/workflows/feature-matrix.yml) | **Tests only.** Runs every `features/*/test.py` against whatever is in the `byom` GH env — no Azure state changes. |
| [`ephemeral-e2e.yml`](.github/workflows/ephemeral-e2e.yml) | Full lifecycle: `azd up` → matrix → `azd down --purge`. Weekly Saturday cron. |
| [`feature-<slug>.yml`](.github/workflows/) | Per-feature wrapper — auto-runs on PRs that touch that folder. |

```bash
gh workflow run feature-matrix.yml           # re-run everything
gh workflow run feature-matrix.yml -f feature_filter='tool-'   # subset
```

## ➕ Adding a new feature card

1. `mkdir features/<slug>`
2. Add `features/<slug>/feature.json` — include `azure_docs` + `sample_url` whenever possible. Add `test.py` if the feature has an automated test; omit `test_file` for a status-only card.
3. If you added a `test.py`, copy `.github/workflows/feature-prompt-agents-static.yml` to `feature-<slug>.yml`, update `paths:` and `with.feature:`.
4. Push — the site rebuilds and the new card appears automatically.

### Status taxonomy

| Field | Meaning |
| --- | --- |
| `support_status` ∈ `supported · partial · not_supported · not_confirmed` | Did **we** verify the BYOM behavior end-to-end? |
| `implementation_status` ∈ `ga · preview · in_progress · not_confirmed · tbd` | How is **engineering** tracking the underlying feature? |

> **Rule:** when `support_status ∈ { not_supported, not_confirmed }`, set `implementation_status = tbd`. If we haven't verified BYOM, we don't honestly know the underlying maturity either.

---

<div align="center">

**👉 [Open the live matrix](https://msft-mfg-ai.github.io/foundry-byom-feature-support/) 👈**

</div>
