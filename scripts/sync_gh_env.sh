#!/usr/bin/env bash
# Populate the `byom` GitHub Environment with every KEY=VALUE line found in a
# local .env file, so the reusable test workflow (_feature-test.yml) can run
# **independently of any deployment** — once you sync, tests can be re-run
# against the same underlying infrastructure without re-provisioning.
#
# The .env file can be:
#   1. The repo-local .env you use for local pytest runs (recommended — it is
#      the exact same source of truth), OR
#   2. An azd env dir; the script auto-detects `<dir>/.env`.
#
# Values from the workflow that are NOT in your .env are simply not pushed
# (so tests that need them will `::warning::` and skip, exactly as they do
# locally).
#
# Usage:
#   scripts/sync_gh_env.sh                                 # uses ./.env
#   scripts/sync_gh_env.sh path/to/.env                    # explicit file
#   scripts/sync_gh_env.sh path/to/azd/env-dir             # dir with .env
#   scripts/sync_gh_env.sh path/to/.env owner/repo envname
#
# Requires: gh (authenticated with admin:repo on the target repo).

set -euo pipefail

SRC="${1:-.env}"
GH_REPO="${2:-msft-mfg-ai/foundry-byom-feature-support}"
GH_ENV="${3:-byom}"

if [[ -d "${SRC}" && -f "${SRC}/.env" ]]; then
  ENV_FILE="${SRC}/.env"
else
  ENV_FILE="${SRC}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "usage: $0 <path-to-.env-or-dir> [gh-repo] [gh-env-name]" >&2
  echo "  (could not find ${ENV_FILE})" >&2
  exit 2
fi

# Superset of every var the reusable workflow reads. Only keys in this list
# get pushed — keeps stray local values (AZURE_*, subscription IDs, etc.) out
# of the GH environment.
WORKFLOW_VARS=(
  PROJECT_ENDPOINT FOUNDRY_ACCOUNT_ENDPOINT FOUNDRY_REGION
  CHAT_MODEL REASONING_MODEL IMAGE_MODEL IMAGE_DEPLOYMENT_NAME
  AI_GATEWAY_CONNECTION_STATIC AI_GATEWAY_CONNECTION_DYNAMIC
  AI_GATEWAY_CONNECTION_ANTHROPIC AI_GATEWAY_CONNECTION_MODELGATEWAY
  AI_GATEWAY_CONNECTION_SERVERLESS
  ANTHROPIC_MODEL MODELGATEWAY_MODEL SERVERLESS_MODEL
  PROMPT_AGENT_NAME_STATIC PROMPT_AGENT_NAME_DYNAMIC
  HOSTED_AGENT_NAME_STATIC HOSTED_AGENT_NAME_DYNAMIC
  BING_CONNECTION_ID FILE_SEARCH_VECTOR_STORE_ID
  AZURE_AI_SEARCH_CONNECTION_ID AZURE_AI_SEARCH_INDEX_NAME
  SHAREPOINT_CONNECTION_ID FABRIC_CONNECTION_ID
  A2A_REMOTE_AGENT_ENDPOINT A2A_PROJECT_CONNECTION_ID A2A_ENDPOINT
  LOGIC_APP_RESOURCE_ID LOGIC_APP_WORKFLOW_NAME
  COMPUTER_USE_ENVIRONMENT OPENAPI_SPEC_PATH
  KNOWLEDGE_BASE_ID MEMORY_STORE_ID
  MCP_SERVER_URL MCP_SERVER_URL_AGENT_IDENTITY MCP_SERVER_URL_OAUTH
  FOUNDRY_IQ_MCP_URL WORK_IQ_MCP_URL WEB_IQ_MCP_URL FABRIC_IQ_MCP_URL
  EVAL_JUDGE_MODEL RED_TEAM_TARGET_MODEL
  MODERATION_MODEL WEB_SEARCH_MODEL VIDEO_MODEL IMAGE_VARIATION_MODEL
  REALTIME_TRANSCRIPTION_MODEL REALTIME_TRANSLATION_MODEL
)

get() {
  local key="$1"
  grep -E "^${key}=" "${ENV_FILE}" | tail -n1 | sed -E "s/^${key}=//" | sed -E 's/^"(.*)"$/\1/'
}

echo "Source .env: ${ENV_FILE}"
echo "Target:      gh repo=${GH_REPO}  env=${GH_ENV}"
echo

pushed=0
skipped=0
for gh_var in "${WORKFLOW_VARS[@]}"; do
  value="$(get "${gh_var}" || true)"
  if [[ -z "${value}" ]]; then
    printf '  %-40s (unset — skipping)\n' "${gh_var}"
    skipped=$((skipped + 1))
    continue
  fi
  # Truncate display for long values (resource IDs).
  display="${value}"
  if (( ${#display} > 60 )); then display="${display:0:57}..."; fi
  printf '  %-40s ← %s\n' "${gh_var}" "${display}"
  gh variable set "${gh_var}" --repo "${GH_REPO}" --env "${GH_ENV}" --body "${value}" >/dev/null
  pushed=$((pushed + 1))
done

echo
echo "Pushed ${pushed} variables, skipped ${skipped}."
echo "Verify:  gh variable list --repo ${GH_REPO} --env ${GH_ENV}"

