#!/usr/bin/env zsh
set -euo pipefail

# Loads environment variables and runs Power BI/Fabric XMLA troubleshooting checks.
# This script does NOT print secrets; it uses them only for token acquisition.

ROOT_DIR=$(cd -- "$(dirname -- "$0")"/.. && pwd)
ENV_FILE="$ROOT_DIR/CODE/.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "[ERROR] .env not found at $ENV_FILE" >&2
  exit 1
fi

# Helper to mask secrets safely
mask_secret() {
  local secret="$1"
  if [[ -z "$secret" ]]; then
    printf "****"
    return
  fi
  local slen=${#secret}
  if (( slen >= 8 )); then
    local first4 last4
    first4=$(printf "%s" "$secret" | awk '{print substr($0,1,4)}')
    last4=$(printf "%s" "$secret" | awk '{print substr($0,length($0)-3)}')
    printf "%s****%s" "$first4" "$last4"
  else
    printf "****"
  fi
}

# Load environment vars from CODE/.env (simple parser: ignores comments and blank lines)
while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  # Trim possible surrounding quotes
  value=${value#\"}
  value=${value%\"}
  value=${value#\'}
  value=${value%\'}
  # Trim leading/trailing whitespace
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  # Export without allowing shell to expand $ inside secrets
  escaped=${value//\'/\'\\\'\'}
  eval "export $key='$escaped'"
done < <(grep -E '^[A-Z0-9_]+=' "$ENV_FILE")

# Sanity print (env summary)
printf "[ENV] Tenant: %s\n" "${PBI_TENANT_ID:-<unset>}"
printf "[ENV] Client ID: %s\n" "${PBI_CLIENT_ID:-<unset>}"
if [[ "${SHOW_FULL_SECRETS:-0}" == "1" ]]; then
  printf "[ENV] Client Secret: %s\n" "${PBI_CLIENT_SECRET:-<unset>}"
else
  printf "[ENV] Client Secret: %s\n" "$(mask_secret "${PBI_CLIENT_SECRET:-}")"
fi
printf "[ENV] XMLA Endpoint: %s\n" "${PBI_XMLA_ENDPOINT:-<unset>}"
printf "[ENV] Dataset (Catalog): %s\n" "${PBI_DATASET_NAME:-<unset>}"

# 1) Show current Azure account context
if command -v az >/dev/null 2>&1; then
  printf "\n[STEP] Azure account context\n"
  printf "[RUN] az account show -o table\n"
  az account show -o table || true
  printf "\n[STEP] Available tenants\n"
  printf "[RUN] az account tenant list -o table\n"
  az account tenant list -o table || true
else
  printf "[WARN] Azure CLI (az) not found; skipping az context checks\n"
fi

# 2) Acquire token via client credentials (AAD v2 endpoint)
PBI_SCOPE="https%3A%2F%2Fanalysis.windows.net%2Fpowerbi%2Fapi%2F.default"
printf "\n[STEP] Acquire AAD token (client credentials)\n"
if [[ "${SHOW_FULL_SECRETS:-0}" == "1" ]]; then
  printf "[RUN] curl -s -X POST -H 'Content-Type: application/x-www-form-urlencoded' -d client_id=%s -d scope=%s -d client_secret=%s -d grant_type=client_credentials https://login.microsoftonline.com/%s/oauth2/v2.0/token\n" "${PBI_CLIENT_ID:-}" "$PBI_SCOPE" "${PBI_CLIENT_SECRET:-}" "${PBI_TENANT_ID:-}"
else
  printf "[RUN] curl -s -X POST -H 'Content-Type: application/x-www-form-urlencoded' -d client_id=%s -d scope=%s -d client_secret=%s -d grant_type=client_credentials https://login.microsoftonline.com/%s/oauth2/v2.0/token\n" "${PBI_CLIENT_ID:-}" "$PBI_SCOPE" "$(mask_secret "${PBI_CLIENT_SECRET:-}")" "${PBI_TENANT_ID:-}"
fi
TOKEN_JSON=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=${PBI_CLIENT_ID}" \
  -d "scope=${PBI_SCOPE}" \
  -d "client_secret=${PBI_CLIENT_SECRET}" \
  -d "grant_type=client_credentials" \
  "https://login.microsoftonline.com/${PBI_TENANT_ID}/oauth2/v2.0/token")

ACCESS_TOKEN=$(echo "$TOKEN_JSON" | jq -r '.access_token // empty')
if [[ -z "$ACCESS_TOKEN" ]]; then
  echo "[ERROR] Failed to get access token:" >&2
  echo "$TOKEN_JSON" | jq . >&2 || echo "$TOKEN_JSON" >&2
  exit 2
fi

printf "[OK] Acquired AAD token\n"

# 3) Power BI Admin/Workspace checks
# List capacities
printf "\n[STEP] List capacities\n"
printf "[RUN] curl -s -H 'Authorization: Bearer ***' https://api.powerbi.com/v1.0/myorg/capacities | jq '.value[] | {id, displayName, region, state}'\n"
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://api.powerbi.com/v1.0/myorg/capacities \
  | jq '.value[] | {id, displayName, region, state}' || true

# List workspaces (groups)
printf "\n[STEP] List workspaces (groups)\n"
printf "[RUN] curl -s -H 'Authorization: Bearer ***' https://api.powerbi.com/v1.0/myorg/groups | jq '.value[] | {id, name, isOnDedicatedCapacity, capacityId}'\n"
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://api.powerbi.com/v1.0/myorg/groups \
  | jq '.value[] | {id, name, isOnDedicatedCapacity, capacityId}' || true

# 4) Optional: Try a lightweight XMLA call (metadata discovery) using the token
# This will not run DAX; it just checks reachability and auth (may still 401/403 without proper permissions)
# Note: XMLA uses SOAP. We send an empty Discover to test connectivity.

printf "\n[STEP] Credentials used for XMLA call\n"
printf "[INFO] Using Client ID: %s\n" "${PBI_CLIENT_ID:-<unset>}"
if [[ -z "${PBI_CLIENT_SECRET:-}" ]]; then
  printf "[WARN] PBI_CLIENT_SECRET is not set\n"
else
  if [[ "${SHOW_FULL_SECRETS:-0}" == "1" ]]; then
    printf "[INFO] Using Client Secret: %s\n" "${PBI_CLIENT_SECRET}"
  else
    printf "[INFO] Using Client Secret (masked): %s\n" "$(mask_secret "$PBI_CLIENT_SECRET")"
  fi
fi

printf "[STEP] XMLA request preview\n"
printf "[RUN] POST %s with SOAP DISCOVER (Catalog=%s) and Authorization: Bearer <token>\n" "${PBI_XMLA_ENDPOINT:-<unset>}" "${PBI_DATASET_NAME:-<unset>}"

XMLA_DISCOVER='<?xml version="1.0" encoding="utf-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/">
  <Body>
    <Discover xmlns="urn:schemas-microsoft-com:xml-analysis">
      <RequestType>DISCOVER_DATASOURCES</RequestType>
      <Restrictions />
      <Properties>
        <PropertyList>
          <Catalog>'"$PBI_DATASET_NAME"'</Catalog>
        </PropertyList>
      </Properties>
    </Discover>
  </Body>
</Envelope>'

printf "\n[STEP] XMLA DISCOVER to %s (Catalog=%s)\n" "${PBI_XMLA_ENDPOINT}" "${PBI_DATASET_NAME}"
XMLA_RESP=$(curl -s -w "\n%{http_code}" -X POST \
  -H "Content-Type: text/xml" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-binary @- \
  "$PBI_XMLA_ENDPOINT" <<< "$XMLA_DISCOVER")

HTTP_BODY=$(echo "$XMLA_RESP" | sed '$d')
HTTP_CODE=$(echo "$XMLA_RESP" | tail -n1)

printf "[INFO] HTTP status: %s\n" "$HTTP_CODE"
if [[ "$HTTP_CODE" != "200" ]]; then
  printf "[WARN] Non-200 from XMLA endpoint. Truncated body:\n"
  printf "%s" "$HTTP_BODY" | head -c 800
else
  printf "[OK] XMLA endpoint reachable; response received\n"
fi

# 5) Hints
cat <<'EOF'

[HINTS]
- 401 Unauthorized: Check service principal is added to the workspace with Build permission; verify tenant settings (XMLA + service principals) in Power BI Admin portal.
- 403 Forbidden: Same as above; ensure capacity/workspace membership and dataset access.
- 404 Not Found: Verify XMLA endpoint URL and dataset (Catalog) name exactly.
- 429/5xx: Retry with backoff; transient or throttling.
- Region mismatch: Workspace must be in the same region as the capacity you assign.
EOF
