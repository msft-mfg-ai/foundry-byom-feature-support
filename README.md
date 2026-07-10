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
