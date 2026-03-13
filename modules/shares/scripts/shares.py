#!/usr/bin/env python3
"""shares — cap table management (toml)"""

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


def cmd_table():
    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    rows = [
        {
            "holder": r["holder"],
            "class": r["class"],
            "held": r["held"],
            "pct": f"{r['pct']}%",
            "vested": r["held"],
        }
        for r in ct
    ]
    datalib.print_table(rows, ["holder", "class", "held", "pct", "vested"])
    total = sum(r["held"] for r in ct)
    print(f"\nTotal issued: {total}")


def cmd_export():
    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    print("holder,share_class,shares_held,percentage,vested,total_granted,notes")
    for r in ct:
        print(f"{r['holder']},{r['class']},{r['held']},{r['pct']},{r['held']},{r['held']},")


def cmd_holders():
    data = datalib.load("shares")
    h = datalib.holdings(data)
    holder_totals = {}
    for r in h:
        holder_totals[r["holder_id"]] = holder_totals.get(r["holder_id"], 0) + r["shares_held"]
    holders = data.get("holders", [])
    rows = []
    for hld in sorted(holders, key=lambda x: x["id"]):
        rows.append({
            "id": hld["id"],
            "name": hld["display_name"],
            "total": holder_totals.get(hld["id"], 0),
        })
    datalib.print_table(rows, ["id", "name", "total"])


def cmd_history(filter_=""):
    data = datalib.load("shares")
    events = data.get("share_events", [])
    if filter_:
        events = [e for e in events if e["holder_id"] == filter_]
    rows = [
        {
            "date": e.get("event_date", ""),
            "event": e["event_type"],
            "holder": e["holder_id"],
            "class": e["share_class"],
            "qty": e["quantity"],
        }
        for e in sorted(events, key=lambda e: (str(e.get("event_date", "")), 0))
    ]
    datalib.print_table(rows, ["date", "event", "holder", "class", "qty"])


def cmd_pools():
    data = datalib.load("shares")
    pools = data.get("pools", [])
    pool_members = data.get("pool_members", [])
    h = datalib.holdings(data)
    holders_map = {r["id"]: r["display_name"] for r in data.get("holders", [])}

    holdings_map = {}
    for r in h:
        holdings_map[(r["holder_id"], r["share_class"])] = r["shares_held"]

    members_by_pool = {}
    for pm in pool_members:
        members_by_pool.setdefault(pm["pool_name"], []).append(pm["holder_id"])

    rows = []
    for p in sorted(pools, key=lambda x: x["name"]):
        cls = p["share_class"]
        members = members_by_pool.get(p["name"], [])
        issued = sum(holdings_map.get((mid, cls), 0) for mid in members)
        avail = p["budget"] - issued
        if members:
            member_strs = []
            for mid in members:
                name = holders_map.get(mid, mid)
                held = holdings_map.get((mid, cls), 0)
                member_strs.append(f"{name} ({held})")
            members_list = ", ".join(member_strs)
        else:
            members_list = "-"
        rows.append({
            "pool": p["name"],
            "class": cls,
            "budget": p["budget"],
            "issued": issued,
            "avail": avail,
            "members": members_list,
        })
    datalib.print_table(rows, ["pool", "class", "budget", "issued", "avail", "members"])


def cmd_check():
    data = datalib.load("shares")
    events = data.get("share_events", [])
    holders = {h["id"] for h in data.get("holders", [])}
    classes = {sc["name"] for sc in data.get("share_classes", [])}
    errors = 0

    # Check 1: bad holders
    bad_holders = sorted({e["holder_id"] for e in events if e["holder_id"] not in holders})
    if bad_holders:
        print(f"error: events reference unknown holders: {', '.join(bad_holders)}")
        errors += 1

    # Check 2: bad classes
    bad_classes = sorted({e["share_class"] for e in events if e["share_class"] not in classes})
    if bad_classes:
        print(f"error: events reference unknown share classes: {', '.join(bad_classes)}")
        errors += 1

    # Check 3: negative holdings
    from collections import defaultdict
    totals = defaultdict(int)
    for e in events:
        key = (e["holder_id"], e["share_class"])
        if e["event_type"] in ("grant", "transfer-in"):
            totals[key] += e["quantity"]
        else:
            totals[key] -= e["quantity"]
    negative = [(k, v) for k, v in sorted(totals.items()) if v < 0]
    if negative:
        print("error: negative holdings found:")
        for (hid, cls), net in negative:
            print(f"  {hid},{cls},{net}")
        errors += 1

    # Check 4: over-issued
    ca = datalib.class_availability(data)
    over = [r for r in ca if r["issued"] > r["authorised"]]
    if over:
        print("error: issued exceeds authorised:")
        for o in over:
            print(f"  {o['class']},{o['authorised']},{o['issued']}")
        errors += 1

    if errors:
        print(f"\n{errors} error(s) found")
        sys.exit(1)

    print("OK")


