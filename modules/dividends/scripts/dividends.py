#!/usr/bin/env python3
"""dividends — dividend declarations and payments."""

import os
import sys
from datetime import date

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def _next_id(dividends):
    """Generate next dividend ID (div-NNN)."""
    nums = []
    for d in dividends:
        parts = d["id"].split("-")
        if len(parts) == 2 and parts[1].isdigit():
            nums.append(int(parts[1]))
    n = max(nums) + 1 if nums else 1
    return f"div-{n:03d}"


# --- Read commands ---


def cmd_list():
    data = datalib.load("dividends")
    divs = data.get("dividends", [])
    rows = [
        {
            "id": d["id"],
            "class": d.get("share_class", ""),
            "per_share": d.get("amount_per_share", ""),
            "declared": d.get("declaration_date", ""),
            "paid": d.get("payment_date", ""),
            "status": d.get("status", ""),
        }
        for d in sorted(divs, key=lambda x: x.get("declaration_date", ""))
    ]
    datalib.print_table(rows, ["id", "class", "per_share", "declared", "paid", "status"])


def cmd_show(args):
    if len(args) < 1:
        die("usage: dividends show <id>")
    did = args[0]
    data = datalib.load("dividends")
    for d in data.get("dividends", []):
        if d["id"] == did:
            print(f"  ID:               {d['id']}")
            print(f"  Declaration date: {d.get('declaration_date', '')}")
            print(f"  Payment date:     {d.get('payment_date', '')}")
            print(f"  Share class:      {d.get('share_class', '')}")
            print(f"  Amount per share: {d.get('currency', 'GBP')} {d.get('amount_per_share', '')}")
            print(f"  Tax voucher ref:  {d.get('tax_voucher_ref', '')}")
            print(f"  Status:           {d.get('status', '')}")
            print(f"  Resolution:       {d.get('resolution_id', '')}")
            return
    die(f"dividend '{did}' not found")


def cmd_check():
    data = datalib.load("dividends")
    errors = datalib.lint("dividends", data)
    if errors:
        print("dividend data errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    print("OK")


# --- Write commands ---


def cmd_declare(args):
    if len(args) < 2:
        die("usage: dividends declare <share_class> <amount_per_share> [resolution_id]")
    share_class = args[0]
    try:
        amount = float(args[1])
    except ValueError:
        die(f"amount must be a number, got: {args[1]}")
    resolution_id = args[2] if len(args) > 2 else ""

    data = datalib.load("dividends")
    divs = data.get("dividends", [])
    did = _next_id(divs)
    today = date.today().isoformat()

    divs.append({
        "id": did,
        "declaration_date": today,
        "payment_date": "",
        "share_class": share_class,
        "amount_per_share": amount,
        "currency": "GBP",
        "tax_voucher_ref": "",
        "status": "declared",
        "resolution_id": resolution_id,
    })
    data["dividends"] = divs
    datalib.save("dividends", data)
    datalib.git_commit(f"dividends: declare {did} ({share_class}, GBP {amount}/share)")
    print(f"Declared dividend {did}")


def cmd_pay(args):
    if len(args) < 1:
        die("usage: dividends pay <id>")
    did = args[0]

    data = datalib.load("dividends")
    found = False
    for d in data.get("dividends", []):
        if d["id"] == did:
            if d.get("status") == "paid":
                die(f"dividend '{did}' already paid")
            d["status"] = "paid"
            d["payment_date"] = date.today().isoformat()
            found = True
            break
    if not found:
        die(f"dividend '{did}' not found")

    datalib.save("dividends", data)
    datalib.git_commit(f"dividends: pay {did}")
    print(f"Dividend {did} marked as paid")


# --- PDF ---


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "register":
            cmd_pdf_register()
        case "voucher":
            cmd_pdf_voucher(args[1:])
        case _:
            print("Usage: dividends pdf <register|voucher <id>>")


def cmd_pdf_register():
    data = datalib.load("dividends")
    divs = data.get("dividends", [])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "dividend-register.pdf")

    lines = [
        f"# Dividend Register\n",
        f"Generated: {today}\n",
        "---\n",
        "| ID | Class | Per Share | Declared | Paid | Status |",
        "|----|-------|----------|----------|------|--------|",
    ]
    for d in sorted(divs, key=lambda x: x.get("declaration_date", "")):
        lines.append(
            f"| {d['id']} | {d.get('share_class', '')} | "
            f"{d.get('currency', 'GBP')} {d.get('amount_per_share', '')} | "
            f"{d.get('declaration_date', '')} | {d.get('payment_date', '')} | "
            f"{d.get('status', '')} |"
        )

    datalib.generate_branded_pdf(output, "\n".join(lines))


def cmd_pdf_voucher(args):
    if len(args) < 1:
        die("usage: dividends pdf voucher <id>")
    did = args[0]

    data = datalib.load("dividends")
    div = None
    for d in data.get("dividends", []):
        if d["id"] == did:
            div = d
            break
    if not div:
        die(f"dividend '{did}' not found")

    # Load share data to compute per-holder amounts
    share_data = datalib.load("shares")
    h = datalib.holdings(share_data)
    holders_map = {r["id"]: r["display_name"] for r in share_data.get("holders", [])}

    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"dividend-voucher-{did}.pdf")
    amount = div.get("amount_per_share", 0)
    cls = div.get("share_class", "")

    lines = [
        f"# Dividend Tax Voucher — {did}\n",
        f"Generated: {today}\n",
        "---\n",
        f"**Declaration date:** {div.get('declaration_date', '')}  ",
        f"**Payment date:** {div.get('payment_date', '')}  ",
        f"**Share class:** {cls}  ",
        f"**Amount per share:** {div.get('currency', 'GBP')} {amount}  ",
        f"**Voucher ref:** {div.get('tax_voucher_ref', '')}  \n",
        "## Holder Payments\n",
        "| Holder | Shares | Dividend |",
        "|--------|--------|----------|",
    ]
    for holding in h:
        if holding["share_class"] == cls:
            hid = holding["holder_id"]
            name = holders_map.get(hid, hid)
            shares = holding["shares_held"]
            total = round(shares * amount, 2)
            lines.append(f"| {name} | {shares} | {div.get('currency', 'GBP')} {total} |")

    datalib.generate_branded_pdf(output, "\n".join(lines))


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/dividends/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


# --- Routing ---


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "list":
            cmd_list()
        case "show":
            cmd_show(args[1:])
        case "check":
            cmd_check()
        case "declare":
            cmd_declare(args[1:])
        case "pay":
            cmd_pay(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
