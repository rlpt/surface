#!/usr/bin/env bash
set -euo pipefail

ROSTER_FILE="${SURFACE_ROOT}/people/roster.json"
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

if [ -z "$GIT_EMAIL" ]; then
  echo "Identity: Unidentified"
  echo "Reason:   No git email configured"
  echo ""
  echo "Set your git email:  git config --global user.email you@example.com"
  echo "Then re-enter the shell: exit && nix develop"
  exit 0
fi

if [ ! -f "$ROSTER_FILE" ]; then
  echo "Identity: Unidentified"
  echo "Reason:   Roster file not found"
  exit 0
fi

USER_JSON=$(jq --arg email "$GIT_EMAIL" '.[] | select(.email == $email)' "$ROSTER_FILE" 2>/dev/null || echo "")

if [ -z "$USER_JSON" ]; then
  echo "Identity: Unidentified"
  echo "Email:    $GIT_EMAIL"
  echo "Reason:   Not found in roster"
  echo ""
  echo "Run 'onboard' for setup instructions."
  exit 0
fi

NAME=$(echo "$USER_JSON" | jq -r '.name')
ROLES=$(echo "$USER_JSON" | jq -r '.roles | join(", ")')
REGION=$(echo "$USER_JSON" | jq -r '.region')
STARTED=$(echo "$USER_JSON" | jq -r '.started')

echo "Identity: $NAME"
echo "Email:    $GIT_EMAIL"
echo "Roles:    $ROLES"
echo "Region:   $REGION"
echo "Started:  $STARTED"
echo ""

echo "Modules:"
if [ -n "${SURFACE_MODULES:-}" ]; then
  IFS=',' read -ra MODS <<< "$SURFACE_MODULES"
  for mod in "${MODS[@]}"; do
    echo "  - $mod"
  done
else
  echo "  (no modules)"
fi
