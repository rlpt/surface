#!/usr/bin/env python3
"""officers — company officers register (directors, secretary, PSC)."""

import os
import subprocess
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
    data = datalib.load("officers")
    officers = data.get("officers", [])
    current = [o for o in officers if not o.get("resigned_date")]
    rows = [
        {
            "id": o["id"],
            "name": o["person_name"],
            "role": o["role"],
            "appointed": o.get("appointed_date", ""),
        }
        for o in sorted(current, key=lambda x: x.get("appointed_date", ""))
    ]
    datalib.print_table(rows, ["id", "name", "role", "appointed"])


def cmd_history():
    data = datalib.load("officers")
    officers = data.get("officers", [])
    rows = [
        {
            "id": o["id"],
            "name": o["person_name"],
            "role": o["role"],
            "appointed": o.get("appointed_date", ""),
            "resigned": o.get("resigned_date", ""),
            "status": "resigned" if o.get("resigned_date") else "active",
        }
        for o in sorted(officers, key=lambda x: x.get("appointed_date", ""))
    ]
    datalib.print_table(rows, ["id", "name", "role", "appointed", "resigned", "status"])


def cmd_check():
    data = datalib.load("officers")
    errors = datalib.lint("officers", data)
    if errors:
        print("officer data errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        sys.exit(1)
    print("OK")


# --- Write commands ---


def cmd_appoint(args):
    if len(args) < 3:
        die('usage: officers appoint <id> "Name" <role>')
    oid, name, role = args[0], args[1], args[2]
    if role not in ("director", "secretary", "psc"):
        die(f"invalid role: {role} (must be director, secretary, or psc)")

    data = datalib.load("officers")
    existing = {o["id"] for o in data.get("officers", [])}
    if oid in existing:
        die(f"officer '{oid}' already exists")

    data.setdefault("officers", []).append({
        "id": oid,
        "person_name": name,
        "role": role,
        "appointed_date": date.today().isoformat(),
    })
    datalib.save("officers", data)
    datalib.git_commit(f"officers: appoint {name} as {role}")
    print(f"Appointed {name} as {role}")


def cmd_resign(args):
    if len(args) < 1:
        die("usage: officers resign <id>")
    oid = args[0]

    data = datalib.load("officers")
    found = False
    for o in data.get("officers", []):
        if o["id"] == oid:
            if o.get("resigned_date"):
                die(f"officer '{oid}' already resigned")
            o["resigned_date"] = date.today().isoformat()
            found = True
            break
    if not found:
        die(f"officer '{oid}' not found")

    datalib.save("officers", data)
    datalib.git_commit(f"officers: {oid} resigned")
    print(f"Recorded resignation for {oid}")


# --- PDF ---


def generate_pdf(output_file, markdown):
    datalib.generate_branded_pdf(output_file, markdown)


def cmd_pdf_register():
    data = datalib.load("officers")
    officers = data.get("officers", [])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "officers-register.pdf")

    lines = [f"# Formabi Ltd — Register of Directors and Secretary\n", f"Generated: {today}\n"]

    current = [o for o in officers if not o.get("resigned_date")]
    if current:
        lines.append("## Current Officers\n")
        lines.append("| Name | Role | Appointed |")
        lines.append("|------|------|-----------|")
        for o in sorted(current, key=lambda x: x.get("appointed_date", "")):
            lines.append(f"| {o['person_name']} | {o['role']} | {o.get('appointed_date', '')} |")
        lines.append("")

    former = [o for o in officers if o.get("resigned_date")]
    if former:
        lines.append("## Former Officers\n")
        lines.append("| Name | Role | Appointed | Resigned |")
        lines.append("|------|------|-----------|----------|")
        for o in sorted(former, key=lambda x: x.get("resigned_date", "")):
            lines.append(f"| {o['person_name']} | {o['role']} | {o.get('appointed_date', '')} | {o.get('resigned_date', '')} |")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "register":
            cmd_pdf_register()
        case _:
            print("Usage: officers pdf <register>")


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/officers/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


# --- Routing ---


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "list":
            cmd_list()
        case "history":
            cmd_history()
        case "check":
            cmd_check()
        case "appoint":
            cmd_appoint(args[1:])
        case "resign":
            cmd_resign(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
