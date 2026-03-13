#!/usr/bin/env bash
set -euo pipefail

SURFACE_DB="${SURFACE_DB:-$SURFACE_ROOT/.surface-db}"
DATA_MODULE="${SURFACE_ROOT}/modules/data"

die() { echo "error: $1" >&2; exit 1; }

dsql() {
  (cd "$SURFACE_DB" && dolt sql "$@")
}

cmd_init() {
  if [ -d "$SURFACE_DB/.dolt" ]; then
    echo "Database already exists at $SURFACE_DB"
    echo "Use 'data reset' to recreate."
    return
  fi

  mkdir -p "$SURFACE_DB"
  (
    cd "$SURFACE_DB"
    dolt init --name "surface" --email "system@formabi.com"
    dolt sql < "$DATA_MODULE/schema.sql"
    dolt sql < "$DATA_MODULE/seed.sql"
    dolt add .
    dolt commit -m "init: schema and seed data"
  )
  echo "Database initialised at $SURFACE_DB"
}

cmd_reset() {
  if [ -d "$SURFACE_DB" ]; then
    rm -rf "$SURFACE_DB"
    echo "Removed $SURFACE_DB"
  fi
  cmd_init
}

cmd_status() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"

  echo "Database: $SURFACE_DB"
  echo ""
  echo "Tables:"
  dsql -q "SHOW TABLES;"
  echo ""
  echo "Row counts:"
  dsql -q "
    SELECT 'accounts' AS tbl, COUNT(*) AS cnt FROM accounts
    UNION ALL SELECT 'transactions', COUNT(*) FROM transactions
    UNION ALL SELECT 'postings', COUNT(*) FROM postings
    UNION ALL SELECT 'share_classes', COUNT(*) FROM share_classes
    UNION ALL SELECT 'holders', COUNT(*) FROM holders
    UNION ALL SELECT 'share_events', COUNT(*) FROM share_events
    UNION ALL SELECT 'pools', COUNT(*) FROM pools
    UNION ALL SELECT 'pool_members', COUNT(*) FROM pool_members
    UNION ALL SELECT 'contacts', COUNT(*) FROM contacts
    UNION ALL SELECT 'interactions', COUNT(*) FROM interactions
    UNION ALL SELECT 'deals', COUNT(*) FROM deals
    UNION ALL SELECT 'tags', COUNT(*) FROM tags;
  "
}

cmd_sql() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  if [ $# -gt 0 ]; then
    dsql -q "$*"
  else
    dsql
  fi
}

cmd_log() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt log "$@")
}

cmd_diff() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt diff "$@")
}

cmd_commit() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt add . && dolt commit "$@")
}

cmd_branch() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt branch "$@")
}

cmd_checkout() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt checkout "$@")
}

cmd_remote() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  if [ $# -eq 0 ]; then
    (cd "$SURFACE_DB" && dolt remote -v)
  else
    (cd "$SURFACE_DB" && dolt remote "$@")
  fi
}

cmd_push() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  local remote="${1:-origin}"
  (cd "$SURFACE_DB" && dolt push "$remote" main)
  echo "Pushed to $remote"
}

cmd_pull() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  local remote="${1:-origin}"
  (cd "$SURFACE_DB" && dolt pull "$remote")
  echo "Pulled from $remote"
}

cmd_clone() {
  local remote_url="$1"
  if [ -d "$SURFACE_DB/.dolt" ]; then
    echo "Database already exists at $SURFACE_DB"
    echo "Use 'data reset' to recreate, or 'data pull' to update."
    return
  fi
  mkdir -p "$(dirname "$SURFACE_DB")"
  dolt clone "$remote_url" "$SURFACE_DB"
  echo "Cloned $remote_url to $SURFACE_DB"
}

cmd_help() {
  echo "data — surface database (dolt)"
  echo ""
  echo "Usage: data <command> [args]"
  echo ""
  echo "Commands:"
  echo "  init               Initialise the database (schema + seed data)"
  echo "  reset              Drop and recreate the database"
  echo "  status             Show tables and row counts"
  echo "  sql [query]        Run a SQL query (or open interactive shell)"
  echo "  log                Show dolt commit history"
  echo "  diff [ref]         Show uncommitted changes (or diff against ref)"
  echo "  commit -m 'msg'    Commit current changes"
  echo "  branch [name]      List or create branches"
  echo "  checkout <branch>  Switch branches"
  echo "  remote [args]      List or manage remotes"
  echo "  push [remote]      Push to remote (default: origin)"
  echo "  pull [remote]      Pull from remote (default: origin)"
  echo "  clone <url>        Clone database from remote"
  echo "  help               Show this help"
}

case "${1:-help}" in
  init)     cmd_init ;;
  reset)    cmd_reset ;;
  status)   cmd_status ;;
  sql)      shift; cmd_sql "$@" ;;
  log)      shift; cmd_log "$@" ;;
  diff)     shift; cmd_diff "$@" ;;
  commit)   shift; cmd_commit "$@" ;;
  branch)   shift; cmd_branch "$@" ;;
  checkout) shift; cmd_checkout "$@" ;;
  remote)   shift; cmd_remote "$@" ;;
  push)     shift; cmd_push "$@" ;;
  pull)     shift; cmd_pull "$@" ;;
  clone)    shift; cmd_clone "$@" ;;
  help|*)   cmd_help ;;
esac
