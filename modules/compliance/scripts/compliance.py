#!/usr/bin/env python3
"""compliance — statutory compliance calendar and deadline tracking."""

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


# --- Colour helpers ---

RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RESET = "\033[0m"


def colour_status(status, days_left):
    if status == "overdue" or days_left < 0:
        return f"{RED}{status}{RESET}"
    elif days_left <= 30:
        return f"{YELLOW}{status}{RESET}"
    else:
        return f"{GREEN}{status}{RESET}"


# --- Read commands ---


def cmd_upcoming():
    data = datalib.load("compliance")
    upcoming = datalib.compliance_upcoming(data)
    if not upcoming:
        print("No upcoming deadlines within 90 days.")
        return

    print(f"{'Title':<40} {'Due Date':<12} {'Category':<18} {'Status':<12} {'Days'}")
    print("-" * 90)
    for d in upcoming:
        status = colour_status(d["status"], d["days_left"])
        print(f"{d['title']:<40} {d['due_date']:<12} {d['category']:<18} {status:<23} {d['days_left']}")


def cmd_list(args):
    data = datalib.load("compliance")
    deadlines = data.get("deadlines", [])
    category = args[0] if args else None
    if category:
        deadlines = [d for d in deadlines if d["category"] == category]

    rows = [
        {
            "id": d["id"],
            "title": d["title"],
            "due_date": d["due_date"],
            "frequency": d["frequency"],
            "category": d["category"],
            "status": d.get("status", "upcoming"),
        }
        for d in sorted(deadlines, key=lambda x: x["due_date"])
    ]
    datalib.print_table(rows, ["id", "title", "due_date", "frequency", "category", "status"])


def cmd_check():
    data = datalib.load("compliance")
    errors = datalib.lint("compliance", data)
    today = date.today()
    overdue = []
    for d in data.get("deadlines", []):
        if d.get("status") == "filed":
            continue
        try:
            due = date.fromisoformat(str(d["due_date"]))
        except (ValueError, TypeError):
            continue
        if due < today:
            overdue.append(d)

    if errors:
        print("compliance data errors:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
    if overdue:
        print(f"{RED}OVERDUE items:{RESET}", file=sys.stderr)
        for d in overdue:
            print(f"  {d['id']}: {d['title']} (due {d['due_date']})", file=sys.stderr)
    if errors or overdue:
        sys.exit(1)
    print("OK — no overdue items")


# --- Write commands ---


def cmd_add(args):
    if len(args) < 5:
        die('usage: compliance add <id> "title" <due-date> <frequency> <category>')
    cid, title, due_date, frequency, category = args[0], args[1], args[2], args[3], args[4]

    if frequency not in ("annual", "quarterly", "monthly", "one-off"):
        die(f"invalid frequency: {frequency}")
    if category not in ("companies-house", "hmrc", "other"):
        die(f"invalid category: {category}")

    data = datalib.load("compliance")
    existing = {d["id"] for d in data.get("deadlines", [])}
    if cid in existing:
        die(f"deadline '{cid}' already exists")

    data.setdefault("deadlines", []).append({
        "id": cid,
        "title": title,
        "due_date": due_date,
        "frequency": frequency,
        "category": category,
        "status": "upcoming",
    })
    datalib.save("compliance", data)
    datalib.git_commit(f"compliance: add {title} due {due_date}")
    print(f"Added deadline: {title} (due {due_date})")


def cmd_file(args):
    if len(args) < 1:
        die("usage: compliance file <id>")
    cid = args[0]

    data = datalib.load("compliance")
    found = False
    for d in data.get("deadlines", []):
        if d["id"] == cid:
            d["status"] = "filed"
            d["filed_date"] = date.today().isoformat()
            found = True
            break
    if not found:
        die(f"deadline '{cid}' not found")

    datalib.save("compliance", data)
    datalib.git_commit(f"compliance: filed {cid}")
    print(f"Marked {cid} as filed")


# --- PDF ---


def generate_pdf(output_file, markdown):
    datalib.generate_branded_pdf(output_file, markdown)


def cmd_pdf_calendar():
    data = datalib.load("compliance")
    deadlines = sorted(data.get("deadlines", []), key=lambda x: x["due_date"])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "compliance-calendar.pdf")

    lines = [f"# Formabi Ltd — Compliance Calendar\n", f"Generated: {today}\n"]
    lines.append("| Deadline | Due Date | Frequency | Category | Status |")
    lines.append("|----------|----------|-----------|----------|--------|")
    for d in deadlines:
        lines.append(
            f"| {d['title']} | {d['due_date']} | {d['frequency']} "
            f"| {d['category']} | {d.get('status', 'upcoming')} |"
        )

    generate_pdf(output, "\n".join(lines))


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "calendar":
            cmd_pdf_calendar()
        case _:
            print("Usage: compliance pdf <calendar>")


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/compliance/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


# --- Routing ---


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "upcoming":
            cmd_upcoming()
        case "list":
            cmd_list(args[1:])
        case "check":
            cmd_check()
        case "add":
            cmd_add(args[1:])
        case "file":
            cmd_file(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
