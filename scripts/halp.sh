#!/usr/bin/env bash
set -euo pipefail

echo "surface shell — available commands"
echo "==================================="
echo ""
echo "Base commands:"
echo "  halp                        Show this help"
echo "  whoami                      Show your identity, roles, and module status"
echo "  onboard                     Guided setup for new users"
echo ""
if [ -n "${SURFACE_MODULE_HELP:-}" ]; then
  echo "$SURFACE_MODULE_HELP"
  echo ""
fi

ROSTER_FILE="${SURFACE_ROOT}/people/roster.json"
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

USER_ROLES="[]"
if [ -n "$GIT_EMAIL" ] && [ -f "$ROSTER_FILE" ]; then
  USER_ROLES=$(jq -r --arg email "$GIT_EMAIL" \
    '[.[] | select(.email == $email) | .roles[]] | unique' \
    "$ROSTER_FILE" 2>/dev/null || echo "[]")
fi

if [ -n "${SURFACE_ROLES_JSON:-}" ]; then
  for role in $(echo "$SURFACE_ROLES_JSON" | jq -r 'keys[]'); do
    desc=$(echo "$SURFACE_ROLES_JSON" | jq -r --arg r "$role" '.[$r].description')
    has_role=$(echo "$USER_ROLES" | jq --arg r "$role" 'index($r) != null')
    if [ "$has_role" = "true" ]; then
      echo "[$role] $desc  ✓ (your role)"
    else
      echo "[$role] $desc  — (not your role)"
    fi
  done
fi
