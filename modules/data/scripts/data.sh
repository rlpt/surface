#!/usr/bin/env bash
set -euo pipefail

SURFACE_ROOT="${SURFACE_ROOT:-.}"
DATA_DIR="${SURFACE_ROOT}/data"

die() { echo "error: $1" >&2; exit 1; }

cmd_status() {
  echo "Data directory: $DATA_DIR"
  echo ""
  for f in "$DATA_DIR"/*.toml; do
    [ -f "$f" ] || continue
    name=$(basename "$f" .toml)
    # Count array-of-tables entries
    count=$(grep -c '^\[\[' "$f" 2>/dev/null || echo "0")
    echo "  $name.toml  ($count entries)"
  done
}

cmd_check() {
  echo "Running module checks..."
  local errors=0
  python3 "$SURFACE_ROOT/modules/shares/scripts/shares.py" check || errors=$((errors + 1))
  python3 "$SURFACE_ROOT/modules/accounts/scripts/accounts.py" check || errors=$((errors + 1))
  if [ "$errors" -gt 0 ]; then
    echo ""
    echo "$errors module(s) reported errors"
    exit 1
  fi
  echo ""
  echo "All checks passed"
}

cmd_edit() {
  ${EDITOR:-vi} "$DATA_DIR"
}

cmd_log() {
  git -C "$SURFACE_ROOT" log --oneline -- data/
}

cmd_diff() {
  git -C "$SURFACE_ROOT" diff -- data/
}

cmd_help() {
  echo "data — surface company data (TOML files in data/)"
  echo ""
  echo "Usage: data <command> [args]"
  echo ""
  echo "Commands:"
  echo "  status             Show data files and entry counts"
  echo "  check              Run all module validation checks"
  echo "  edit               Open data/ in \$EDITOR"
  echo "  log                Show git history for data/"
  echo "  diff               Show uncommitted changes to data/"
  echo "  help               Show this help"
  echo ""
  echo "Data files live in data/*.toml and are versioned by git."
}

case "${1:-help}" in
  status)   cmd_status ;;
  check)    cmd_check ;;
  edit)     cmd_edit ;;
  log)      shift; cmd_log "$@" ;;
  diff)     shift; cmd_diff "$@" ;;
  help|*)   cmd_help ;;
esac
