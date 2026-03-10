#!/usr/bin/env python3
"""shares — cap table management (dolt)"""

import csv
import io
import os
import subprocess
import sys
from datetime import date

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
SURFACE_DB = os.environ.get("SURFACE_DB", os.path.join(SURFACE_ROOT, ".surface-db"))
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")


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


def dsql_rows(query):
    """Return list of dicts from a CSV query."""
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
        check=True,
    )
    return list(csv.DictReader(io.StringIO(r.stdout)))


def dsql_val(query):
    rows = dsql_csv(query)
    return rows[0] if rows else ""


def dolt_commit(msg):
    subprocess.run(["dolt", "add", "."], cwd=SURFACE_DB, check=True)
    subprocess.run(["dolt", "commit", "-m", msg], cwd=SURFACE_DB, check=True)


# --- Read commands ---


def cmd_table():
    dsql(
        "SELECT ct.holder, ct.class, ct.held, "
        "CONCAT(ct.pct, '%') AS pct, ct.held AS vested "
        "FROM cap_table ct;"
    )
    total = dsql_val("SELECT COALESCE(SUM(shares_held), 0) FROM holdings;")
    print(f"\nTotal issued: {total}")


def cmd_export():
    check_db()
    subprocess.run(
        [
            "dolt", "sql", "-r", "csv", "-q",
            "SELECT ct.holder, ct.class AS share_class, ct.held AS shares_held, "
            "ct.pct AS percentage, ct.held AS vested, ct.held AS total_granted, "
            "'' AS notes FROM cap_table ct;",
        ],
        cwd=SURFACE_DB,
        check=True,
    )


def cmd_holders():
    dsql(
        "SELECT h.id, h.display_name AS name, "
        "COALESCE(SUM(ho.shares_held), 0) AS total "
        "FROM holders h "
        "LEFT JOIN holdings ho ON ho.holder_id = h.id "
        "GROUP BY h.id, h.display_name ORDER BY h.id;"
    )


def cmd_history(filter_=""):
    where = f"WHERE se.holder_id = '{filter_}'" if filter_ else ""
    dsql(
        "SELECT se.event_date AS date, se.event_type AS event, "
        "se.holder_id AS holder, se.share_class AS class, se.quantity AS qty "
        f"FROM share_events se {where} "
        "ORDER BY se.event_date, se.id;"
    )


def cmd_pools():
    dsql(
        "SELECT p.name AS pool, p.share_class AS class, p.budget, "
        "COALESCE(issued.total, 0) AS issued, "
        "p.budget - COALESCE(issued.total, 0) AS avail, "
        "COALESCE(members.list, '-') AS members "
        "FROM pools p "
        "LEFT JOIN ("
        "  SELECT pm.pool_name, SUM(COALESCE(ho.shares_held, 0)) AS total "
        "  FROM pool_members pm "
        "  LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id "
        "    AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name) "
        "  GROUP BY pm.pool_name"
        ") issued ON issued.pool_name = p.name "
        "LEFT JOIN ("
        "  SELECT pm.pool_name, "
        "    GROUP_CONCAT(CONCAT(h.display_name, ' (', COALESCE(ho.shares_held, 0), ')') SEPARATOR ', ') AS list "
        "  FROM pool_members pm "
        "  JOIN holders h ON h.id = pm.holder_id "
        "  LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id "
        "    AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name) "
        "  GROUP BY pm.pool_name"
        ") members ON members.pool_name = p.name "
        "ORDER BY p.name;"
    )


