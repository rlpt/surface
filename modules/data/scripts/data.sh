#!/usr/bin/env bash
set -euo pipefail

SURFACE_ROOT="${SURFACE_ROOT:-.}"
DATA_DIR="${SURFACE_ROOT}/data"

die() { echo "error: $1" >&2; exit 1; }

cmd_status() {
  echo "Data directory: $DATA_DIR"
  echo ""
  for f in "$DATA_DIR"/*.yaml; do
    [ -f "$f" ] || continue
    domain=$(basename "$f" .yaml)
    # Count top-level keys and their list lengths
    echo "  $domain.yaml"
    python3 -c "
import yaml, sys
with open('$f') as fh:
    data = yaml.safe_load(fh) or {}
for key, val in data.items():
    if isinstance(val, list):
        print(f'    {key}: {len(val)} entries')
    else:
        print(f'    {key}: (scalar)')
"
  done
}

cmd_check() {
  echo "Running data checks..."
  python3 -c "
import sys, os
sys.path.insert(0, os.path.join('$SURFACE_ROOT', 'modules', 'data', 'scripts'))
import datalib

all_errors = []
for domain in ['shares', 'officers', 'compliance', 'board']:
    data = datalib.load(domain)

    # Schema lint
    errs = datalib.lint(domain, data)
    for e in errs:
        all_errors.append(f'  {domain} lint: {e}')

    # Referential integrity
    errs = datalib.validate_refs(domain, data)
    for e in errs:
        all_errors.append(f'  {domain} refs: {e}')

if all_errors:
    print('data errors:', file=sys.stderr)
    for e in all_errors:
        print(e, file=sys.stderr)
    sys.exit(1)
else:
    print('OK — all data valid')
"
}

cmd_lint() {
  echo "Linting data..."
  python3 -c "
import sys, os
sys.path.insert(0, os.path.join('$SURFACE_ROOT', 'modules', 'data', 'scripts'))
import datalib

all_errors = []
for domain in ['shares', 'officers', 'compliance', 'board']:
    data = datalib.load(domain)
    errs = datalib.lint(domain, data)
    for e in errs:
        all_errors.append(f'  {domain}: {e}')

if all_errors:
    print('lint errors:', file=sys.stderr)
    for e in all_errors:
        print(e, file=sys.stderr)
    sys.exit(1)
else:
    print('OK — all data passes lint')
"
}

cmd_changelog() {
  local domain="${1:-}"
  local since="${2:-}"
  if [ -z "$domain" ]; then
    die "usage: data changelog <domain> [--since date]"
  fi
  local since_arg=""
  if [ -n "$since" ]; then
    since_arg="$since"
  fi
  python3 -c "
import sys, os
sys.path.insert(0, os.path.join('$SURFACE_ROOT', 'modules', 'data', 'scripts'))
import datalib
since = '$since_arg' if '$since_arg' else None
entries = datalib.changelog('$domain', since)
if not entries:
    print('No changes found.')
else:
    for e in entries:
        print(f\"{e['commit']}  {e['date']}  {e['message']}\")
"
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
  echo "data — surface company data (YAML files in data/)"
  echo ""
  echo "Usage: data <command> [args]"
  echo ""
  echo "Commands:"
  echo "  status             Show data files and entry counts"
  echo "  check              Run lint + referential integrity checks"
  echo "  lint               Run schema validation only"
  echo "  edit               Open data/ in \$EDITOR"
  echo "  log                Show git history for data/"
  echo "  diff               Show uncommitted changes to data/"
  echo "  changelog <domain> [--since date]  Show structured change history"
  echo "  help               Show this help"
  echo ""
  echo "Data files live in data/<domain>.yaml and are versioned by git."
}

case "${1:-help}" in
  status)    cmd_status ;;
  check)     cmd_check ;;
  lint)      cmd_lint ;;
  edit)      cmd_edit ;;
  log)       shift; cmd_log "$@" ;;
  diff)      shift; cmd_diff "$@" ;;
  changelog) shift; cmd_changelog "$@" ;;
  help|*)    cmd_help ;;
esac
