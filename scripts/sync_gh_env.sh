#!/usr/bin/env bash
# Populate the `byom` GitHub Environment with variables read from an azd
# environment produced by the `ai-gateway-pe-testing` bicep variant.
#
# Usage:
#   scripts/sync_gh_env.sh <path-to-azd-env-dir> [gh-repo] [gh-env-name]
#
# Example:
#   scripts/sync_gh_env.sh \
#     ~/projects/otis/ai-foundry-config-testing/options-infra/ai-gateway-pe-testing/.azure/testing-byom
#
# Requires: gh (authenticated), jq. The current gh user needs
# `admin:repo` on the target repo to write environment variables.

set -euo pipefail

AZD_ENV_DIR="${1:-}"
GH_REPO="${2:-msft-mfg-ai/foundry-byom-feature-support}"
GH_ENV="${3:-byom}"

if [[ -z "${AZD_ENV_DIR}" || ! -f "${AZD_ENV_DIR}/.env" ]]; then
  echo "usage: $0 <path-to-azd-env-dir> [gh-repo] [gh-env-name]" >&2
  echo "  (expected ${AZD_ENV_DIR}/.env to exist)" >&2
  exit 2
fi

# ── azd-provisioned values that must land in the GH env unchanged ──
# key = GH environment variable name
# value = azd .env key it comes from
declare -A MAPPING=(
  [PROJECT_ENDPOINT]=PROJECT_ENDPOINT
  [AI_GATEWAY_CONNECTION_STATIC]=AI_GATEWAY_CONNECTION_STATIC
  [AI_GATEWAY_CONNECTION_DYNAMIC]=AI_GATEWAY_CONNECTION_DYNAMIC
  [BING_CONNECTION_ID]=BING_CONNECTION_ID
  [AZURE_AI_SEARCH_CONNECTION_ID]=AZURE_AI_SEARCH_CONNECTION_ID
  [AZURE_AI_SEARCH_INDEX_NAME]=AZURE_AI_SEARCH_INDEX_NAME
  [FOUNDRY_NAME]=FOUNDRY_NAME
  [RESOURCE_GROUP]=RESOURCE_GROUP
  [AZURE_ENV_NAME]=AZURE_ENV_NAME
  [AZURE_LOCATION]=AZURE_LOCATION
)

# Parse "KEY=\"value\"" style lines from the azd .env file.
get() {
  local key="$1"
  grep -E "^${key}=" "${AZD_ENV_DIR}/.env" | tail -n1 | sed -E "s/^${key}=//" | sed -E 's/^"(.*)"$/\1/'
}

echo "Reading azd env from: ${AZD_ENV_DIR}/.env"
echo "Target: gh repo=${GH_REPO}  env=${GH_ENV}"
echo

for gh_var in "${!MAPPING[@]}"; do
  azd_key="${MAPPING[$gh_var]}"
  value="$(get "${azd_key}")"
  if [[ -z "${value}" ]]; then
    echo "::warning:: ${azd_key} not set in azd env — skipping ${gh_var}"
    continue
  fi
  printf '  %-32s ← %s\n' "${gh_var}" "${value}"
  gh variable set "${gh_var}" --repo "${GH_REPO}" --env "${GH_ENV}" --body "${value}" >/dev/null
done

echo
echo "Done. Verify with:"
echo "  gh variable list --repo ${GH_REPO} --env ${GH_ENV}"