def cmd_check():
    errors = 0

    bad_holders = dsql_csv(
        "SELECT DISTINCT se.holder_id FROM share_events se "
        "LEFT JOIN holders h ON h.id = se.holder_id WHERE h.id IS NULL;"
    )
    if bad_holders:
        print(f"error: events reference unknown holders: {', '.join(bad_holders)}")
        errors += 1

    bad_classes = dsql_csv(
        "SELECT DISTINCT se.share_class FROM share_events se "
        "LEFT JOIN share_classes sc ON sc.name = se.share_class WHERE sc.name IS NULL;"
    )
    if bad_classes:
        print(f"error: events reference unknown share classes: {', '.join(bad_classes)}")
        errors += 1

    negative = dsql_csv(
        "SELECT holder_id, share_class, "
        "SUM(CASE WHEN event_type IN ('grant', 'transfer-in') THEN quantity ELSE -quantity END) AS net "
        "FROM share_events GROUP BY holder_id, share_class HAVING net < 0;"
    )
    if negative:
        print("error: negative holdings found:")
        for n in negative:
            print(f"  {n}")
        errors += 1

    over = dsql_csv(
        "SELECT class, authorised, issued FROM class_availability WHERE issued > authorised;"
    )
    if over:
        print("error: issued exceeds authorised:")
        for o in over:
            print(f"  {o}")
        errors += 1

    if errors:
        print(f"\n{errors} error(s) found")
        sys.exit(1)

    print("OK")


def cmd_brief():
    print("# shares context\n")

    print("## classes")
    for row in dsql_rows("SELECT name, nominal_value, nominal_currency, authorised FROM share_classes;"):
        print(f"  {row['name']}  nominal={row['nominal_currency']}{row['nominal_value']}  authorised={row['authorised']}")
    print()

    print("## holders")
    for row in dsql_rows("SELECT id, display_name FROM holders ORDER BY id;"):
        print(f"  {row['id']}  {row['display_name']}")
    print()

    print("## holdings")
    for row in dsql_rows("SELECT holder, class, held, pct FROM cap_table;"):
        print(f"  {row['holder']}  {row['class']}  held={row['held']} ({row['pct']}%)  vested={row['held']}")
    print()

    print("## availability")
    for row in dsql_rows("SELECT class, issued, authorised, available FROM class_availability;"):
        print(f"  {row['class']}  issued={row['issued']}/{row['authorised']}  available={row['available']}")


# --- Mutation commands ---


def cmd_grant(args):
    if len(args) < 3:
        die("usage: shares grant <holder-id> <class> <quantity>")
    holder, cls, qty = args[0], args[1], args[2]

    hname = dsql_val(f"SELECT display_name FROM holders WHERE id = '{holder}';")
    if not hname:
        die(f"unknown holder: {holder}")

    cauth = dsql_val(f"SELECT authorised FROM share_classes WHERE name = '{cls}';")
    if not cauth:
        die(f"unknown share class: {cls}")

    avail = dsql_val(f"SELECT available FROM class_availability WHERE class = '{cls}';")
    if int(qty) > int(avail):
        die(f"insufficient shares: requested {qty} but only {avail} available in class '{cls}'")

    today = date.today().isoformat()
    dsql(
        "INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity) "
        f"VALUES ('{today}', 'grant', '{holder}', '{cls}', {qty});"
    )
    dolt_commit(f"grant {qty} {cls} to {holder}")

    print(f"Granted {qty} {cls} shares to {hname}\n")
    cmd_table()


def cmd_transfer(args):
    if len(args) < 4:
        die("usage: shares transfer <from-id> <to-id> <class> <quantity>")
    frm, to, cls, qty = args[0], args[1], args[2], args[3]

    fname = dsql_val(f"SELECT display_name FROM holders WHERE id = '{frm}';")
    if not fname:
        die(f"unknown holder: {frm}")

    tname = dsql_val(f"SELECT display_name FROM holders WHERE id = '{to}';")
    if not tname:
        die(f"unknown holder: {to}")

    held = dsql_val(
        f"SELECT COALESCE(shares_held, 0) FROM holdings "
        f"WHERE holder_id = '{frm}' AND share_class = '{cls}';"
    ) or "0"
    if int(qty) > int(held):
        die(f"{fname} only holds {held} {cls} shares, cannot transfer {qty}")

    today = date.today().isoformat()
    dsql(
        "INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity) VALUES "
        f"('{today}', 'transfer-out', '{frm}', '{cls}', {qty}), "
        f"('{today}', 'transfer-in', '{to}', '{cls}', {qty});"
    )
    dolt_commit(f"transfer {qty} {cls} from {frm} to {to}")

    print(f"Transferred {qty} {cls} shares: {fname} -> {tname}\n")
    cmd_table()


