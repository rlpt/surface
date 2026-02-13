#!/usr/bin/env bash
set -euo pipefail

echo "surface shell — available commands"
echo "==================================="
echo ""
echo "Base commands (everyone):"
echo "  halp       Show this help"
echo "  whoami     Show your identity, roles, and module status"
echo "  onboard    Guided setup for new users"
echo "  accounts   hledger shortcut (accounts bal, accounts is, etc.)"
echo ""

ROSTER_FILE="${SURFACE_ROOT}/people/roster.json"
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

USER_ROLES="[]"
if [ -n "$GIT_EMAIL" ] && [ -f "$ROSTER_FILE" ]; then
  USER_ROLES=$(jq -r --arg email "$GIT_EMAIL" \
    '[.[] | select(.email == $email) | .roles[]] | unique' \
    "$ROSTER_FILE" 2>/dev/null || echo "[]")
fi

ROLES_FILE="${SURFACE_ROOT}/roles/roles.json"
if [ -f "$ROLES_FILE" ]; then
  for role in $(jq -r 'keys[]' "$ROLES_FILE"); do
    desc=$(jq -r --arg r "$role" '.[$r].description' "$ROLES_FILE")
    has_role=$(echo "$USER_ROLES" | jq --arg r "$role" 'index($r) != null')
    if [ "$has_role" = "true" ]; then
      echo "[$role] $desc  ✓ (your role)"
    else
      echo "[$role] $desc  — (not your role)"
    fi
  done
fi
