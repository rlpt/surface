#!/usr/bin/env python3
"""accounts — double-entry bookkeeping (dolt)"""

import os
import subprocess
import sys

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
SURFACE_DB = os.environ.get("SURFACE_DB", os.path.join(SURFACE_ROOT, ".surface-db"))


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_db():
    if not os.path.isdir(os.path.join(SURFACE_DB, ".dolt")):
        die("database not initialised — run 'data init'")


def dsql(query):
    check_db()
    sys.stdout.flush()
    subprocess.run(["dolt", "sql", "-q", query], cwd=SURFACE_DB, check=True)


def dsql_csv(query):
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = r.stdout.strip().split("\n")
    return lines[1:] if len(lines) > 1 else []


def dsql_val(query):
    rows = dsql_csv(query)
    return rows[0] if rows else ""


# --- Commands ---


def cmd_bal(filter_=""):
    if filter_:
        esc = filter_.replace("'", "''")
        dsql(
            "SELECT p.account_path, SUM(p.amount) AS balance, p.currency "
            "FROM postings p "
            "JOIN accounts a ON a.path = p.account_path "
            f"WHERE p.account_path LIKE '%{esc}%' "
            "GROUP BY p.account_path, p.currency "
            "ORDER BY p.account_path;"
        )
    else:
        dsql(
            "SELECT account_type, account_path, balance, currency "
            "FROM account_balances "
            "ORDER BY account_type, account_path;"
        )


def cmd_is(args):
    where_period = ""
    if len(args) >= 2 and args[0] == "-p":
        month_year = args[1]
        where_period = (
            f"AND t.txn_date >= DATE_FORMAT(STR_TO_DATE('01 {month_year}', '%d %b %Y'), '%Y-%m-01') "
            f"AND t.txn_date < DATE_ADD(DATE_FORMAT(STR_TO_DATE('01 {month_year}', '%d %b %Y'), '%Y-%m-01'), INTERVAL 1 MONTH)"
        )

    dsql(
        "SELECT "
        "CASE WHEN a.account_type = 'revenue' THEN 'Revenue' ELSE 'Expenses' END AS section, "
        "p.account_path, "
        "SUM(CASE WHEN a.account_type = 'revenue' THEN -p.amount ELSE p.amount END) AS amount, "
        "p.currency "
        "FROM postings p "
        "JOIN transactions t ON t.id = p.txn_id "
        "JOIN accounts a ON a.path = p.account_path "
        "WHERE a.account_type IN ('revenue', 'expenses') "
        f"{where_period} "
        "GROUP BY section, p.account_path, p.currency "
        "ORDER BY section DESC, p.account_path;"
    )


def cmd_bs():
    dsql(
        "SELECT a.account_type AS type, p.account_path, "
        "SUM(p.amount) AS balance, p.currency "
        "FROM postings p "
        "JOIN accounts a ON a.path = p.account_path "
        "WHERE a.account_type IN ('assets', 'liabilities', 'equity') "
        "GROUP BY a.account_type, p.account_path, p.currency "
        "ORDER BY a.account_type, p.account_path;"
    )


def cmd_reg(acct):
    if not acct:
        die("usage: accounts reg <account>")
    esc = acct.replace("'", "''")
    dsql(
        "SELECT t.txn_date AS date, t.payee, p.amount, p.currency "
        "FROM postings p "
        "JOIN transactions t ON t.id = p.txn_id "
        f"WHERE p.account_path LIKE '%{esc}%' "
        "ORDER BY t.txn_date, t.id;"
    )


def cmd_stats():
    dsql(
        "SELECT "
        "(SELECT COUNT(*) FROM accounts) AS account_count, "
        "(SELECT COUNT(*) FROM transactions) AS txn_count, "
        "(SELECT MIN(txn_date) FROM transactions) AS first_txn, "
        "(SELECT MAX(txn_date) FROM transactions) AS last_txn;"
    )


def cmd_check():
    errors = 0

    orphans = dsql_csv(
        "SELECT DISTINCT p.account_path "
        "FROM postings p "
        "LEFT JOIN accounts a ON a.path = p.account_path "
        "WHERE a.path IS NULL;"
    )
    if orphans:
        print("error: postings reference undeclared accounts:")
        for o in orphans:
            print(f"  {o}")
        errors += 1

    unbalanced = dsql_csv(
        "SELECT txn_id, SUM(amount) AS net "
        "FROM postings GROUP BY txn_id HAVING ABS(net) > 0.005;"
    )
    if unbalanced:
        print("error: unbalanced transactions:")
        for u in unbalanced:
            print(f"  {u}")
        errors += 1

    if errors:
        print(f"\n{errors} error(s) found")
        sys.exit(1)

    acct_count = dsql_val("SELECT COUNT(*) FROM accounts;")
    txn_count = dsql_val("SELECT COUNT(*) FROM transactions;")
    print(f"OK — {acct_count} accounts, {txn_count} transactions")


def cmd_list():
    dsql("SELECT path, account_type FROM accounts ORDER BY account_type, path;")


def cmd_help():
    print("accounts — double-entry bookkeeping (dolt)")
    print()
    print("Usage: accounts <command> [args]")
    print()
    print("Commands:")
    print("  bal [acct]           Current balances (optionally filter by account)")
    print("  is [-p period]       Income statement")
    print("  bs                   Balance sheet")
    print("  reg <acct>           Transaction register for an account")
    print("  stats                Account and transaction counts")
    print("  check                Validate balanced entries and declared accounts")
    print("  list                 List all declared accounts")
    print("  help                 Show this help")
    print()
    print("To add transactions, use: data sql")
    print("  INSERT INTO transactions (txn_date, payee, description) VALUES ('2026-03-09', 'AWS', 'Monthly hosting');")
    print("  INSERT INTO postings (txn_id, account_path, amount) VALUES (LAST_INSERT_ID(), 'expenses:infra:hosting', 45.00);")
    print("  INSERT INTO postings (txn_id, account_path, amount) VALUES (LAST_INSERT_ID(), 'assets:bank:tide', -45.00);")


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "bal":
            cmd_bal(args[1] if len(args) > 1 else "")
        case "is":
            cmd_is(args[1:])
        case "bs":
            cmd_bs()
        case "reg":
            cmd_reg(args[1] if len(args) > 1 else "")
        case "stats":
            cmd_stats()
        case "check":
            cmd_check()
        case "list":
            cmd_list()
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
