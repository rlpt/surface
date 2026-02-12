#!/usr/bin/env bash
set -euo pipefail

echo "surface — formabi onboarding"
echo "============================="
echo ""

ROSTER_FILE="${SURFACE_ROOT}/people/roster.json"
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "")

if [ -z "$GIT_EMAIL" ]; then
  echo "Step 1: Configure git"
  echo "  git config --global user.email you@example.com"
  echo "  git config --global user.name \"Your Name\""
  echo ""
  echo "Then re-enter the shell: exit && nix develop"
  exit 0
fi

USER_JSON=""
if [ -f "$ROSTER_FILE" ]; then
  USER_JSON=$(jq --arg email "$GIT_EMAIL" '.[] | select(.email == $email)' "$ROSTER_FILE" 2>/dev/null || echo "")
fi

if [ -z "$USER_JSON" ]; then
  echo "You ($GIT_EMAIL) are not in the roster."
  echo ""
  echo "Surface is the root shell for the formabi company-as-code system."
  echo "To be added to the roster, contact an admin or submit a PR adding"
  echo "your entry to people/roster.json."
  echo ""
  echo "You can still use the base shell — git, jq, halp, and whoami are available."
  exit 0
fi

NAME=$(echo "$USER_JSON" | jq -r '.name')
ROLES=$(echo "$USER_JSON" | jq -r '.roles[]')
REGION=$(echo "$USER_JSON" | jq -r '.region')

echo "Welcome, $NAME! ($GIT_EMAIL)"
echo "Region: $REGION"
echo ""

echo "Your roles:"
ROLES_FILE="${SURFACE_ROOT}/roles/roles.json"
for role in $ROLES; do
  if [ -f "$ROLES_FILE" ]; then
    desc=$(jq -r --arg r "$role" '.[$r].description // "No description"' "$ROLES_FILE")
    echo "  - $role: $desc"
  else
    echo "  - $role"
  fi
done
echo ""

echo "Useful commands:"
echo "  halp     — see all available commands"
echo "  whoami   — see your identity and module status"