def cmd_add_holder(args):
    if len(args) < 2:
        die('usage: shares add-holder <id> "Display Name"')
    hid, name = args[0], args[1]

    existing = dsql_val(f"SELECT id FROM holders WHERE id = '{hid}';")
    if existing:
        die(f"holder '{hid}' already exists")

    esc_name = name.replace("'", "''")
    dsql(f"INSERT INTO holders (id, display_name) VALUES ('{hid}', '{esc_name}');")
    dolt_commit(f"add holder: {name} ({hid})")
    print(f"Added holder: {name} ({hid})")


def cmd_add_pool(args):
    if len(args) < 3:
        die("usage: shares add-pool <name> <class> <budget>")
    name, cls, budget = args[0], args[1], args[2]

    cauth = dsql_val(f"SELECT authorised FROM share_classes WHERE name = '{cls}';")
    if not cauth:
        die(f"unknown share class: {cls}")

    dsql(f"INSERT INTO pools (name, share_class, budget) VALUES ('{name}', '{cls}', {budget});")
    dolt_commit(f"add pool: {name} ({budget} {cls})")
    print(f"Added pool: {name} — {budget} {cls} shares")


def cmd_pool_add(args):
    if len(args) < 2:
        die("usage: shares pool-add <pool> <holder-id>")
    pool, holder = args[0], args[1]

    pname = dsql_val(f"SELECT name FROM pools WHERE name = '{pool}';")
    if not pname:
        die(f"unknown pool: {pool}")

    hname = dsql_val(f"SELECT display_name FROM holders WHERE id = '{holder}';")
    if not hname:
        die(f"unknown holder: {holder}")

    dsql(f"INSERT INTO pool_members (pool_name, holder_id) VALUES ('{pool}', '{holder}');")
    dolt_commit(f"add {holder} to pool {pool}")
    print(f"Added {hname} to pool {pool}")


def cmd_push(args):
    subcmd = args[0] if args else ""
    script = os.path.join(SURFACE_ROOT, "modules/shares/scripts/push.py")
    env = {**os.environ, "PYTHONPATH": ""}
    subprocess.run(["python3", script, subcmd] + args[1:], env=env, check=True)


# --- PDF helpers ---


def generate_pdf(output_file, markdown):
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    subprocess.run(
        [
            "pandoc",
            "--pdf-engine=typst",
            "-V", "mainfont=Helvetica",
            "-V", "margin-top=2cm",
            "-V", "margin-bottom=2cm",
            "-V", "margin-left=2cm",
            "-V", "margin-right=2cm",
            "-o", output_file,
        ],
        input=markdown,
        text=True,
        check=True,
    )
    print(output_file)


