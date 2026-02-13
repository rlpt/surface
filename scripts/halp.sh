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
echo "Accounts (hledger bookkeeping):"
echo "  accounts bal [acct]         Current balances (optionally filter by account)"
echo "  accounts is [-p period]     Income statement"
echo "  accounts bs                 Balance sheet"
echo "  accounts reg <acct>         Transaction register for an account"
echo "  accounts stats              Journal health (date range, txn count)"
echo "  accounts check              Validate balanced entries and declared accounts"
echo ""
echo "Shares (cap table management):"
echo "  shares table                Show cap table with percentages and vesting"
echo "  shares export               Output cap table as CSV"
echo "  shares holders              List all shareholders with totals"
echo "  shares history [holder]     Show share events (optionally filter by holder)"
echo "  shares check                Validate ledger consistency"
echo "  shares brief                Compact context dump for agent warm-up"
echo "  shares pdf table            Cap table as PDF"
echo "  shares pdf history          Share event history as PDF"
echo "  shares pdf holder <id>      Individual holder statement as PDF"
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
