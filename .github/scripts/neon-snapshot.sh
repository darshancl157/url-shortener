#!/usr/bin/env bash
# Replace the Neon branch "pre-deploy" with a fresh copy of the database as it is right now.
# Keeps exactly one snapshot: the state before the most recent deploy.
set -euo pipefail

api="https://console.neon.tech/api/v2/projects/${NEON_PROJECT_ID}"
auth="Authorization: Bearer ${NEON_API_KEY}"

old=$(curl -fsS -H "$auth" "$api/branches" | jq -r '.branches[] | select(.name == "pre-deploy") | .id')
if [ -n "$old" ]; then
  echo "Deleting previous snapshot $old"
  curl -fsS -X DELETE -H "$auth" "$api/branches/$old" > /dev/null
fi

echo "Creating snapshot"
curl -fsS -X POST -H "$auth" -H "Content-Type: application/json" \
  -d '{"branch": {"name": "pre-deploy"}}' \
  "$api/branches" | jq '.branch | {id, name, parent_id, created_at}'