def cmd_brief():
    data = datalib.load("shares")
    print("# shares context\n")

    print("## classes")
    for sc in data.get("share_classes", []):
        print(f"  {sc['name']}  nominal={sc['nominal_currency']}{sc['nominal_value']}  authorised={sc['authorised']}")
    print()

    print("## holders")
    for h in sorted(data.get("holders", []), key=lambda x: x["id"]):
        print(f"  {h['id']}  {h['display_name']}")
    print()

    print("## holdings")
    ct = datalib.cap_table(data)
    for r in ct:
        print(f"  {r['holder']}  {r['class']}  held={r['held']} ({r['pct']}%)  vested={r['held']}")
    print()

    print("## availability")
    ca = datalib.class_availability(data)
    for r in ca:
        print(f"  {r['class']}  issued={r['issued']}/{r['authorised']}  available={r['available']}")


# --- Mutation commands ---


def cmd_grant(args):
    if len(args) < 3:
        die("usage: shares grant <holder-id> <class> <quantity>")
    holder, cls, qty = args[0], args[1], int(args[2])

    data = datalib.load("shares")

    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if holder not in holders_map:
        die(f"unknown holder: {holder}")
    hname = holders_map[holder]

    classes = {sc["name"] for sc in data.get("share_classes", [])}
    if cls not in classes:
        die(f"unknown share class: {cls}")

    ca = datalib.class_availability(data)
    avail = 0
    for r in ca:
        if r["class"] == cls:
            avail = r["available"]
            break
    if qty > avail:
        die(f"insufficient shares: requested {qty} but only {avail} available in class '{cls}'")

    today = date.today().isoformat()
    data.setdefault("share_events", []).append({
        "event_date": today,
        "event_type": "grant",
        "holder_id": holder,
        "share_class": cls,
        "quantity": qty,
    })
    datalib.save("shares", data)
    datalib.git_commit(f"grant {qty} {cls} to {holder}")

    print(f"Granted {qty} {cls} shares to {hname}\n")
    cmd_table()


def cmd_transfer(args):
    if len(args) < 4:
        die("usage: shares transfer <from-id> <to-id> <class> <quantity>")
    frm, to, cls, qty = args[0], args[1], args[2], int(args[3])

    data = datalib.load("shares")

    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if frm not in holders_map:
        die(f"unknown holder: {frm}")
    fname = holders_map[frm]

    if to not in holders_map:
        die(f"unknown holder: {to}")
    tname = holders_map[to]

    h = datalib.holdings(data)
    held = 0
    for r in h:
        if r["holder_id"] == frm and r["share_class"] == cls:
            held = r["shares_held"]
            break
    if qty > held:
        die(f"{fname} only holds {held} {cls} shares, cannot transfer {qty}")

    today = date.today().isoformat()
    data.setdefault("share_events", []).append({
        "event_date": today,
        "event_type": "transfer-out",
        "holder_id": frm,
        "share_class": cls,
        "quantity": qty,
    })
    data["share_events"].append({
        "event_date": today,
        "event_type": "transfer-in",
        "holder_id": to,
        "share_class": cls,
        "quantity": qty,
    })
    datalib.save("shares", data)
    datalib.git_commit(f"transfer {qty} {cls} from {frm} to {to}")

    print(f"Transferred {qty} {cls} shares: {fname} -> {tname}\n")
    cmd_table()


