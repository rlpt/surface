#!/usr/bin/env bash
set -euo pipefail

SURFACE_DB="${SURFACE_DB:-$SURFACE_ROOT/.surface-db}"

die() { echo "error: $1" >&2; exit 1; }

dsql() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt sql -q "$1")
}

dsql_csv() {
  [ -d "$SURFACE_DB/.dolt" ] || die "database not initialised — run 'data init'"
  (cd "$SURFACE_DB" && dolt sql -r csv -q "$1")
}

cmd_bal() {
  local filter="${1:-}"
  if [ -n "$filter" ]; then
    dsql "
      SELECT p.account_path, SUM(p.amount) AS balance, p.currency
      FROM postings p
      JOIN accounts a ON a.path = p.account_path
      WHERE p.account_path LIKE '%${filter}%'
      GROUP BY p.account_path, p.currency
      ORDER BY p.account_path;
    "
  else
    dsql "
      SELECT account_type, account_path, balance, currency
      FROM account_balances
      ORDER BY account_type, account_path;
    "
  fi
}

cmd_is() {
  local where_period=""
  if [ "${1:-}" = "-p" ] && [ -n "${2:-}" ]; then
    local month_year="$2"
    where_period="AND t.txn_date >= DATE_FORMAT(STR_TO_DATE('01 ${month_year}', '%d %b %Y'), '%Y-%m-01')
      AND t.txn_date < DATE_ADD(DATE_FORMAT(STR_TO_DATE('01 ${month_year}', '%d %b %Y'), '%Y-%m-01'), INTERVAL 1 MONTH)"
  fi

  dsql "
    SELECT
      CASE WHEN a.account_type = 'revenue' THEN 'Revenue' ELSE 'Expenses' END AS section,
      p.account_path,
      SUM(CASE WHEN a.account_type = 'revenue' THEN -p.amount ELSE p.amount END) AS amount,
      p.currency
    FROM postings p
    JOIN transactions t ON t.id = p.txn_id
    JOIN accounts a ON a.path = p.account_path
    WHERE a.account_type IN ('revenue', 'expenses')
    ${where_period}
    GROUP BY section, p.account_path, p.currency
    ORDER BY section DESC, p.account_path;
  "
}

cmd_bs() {
  dsql "
    SELECT
      a.account_type AS type,
      p.account_path,
      SUM(p.amount) AS balance,
      p.currency
    FROM postings p
    JOIN accounts a ON a.path = p.account_path
    WHERE a.account_type IN ('assets', 'liabilities', 'equity')
    GROUP BY a.account_type, p.account_path, p.currency
    ORDER BY a.account_type, p.account_path;
  "
}

cmd_reg() {
  local acct="${1:-}"
  [ -z "$acct" ] && die "usage: accounts reg <account>"
  dsql "
    SELECT t.txn_date AS date, t.payee, p.amount, p.currency
    FROM postings p
    JOIN transactions t ON t.id = p.txn_id
    WHERE p.account_path LIKE '%${acct}%'
    ORDER BY t.txn_date, t.id;
  "
}

cmd_stats() {
  dsql "
    SELECT
      (SELECT COUNT(*) FROM accounts) AS account_count,
      (SELECT COUNT(*) FROM transactions) AS txn_count,
      (SELECT MIN(txn_date) FROM transactions) AS first_txn,
      (SELECT MAX(txn_date) FROM transactions) AS last_txn;
  "
}

cmd_check() {
  local errors=0

  # Check all postings reference valid accounts
  local orphans
  orphans=$(dsql_csv "
    SELECT DISTINCT p.account_path
    FROM postings p
    LEFT JOIN accounts a ON a.path = p.account_path
    WHERE a.path IS NULL;
  " | tail -n +2)

  if [ -n "$orphans" ]; then
    echo "error: postings reference undeclared accounts:"
    echo "$orphans"
    errors=$((errors + 1))
  fi

  # Check all transactions balance to zero
  local unbalanced
  unbalanced=$(dsql_csv "
    SELECT txn_id, SUM(amount) AS net
    FROM postings
    GROUP BY txn_id
    HAVING ABS(net) > 0.005;
  " | tail -n +2)

  if [ -n "$unbalanced" ]; then
    echo "error: unbalanced transactions:"
    echo "$unbalanced"
    errors=$((errors + 1))
  fi

  if (( errors > 0 )); then
    echo ""
    echo "$errors error(s) found"
    exit 1
  fi

  echo "OK — $(dsql_csv "SELECT COUNT(*) FROM accounts;" | tail -1) accounts, $(dsql_csv "SELECT COUNT(*) FROM transactions;" | tail -1) transactions"
}

cmd_list() {
  dsql "SELECT path, account_type FROM accounts ORDER BY account_type, path;"
}

cmd_help() {
  echo "accounts — double-entry bookkeeping (dolt)"
  echo ""
  echo "Usage: accounts <command> [args]"
  echo ""
  echo "Commands:"
  echo "  bal [acct]           Current balances (optionally filter by account)"
  echo "  is [-p period]       Income statement"
  echo "  bs                   Balance sheet"
  echo "  reg <acct>           Transaction register for an account"
  echo "  stats                Account and transaction counts"
  echo "  check                Validate balanced entries and declared accounts"
  echo "  list                 List all declared accounts"
  echo "  help                 Show this help"
  echo ""
  echo "To add transactions, use: data sql"
  echo "  INSERT INTO transactions (txn_date, payee, description) VALUES ('2026-03-09', 'AWS', 'Monthly hosting');"
  echo "  INSERT INTO postings (txn_id, account_path, amount) VALUES (LAST_INSERT_ID(), 'expenses:infra:hosting', 45.00);"
  echo "  INSERT INTO postings (txn_id, account_path, amount) VALUES (LAST_INSERT_ID(), 'assets:bank:tide', -45.00);"
}

case "${1:-help}" in
  bal)    shift; cmd_bal "${1:-}" ;;
  is)     shift; cmd_is "$@" ;;
  bs)     cmd_bs ;;
  reg)    shift; cmd_reg "${1:-}" ;;
  stats)  cmd_stats ;;
  check)  cmd_check ;;
  list)   cmd_list ;;
  help|*) cmd_help ;;
esac
