#!/usr/bin/env python3
"""company — company details register."""

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


def cmd_show():
    data = datalib.load("company")
    co = data.get("company", {})
    if not co:
        die("no company data found")

    print(f"  Name:              {co.get('name', '')}")
    print(f"  Company number:    {co.get('company_number', '')}")
    print(f"  Jurisdiction:      {co.get('jurisdiction', '')}")
    print(f"  Type:              {co.get('company_type', '')}")
    print(f"  Incorporated:      {co.get('incorporation_date', '')}")

    addr = co.get("registered_address", {})
    if addr:
        parts = [addr.get("line_1", ""), addr.get("line_2", "")]
        parts = [p for p in parts if p]
        parts.append(addr.get("city", ""))
        parts.append(addr.get("postcode", ""))
        parts.append(addr.get("country", ""))
        print(f"  Registered addr:   {', '.join(p for p in parts if p)}")

    sic = co.get("sic_codes", [])
    if sic:
        print(f"  SIC codes:         {', '.join(sic)}")

    ard = co.get("accounting_reference_date", "")
    if ard:
        print(f"  Accounting ref:    {ard}")

    articles = co.get("articles", "")
    if articles:
        print(f"  Articles:          {articles}")


def cmd_check():
    data = datalib.load("company")
    errors = datalib.lint("company", data)
    if errors:
        print("company data errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    print("OK")


# --- Write commands ---


def cmd_set(args):
    if len(args) < 2:
        die("usage: company set <field> <value>")
    field, value = args[0], " ".join(args[1:])

    data = datalib.load("company")
    co = data.get("company", {})

    valid_fields = [
        "name", "company_number", "jurisdiction", "company_type",
        "articles", "accounting_reference_date",
    ]
    if field not in valid_fields:
        die(f"unknown field: {field} (valid: {', '.join(valid_fields)})")

    co[field] = value
    data["company"] = co
    datalib.save("company", data)
    datalib.git_commit(f"company: set {field} to {value}")
    print(f"Set {field} = {value}")


def cmd_set_address(args):
    if len(args) < 3:
        die('usage: company set-address <line_1> <city> <postcode> [country] [line_2]')
    data = datalib.load("company")
    co = data.get("company", {})

    addr = {
        "line_1": args[0],
        "city": args[1],
        "postcode": args[2],
        "country": args[3] if len(args) > 3 else "GB",
    }
    if len(args) > 4:
        addr["line_2"] = args[4]

    co["registered_address"] = addr
    data["company"] = co
    datalib.save("company", data)
    datalib.git_commit(f"company: update registered address")
    print(f"Updated registered address")


def cmd_add_sic(args):
    if len(args) < 1:
        die("usage: company add-sic <code>")
    code = args[0]
    data = datalib.load("company")
    co = data.get("company", {})
    sic = co.get("sic_codes", [])
    if code in sic:
        die(f"SIC code {code} already present")
    sic.append(code)
    co["sic_codes"] = sic
    data["company"] = co
    datalib.save("company", data)
    datalib.git_commit(f"company: add SIC code {code}")
    print(f"Added SIC code {code}")


def cmd_remove_sic(args):
    if len(args) < 1:
        die("usage: company remove-sic <code>")
    code = args[0]
    data = datalib.load("company")
    co = data.get("company", {})
    sic = co.get("sic_codes", [])
    if code not in sic:
        die(f"SIC code {code} not found")
    sic.remove(code)
    co["sic_codes"] = sic
    data["company"] = co
    datalib.save("company", data)
    datalib.git_commit(f"company: remove SIC code {code}")
    print(f"Removed SIC code {code}")


# --- PDF ---


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "summary":
            cmd_pdf_summary()
        case _:
            print("Usage: company pdf summary")


def cmd_pdf_summary():
    data = datalib.load("company")
    co = data.get("company", {})
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "company-summary.pdf")

    addr = co.get("registered_address", {})
    addr_parts = [addr.get("line_1", ""), addr.get("line_2", "")]
    addr_parts = [p for p in addr_parts if p]
    addr_parts.extend([addr.get("city", ""), addr.get("postcode", ""), addr.get("country", "")])
    addr_str = ", ".join(p for p in addr_parts if p)

    sic = co.get("sic_codes", [])

    lines = [
        f"# {co.get('name', 'Company')} — Summary\n",
        f"Generated: {today}\n",
        "---\n",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Company number | {co.get('company_number', '')} |",
        f"| Jurisdiction | {co.get('jurisdiction', '')} |",
        f"| Type | {co.get('company_type', '')} |",
        f"| Incorporated | {co.get('incorporation_date', '')} |",
        f"| Registered address | {addr_str} |",
        f"| SIC codes | {', '.join(sic)} |",
        f"| Accounting reference date | {co.get('accounting_reference_date', '')} |",
        f"| Articles | {co.get('articles', '')} |",
    ]

    datalib.generate_branded_pdf(output, "\n".join(lines))


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/company/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


# --- Routing ---


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "show":
            cmd_show()
        case "check":
            cmd_check()
        case "set":
            cmd_set(args[1:])
        case "set-address":
            cmd_set_address(args[1:])
        case "add-sic":
            cmd_add_sic(args[1:])
        case "remove-sic":
            cmd_remove_sic(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
