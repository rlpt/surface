#!/usr/bin/env python3
"""charges — register of charges (secured loans and debentures)."""

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


# --- Read commands ---


def cmd_list():
    data = datalib.load("charges")
    charges = data.get("charges", [])
    rows = [
        {
            "id": c["id"],
            "chargee": c.get("chargee", ""),
            "amount": f"{c.get('currency', 'GBP')} {c.get('amount', '')}",
            "created": c.get("created_date", ""),
            "status": c.get("status", ""),
        }
        for c in sorted(charges, key=lambda x: x.get("created_date", ""))
    ]
    datalib.print_table(rows, ["id", "chargee", "amount", "created", "status"])


def cmd_show(args):
    if len(args) < 1:
        die("usage: charges show <id>")
    cid = args[0]
    data = datalib.load("charges")
    for c in data.get("charges", []):
        if c["id"] == cid:
            print(f"  ID:             {c['id']}")
            print(f"  Charge code:    {c.get('charge_code', '')}")
            print(f"  Created:        {c.get('created_date', '')}")
            print(f"  Description:    {c.get('description', '')}")
            print(f"  Chargee:        {c.get('chargee', '')}")
            print(f"  Amount:         {c.get('currency', 'GBP')} {c.get('amount', '')}")
            print(f"  Status:         {c.get('status', '')}")
            print(f"  Delivered:      {c.get('delivered_date', '')}")
            print(f"  Satisfied:      {c.get('satisfied_date', '')}")
            return
    die(f"charge '{cid}' not found")


def cmd_check():
    data = datalib.load("charges")
    errors = datalib.lint("charges", data)
    if errors:
        print("charge data errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    print("OK")


# --- Write commands ---


def cmd_register(args):
    if len(args) < 4:
        die('usage: charges register <id> "description" <chargee> <amount>')
    cid, desc, chargee, amount = args[0], args[1], args[2], args[3]
    try:
        amount = int(amount)
    except ValueError:
        die(f"amount must be an integer, got: {amount}")

    data = datalib.load("charges")
    existing = {c["id"] for c in data.get("charges", [])}
    if cid in existing:
        die(f"charge '{cid}' already exists")

    today = date.today().isoformat()
    data.setdefault("charges", []).append({
        "id": cid,
        "charge_code": "",
        "created_date": today,
        "description": desc,
        "chargee": chargee,
        "amount": amount,
        "currency": "GBP",
        "status": "outstanding",
        "delivered_date": "",
        "satisfied_date": "",
    })
    datalib.save("charges", data)
    datalib.git_commit(f"charges: register {cid} ({chargee}, GBP {amount})")
    print(f"Registered charge {cid}")


def cmd_satisfy(args):
    if len(args) < 1:
        die("usage: charges satisfy <id>")
    cid = args[0]

    data = datalib.load("charges")
    found = False
    for c in data.get("charges", []):
        if c["id"] == cid:
            if c.get("status") == "satisfied":
                die(f"charge '{cid}' already satisfied")
            c["status"] = "satisfied"
            c["satisfied_date"] = date.today().isoformat()
            found = True
            break
    if not found:
        die(f"charge '{cid}' not found")

    datalib.save("charges", data)
    datalib.git_commit(f"charges: satisfy {cid}")
    print(f"Charge {cid} marked as satisfied")


# --- PDF ---


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "register":
            cmd_pdf_register()
        case _:
            print("Usage: charges pdf register")


def cmd_pdf_register():
    data = datalib.load("charges")
    charges = data.get("charges", [])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "charges-register.pdf")

    lines = [
        f"# Register of Charges\n",
        f"Generated: {today}\n",
        "---\n",
    ]

    outstanding = [c for c in charges if c.get("status") == "outstanding"]
    if outstanding:
        lines.append("## Outstanding Charges\n")
        lines.append("| ID | Chargee | Amount | Created | Description |")
        lines.append("|----|---------|--------|---------|-------------|")
        for c in sorted(outstanding, key=lambda x: x.get("created_date", "")):
            lines.append(
                f"| {c['id']} | {c.get('chargee', '')} | "
                f"{c.get('currency', 'GBP')} {c.get('amount', '')} | "
                f"{c.get('created_date', '')} | {c.get('description', '')} |"
            )
        lines.append("")

    satisfied = [c for c in charges if c.get("status") == "satisfied"]
    if satisfied:
        lines.append("## Satisfied Charges\n")
        lines.append("| ID | Chargee | Amount | Created | Satisfied |")
        lines.append("|----|---------|--------|---------|-----------|")
        for c in sorted(satisfied, key=lambda x: x.get("satisfied_date", "")):
            lines.append(
                f"| {c['id']} | {c.get('chargee', '')} | "
                f"{c.get('currency', 'GBP')} {c.get('amount', '')} | "
                f"{c.get('created_date', '')} | {c.get('satisfied_date', '')} |"
            )

    datalib.generate_branded_pdf(output, "\n".join(lines))


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/charges/scripts/help.txt")
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
        case "register":
            cmd_register(args[1:])
        case "satisfy":
            cmd_satisfy(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