def cmd_add_holder(args):
    if len(args) < 2:
        die('usage: shares add-holder <id> "Display Name"')
    hid, name = args[0], args[1]

    data = datalib.load("shares")
    existing = {h["id"] for h in data.get("holders", [])}
    if hid in existing:
        die(f"holder '{hid}' already exists")

    data.setdefault("holders", []).append({"id": hid, "display_name": name})
    datalib.save("shares", data)
    datalib.git_commit(f"add holder: {name} ({hid})")
    print(f"Added holder: {name} ({hid})")


def cmd_add_pool(args):
    if len(args) < 3:
        die("usage: shares add-pool <name> <class> <budget>")
    name, cls, budget = args[0], args[1], int(args[2])

    data = datalib.load("shares")
    classes = {sc["name"] for sc in data.get("share_classes", [])}
    if cls not in classes:
        die(f"unknown share class: {cls}")

    data.setdefault("pools", []).append({
        "name": name,
        "share_class": cls,
        "budget": budget,
    })
    datalib.save("shares", data)
    datalib.git_commit(f"add pool: {name} ({budget} {cls})")
    print(f"Added pool: {name} — {budget} {cls} shares")


def cmd_pool_add(args):
    if len(args) < 2:
        die("usage: shares pool-add <pool> <holder-id>")
    pool, holder = args[0], args[1]

    data = datalib.load("shares")

    pool_names = {p["name"] for p in data.get("pools", [])}
    if pool not in pool_names:
        die(f"unknown pool: {pool}")

    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if holder not in holders_map:
        die(f"unknown holder: {holder}")

    data.setdefault("pool_members", []).append({
        "pool_name": pool,
        "holder_id": holder,
    })
    datalib.save("shares", data)
    datalib.git_commit(f"add {holder} to pool {pool}")
    print(f"Added {holders_map[holder]} to pool {pool}")


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
    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    total = sum(r["held"] for r in ct)
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"cap-table-{today}.pdf")

    lines = [f"# Formabi — Cap Table\n", f"Generated: {today}\n"]

    if total == 0:
        lines.append("No shares issued.")
    else:
        lines.append("| Holder | Class | Held | % | Vested |")
        lines.append("|--------|-------|-----:|--:|-------:|")
        for r in ct:
            lines.append(f"| {r['holder']} | {r['class']} | {r['held']} | {r['pct']}% | {r['held']} |")
        lines.append(f"\n**Total issued:** {total}")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_history():
    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    events = data.get("share_events", [])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"share-history-{today}.pdf")

    lines = [
        f"# Formabi — Share History\n",
        f"Generated: {today}\n",
        "| Date | Event | Holder | Class | Qty |",
        "|------|-------|--------|-------|----:|",
    ]
    for e in sorted(events, key=lambda e: (str(e.get("event_date", "")), 0)):
        name = holders_map.get(e["holder_id"], e["holder_id"])
        lines.append(
            f"| {e.get('event_date', '')} | {e['event_type']} | {name} "
            f"| {e['share_class']} | {e['quantity']} |"
        )

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_holder(holder_id):
    if not holder_id:
        die("usage: shares pdf holder <holder-id>")

    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if holder_id not in holders_map:
        die(f"unknown holder: {holder_id}")
    name = holders_map[holder_id]

    ct = datalib.cap_table(data)
    holder_ct = [r for r in ct if r["holder_id"] == holder_id]

    h = datalib.holdings(data)
    htotal = sum(r["shares_held"] for r in h if r["holder_id"] == holder_id)

    events = data.get("share_events", [])
    holder_events = [e for e in events if e["holder_id"] == holder_id]
    holder_events.sort(key=lambda e: (str(e.get("event_date", "")), 0))

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
    for r in holder_ct:
        lines.append(f"| {r['class']} | {r['held']} | {r['pct']}% | {r['held']} |")

    lines.append(f"\n**Total shares:** {htotal}\n")

    lines.append("## Event History\n")
    lines.append("| Date | Event | Class | Qty |")
    lines.append("|------|-------|-------|----:|")
    for e in holder_events:
        lines.append(f"| {e.get('event_date', '')} | {e['event_type']} | {e['share_class']} | {e['quantity']} |")

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
    print("shares — cap table management (toml)")
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