def cmd_pdf_table():
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"cap-table-{today}.pdf")
    total = dsql_val("SELECT COALESCE(SUM(shares_held), 0) FROM holdings;")

    lines = [f"# Formabi — Cap Table\n", f"Generated: {today}\n"]

    if total == "0":
        lines.append("No shares issued.")
    else:
        lines.append("| Holder | Class | Held | % | Vested |")
        lines.append("|--------|-------|-----:|--:|-------:|")
        for row in dsql_rows("SELECT holder, class, held, pct FROM cap_table;"):
            lines.append(f"| {row['holder']} | {row['class']} | {row['held']} | {row['pct']}% | {row['held']} |")
        lines.append(f"\n**Total issued:** {total}")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_history():
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"share-history-{today}.pdf")

    lines = [
        f"# Formabi — Share History\n",
        f"Generated: {today}\n",
        "| Date | Event | Holder | Class | Qty |",
        "|------|-------|--------|-------|----:|",
    ]
    for row in dsql_rows(
        "SELECT se.event_date, se.event_type, h.display_name, se.share_class, se.quantity "
        "FROM share_events se JOIN holders h ON h.id = se.holder_id "
        "ORDER BY se.event_date, se.id;"
    ):
        lines.append(
            f"| {row['event_date']} | {row['event_type']} | {row['display_name']} "
            f"| {row['share_class']} | {row['quantity']} |"
        )

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_holder(holder_id):
    if not holder_id:
        die("usage: shares pdf holder <holder-id>")

    name = dsql_val(f"SELECT display_name FROM holders WHERE id = '{holder_id}';")
    if not name:
        die(f"unknown holder: {holder_id}")

    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{holder_id}-statement-{today}.pdf")

    lines = [
        "# Formabi — Holder Statement\n",
        f"**Holder:** {name}\n",
        f"Generated: {today}\n",
        "## Current Holdings\n",
        "| Class | Held | % | Vested |",
        "|-------|-----:|--:|-------:|",
    ]
    for row in dsql_rows(f"SELECT class, held, pct FROM cap_table WHERE holder_id = '{holder_id}';"):
        lines.append(f"| {row['class']} | {row['held']} | {row['pct']}% | {row['held']} |")

    htotal = dsql_val(f"SELECT COALESCE(SUM(shares_held), 0) FROM holdings WHERE holder_id = '{holder_id}';")
    lines.append(f"\n**Total shares:** {htotal}\n")

    lines.append("## Event History\n")
    lines.append("| Date | Event | Class | Qty |")
    lines.append("|------|-------|-------|----:|")
    for row in dsql_rows(
        f"SELECT event_date, event_type, share_class, quantity "
        f"FROM share_events WHERE holder_id = '{holder_id}' ORDER BY event_date, id;"
    ):
        lines.append(f"| {row['event_date']} | {row['event_type']} | {row['share_class']} | {row['quantity']} |")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "table":
            cmd_pdf_table()
        case "history":
            cmd_pdf_history()
        case "holder":
            cmd_pdf_holder(args[1] if len(args) > 1 else "")
        case _:
            print("Usage: shares pdf <table|history|holder <id>>")
            print()
            print("Report types:")
            print("  table              Cap table summary as PDF")
            print("  history            Full share event history as PDF")
            print("  holder <id>        Individual holder statement as PDF")
            print()
            print("PDFs are saved to downloads/")


def cmd_help():
    print("shares — cap table management (dolt)")
    print()
    print("Usage: shares <command> [args]")
    print()
    print("Read:")
    print("  table                              Cap table with percentages")
    print("  export                             Cap table as CSV")
    print("  holders                            List all shareholders")
    print("  history [holder]                   Share events (optionally filtered)")
    print("  pools                              Pool budgets and usage")
    print("  check                              Validate consistency")
    print("  brief                              Context dump for agent warm-up")
    print()
    print("Write:")
    print("  grant <holder> <class> <qty>       Grant shares")
    print("  transfer <from> <to> <class> <qty> Transfer shares")
    print('  add-holder <id> "Name"             Add a shareholder')
    print("  add-pool <name> <class> <budget>   Create a share pool")
    print("  pool-add <pool> <holder>           Add holder to pool")
    print()
    print("Export:")
    print("  pdf <table|history|holder <id>>    Generate PDF")
    print("  push <table|history|holders|pools|all>  Push to Google Sheets")
    print()
    print("  push requires: GOOGLE_SERVICE_ACCOUNT_KEY, SHARES_SHEET_ID")


# --- Routing ---


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "table":
            cmd_table()
        case "export":
            cmd_export()
        case "holders":
            cmd_holders()
        case "history":
            cmd_history(args[1] if len(args) > 1 else "")
        case "pools":
            cmd_pools()
        case "check":
            cmd_check()
        case "brief":
            cmd_brief()
        case "grant":
            cmd_grant(args[1:])
        case "transfer":
            cmd_transfer(args[1:])
        case "add-holder":
            cmd_add_holder(args[1:])
        case "add-pool":
            cmd_add_pool(args[1:])
        case "pool-add":
            cmd_pool_add(args[1:])
        case "push":
            cmd_push(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
