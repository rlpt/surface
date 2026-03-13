#!/usr/bin/env bash
set -euo pipefail

SURFACE_ROOT="${SURFACE_ROOT:-.}"
DATA_DIR="${SURFACE_ROOT}/data"

die() { echo "error: $1" >&2; exit 1; }

cmd_status() {
  echo "Data directory: $DATA_DIR"
  echo ""
  for d in "$DATA_DIR"/*/; do
    [ -d "$d" ] || continue
    domain=$(basename "$d")
    echo "  $domain/"
    for f in "$d"*.csv; do
      [ -f "$f" ] || continue
      name=$(basename "$f" .csv)
      # Count data rows (subtract 1 for header)
      total=$(wc -l < "$f" | tr -d ' ')
      rows=$((total - 1))
      echo "    $name.csv  ($rows rows)"
    done
  done
}

cmd_check() {
  echo "Running module checks..."
  local errors=0
  python3 "$SURFACE_ROOT/modules/shares/scripts/shares.py" check || errors=$((errors + 1))
  python3 "$SURFACE_ROOT/modules/accounts/scripts/accounts.py" check || errors=$((errors + 1))
  echo ""
  echo "Running referential integrity checks..."
  python3 -c "
import sys, os
sys.path.insert(0, os.path.join('$SURFACE_ROOT', 'modules', 'data', 'scripts'))
import datalib
all_errors = []
for domain in ['shares', 'accounts', 'crm', 'board']:
    data = datalib.load(domain)
    errs = datalib.validate_refs(domain, data)
    for e in errs:
        all_errors.append(f'  {domain}: {e}')
if all_errors:
    print('referential integrity errors:')
    for e in all_errors:
        print(e)
    sys.exit(1)
else:
    print('OK — all references valid')
" || errors=$((errors + 1))
  if [ "$errors" -gt 0 ]; then
    echo ""
    echo "$errors check(s) reported errors"
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
  echo "Data files live in data/<domain>/*.csv and are versioned by git."
}

case "${1:-help}" in
  status)   cmd_status ;;
  check)    cmd_check ;;
  edit)     cmd_edit ;;
  log)      shift; cmd_log "$@" ;;
  diff)     shift; cmd_diff "$@" ;;
  help|*)   cmd_help ;;
esac
