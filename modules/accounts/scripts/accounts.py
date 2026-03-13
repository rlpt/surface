#!/usr/bin/env python3
"""accounts — double-entry bookkeeping (toml)"""

import os
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib


# --- Commands ---


def cmd_bal(filter_=""):
    bals = datalib.account_balances()
    if filter_:
        bals = [b for b in bals if filter_ in b["account_path"]]
    datalib.print_table(bals)


def cmd_is(args):
    data = datalib.load("accounts")
    accounts = {a["path"]: a["account_type"] for a in data.get("accounts", [])}
    transactions = {t["id"]: t for t in data.get("transactions", [])}
    postings = data.get("postings", [])

    # Optional period filter: -p "Mar 2026" or -p "2026-03"
    period_start = None
    period_end = None
    if len(args) >= 2 and args[0] == "-p":
        period_start, period_end = _parse_period(args[1])

    rows = []
    # Group by account_path and currency
    grouped = defaultdict(float)
    for p in postings:
        acct_type = accounts.get(p["account_path"])
        if acct_type not in ("revenue", "expenses"):
            continue
        if period_start is not None:
            txn = transactions.get(p["txn_id"])
            if txn:
                txn_date = str(txn["txn_date"])
                if txn_date < period_start or txn_date >= period_end:
                    continue
        currency = p.get("currency", "GBP")
        section = "Revenue" if acct_type == "revenue" else "Expenses"
        sign = -1 if acct_type == "revenue" else 1
        key = (section, p["account_path"], currency)
        grouped[key] += sign * p["amount"]

    for (section, path, currency), amount in sorted(grouped.items(), key=lambda x: (x[0][0] == "E", x[0][1])):
        rows.append({
            "section": section,
            "account_path": path,
            "amount": round(amount, 2),
            "currency": currency,
        })
    datalib.print_table(rows)


def cmd_bs():
    data = datalib.load("accounts")
    accounts = {a["path"]: a["account_type"] for a in data.get("accounts", [])}
    postings = data.get("postings", [])

    grouped = defaultdict(float)
    for p in postings:
        acct_type = accounts.get(p["account_path"])
        if acct_type not in ("assets", "liabilities", "equity"):
            continue
        currency = p.get("currency", "GBP")
        key = (acct_type, p["account_path"], currency)
        grouped[key] += p["amount"]

    rows = []
    for (typ, path, currency), balance in sorted(grouped.items()):
        rows.append({
            "type": typ,
            "account_path": path,
            "balance": round(balance, 2),
            "currency": currency,
        })
    datalib.print_table(rows)


def cmd_reg(acct):
    if not acct:
        datalib.die("usage: accounts reg <account>")
    data = datalib.load("accounts")
    transactions = {t["id"]: t for t in data.get("transactions", [])}
    postings = data.get("postings", [])

    rows = []
    for p in postings:
        if acct not in p["account_path"]:
            continue
        txn = transactions.get(p["txn_id"])
        if not txn:
            continue
        rows.append({
            "date": str(txn["txn_date"]),
            "payee": txn.get("payee", ""),
            "amount": p["amount"],
            "currency": p.get("currency", "GBP"),
        })
    rows.sort(key=lambda r: (r["date"], str(r["amount"])))
    datalib.print_table(rows)


def cmd_stats():
    data = datalib.load("accounts")
    accounts = data.get("accounts", [])
    transactions = data.get("transactions", [])
    acct_count = len(accounts)
    txn_count = len(transactions)
    if transactions:
        dates = sorted(str(t["txn_date"]) for t in transactions)
        first_txn = dates[0]
        last_txn = dates[-1]
    else:
        first_txn = ""
        last_txn = ""
    datalib.print_table([{
        "account_count": acct_count,
        "txn_count": txn_count,
        "first_txn": first_txn,
        "last_txn": last_txn,
    }])


def cmd_check():
    data = datalib.load("accounts")
    account_paths = {a["path"] for a in data.get("accounts", [])}
    postings = data.get("postings", [])
    transactions = data.get("transactions", [])
    errors = 0

    # Check orphan posting accounts
    orphans = sorted({p["account_path"] for p in postings if p["account_path"] not in account_paths})
    if orphans:
        print("error: postings reference undeclared accounts:")
        for o in orphans:
            print(f"  {o}")
        errors += 1

    # Check balanced transactions
    txn_totals = defaultdict(float)
    for p in postings:
        txn_totals[p["txn_id"]] += p["amount"]
    unbalanced = [(tid, total) for tid, total in sorted(txn_totals.items()) if abs(total) > 0.005]
    if unbalanced:
        print("error: unbalanced transactions:")
        for tid, net in unbalanced:
            print(f"  txn_id={tid}, net={round(net, 4)}")
        errors += 1

    if errors:
        print(f"\n{errors} error(s) found")
        sys.exit(1)

    print(f"OK — {len(account_paths)} accounts, {len(transactions)} transactions")


def cmd_list():
    data = datalib.load("accounts")
    accounts = data.get("accounts", [])
    rows = sorted(accounts, key=lambda a: (a["account_type"], a["path"]))
    datalib.print_table(rows, columns=["path", "account_type"])


def cmd_help():
    print("accounts — double-entry bookkeeping (toml)")
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
    print("To add transactions, edit data/accounts.toml directly.")
    print("Add a [[transactions]] entry and corresponding [[postings]] entries.")
    print("Postings must sum to zero per transaction (double-entry).")
    print("Then run: accounts check")


def _parse_period(s):
    """Parse a period string into (start_iso, end_iso) for YYYY-MM range.

    Accepts: "Mar 2026", "2026-03", "March 2026"
    Returns: ("2026-03-01", "2026-04-01") or similar.
    """
    import calendar
    s = s.strip()
    # Try YYYY-MM format
    if len(s) >= 7 and s[4] == "-":
        try:
            d = date.fromisoformat(s + "-01")
            year, month = d.year, d.month
        except ValueError:
            datalib.die(f"cannot parse period: {s}")
            return None, None  # unreachable
    else:
        # Try "Mon YYYY" or "Month YYYY"
        parts = s.split()
        if len(parts) != 2:
            datalib.die(f"cannot parse period: {s}")
            return None, None
        month_str, year_str = parts
        try:
            year = int(year_str)
        except ValueError:
            datalib.die(f"cannot parse period: {s}")
            return None, None
        # Try abbreviated and full month names
        month = None
        for i in range(1, 13):
            if calendar.month_abbr[i].lower() == month_str.lower():
                month = i
                break
            if calendar.month_name[i].lower() == month_str.lower():
                month = i
                break
        if month is None:
            datalib.die(f"cannot parse period: {s}")
            return None, None

    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start.isoformat(), end.isoformat()


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
