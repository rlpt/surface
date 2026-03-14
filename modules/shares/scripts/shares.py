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


def _vested_lookup(data):
    """Build {(holder_id, share_class): vested_qty} from vesting schedule.

    Caps vested at current holdings (transfers may reduce held below total vested).
    """
    vs = datalib.vesting_schedule(data)
    lookup = {}
    for v in vs:
        key = (v["holder_id"], v["share_class"])
        lookup[key] = lookup.get(key, 0) + v["vested"]
    # Cap at current holdings
    h = datalib.holdings(data)
    held = {}
    for r in h:
        key = (r["holder_id"], r["share_class"])
        held[key] = held.get(key, 0) + r["shares_held"]
    for key in lookup:
        if key in held:
            lookup[key] = min(lookup[key], held[key])
    return lookup


def cmd_table():
    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    vested = _vested_lookup(data)
    rows = [
        {
            "holder": r["holder"],
            "class": r["class"],
            "held": r["held"],
            "pct": f"{r['pct']}%",
            "vested": vested.get((r["holder_id"], r["class"]), r["held"]),
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


def cmd_vesting(filter_=""):
    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    vs = datalib.vesting_schedule(data)
    if filter_:
        vs = [v for v in vs if v["holder_id"] == filter_]
    rows = [
        {
            "holder": holders_map.get(v["holder_id"], v["holder_id"]),
            "class": v["share_class"],
            "granted": v["total_granted"],
            "vested": v["vested"],
            "unvested": v["unvested"],
            "pct": f"{v['pct_vested']}%",
            "cliff": v["cliff_date"],
            "fully_vested": v["fully_vested_date"],
        }
        for v in vs
    ]
    datalib.print_table(rows, ["holder", "class", "granted", "vested", "unvested", "pct", "cliff", "fully_vested"])


def cmd_model_round(args):
    if len(args) < 2:
        die("usage: shares model round <amount> <pre-money>")
    amount = float(args[0])
    pre_money = float(args[1])

    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    total_shares = sum(r["held"] for r in ct)

    if total_shares == 0:
        die("no shares issued — cannot model round")

    post_money = pre_money + amount
    dilution = amount / post_money
    new_shares = int(total_shares * amount / pre_money)

    print(f"Funding Round Model")
    print(f"  Investment:   {amount:,.0f}")
    print(f"  Pre-money:    {pre_money:,.0f}")
    print(f"  Post-money:   {post_money:,.0f}")
    print(f"  Dilution:     {dilution * 100:.1f}%")
    print(f"  New shares:   {new_shares:,}")
    print()

    print(f"{'Holder':<20} {'Class':<12} {'Current':>10} {'Pre %':>8} {'Post %':>8}")
    print("-" * 62)
    post_total = total_shares + new_shares
    for r in ct:
        pre_pct = r["held"] * 100.0 / total_shares
        post_pct = r["held"] * 100.0 / post_total
        print(f"{r['holder']:<20} {r['class']:<12} {r['held']:>10,} {pre_pct:>7.1f}% {post_pct:>7.1f}%")
    print(f"{'[New Investor]':<20} {'':12} {new_shares:>10,} {'':>8} {dilution * 100:>7.1f}%")
    print(f"{'TOTAL':<20} {'':12} {post_total:>10,} {'100.0%':>8} {'100.0%':>8}")


def cmd_model_pool_expand(args):
    if len(args) < 2:
        die("usage: shares model pool-expand <pool> <additional>")
    pool_name = args[0]
    additional = int(args[1])

    data = datalib.load("shares")
    pools = data.get("pools", [])
    pool = None
    for p in pools:
        if p["name"] == pool_name:
            pool = p
            break
    if not pool:
        die(f"unknown pool: {pool_name}")

    ct = datalib.cap_table(data)
    total_shares = sum(r["held"] for r in ct)
    ca = datalib.class_availability(data)
    avail = 0
    for c in ca:
        if c["class"] == pool["share_class"]:
            avail = c["available"]

    new_budget = pool["budget"] + additional
    post_total = total_shares + additional

    print(f"Pool Expansion Model: {pool_name}")
    print(f"  Current budget:  {pool['budget']:,}")
    print(f"  Additional:      {additional:,}")
    print(f"  New budget:      {new_budget:,}")
    print(f"  Available in class: {avail}")
    print()

    print(f"{'Holder':<20} {'Class':<12} {'Current':>10} {'Pre %':>8} {'Post %':>8}")
    print("-" * 62)
    for r in ct:
        pre_pct = r["held"] * 100.0 / total_shares if total_shares else 0
        post_pct = r["held"] * 100.0 / post_total if post_total else 0
        print(f"{r['holder']:<20} {r['class']:<12} {r['held']:>10,} {pre_pct:>7.1f}% {post_pct:>7.1f}%")
    dilution_pct = additional * 100.0 / post_total if post_total else 0
    print(f"{'[Pool expansion]':<20} {'':12} {additional:>10,} {'':>8} {dilution_pct:>7.1f}%")


def cmd_model(args):
    if not args:
        die("usage: shares model <round|pool-expand> [args]")
    match args[0]:
        case "round":
            cmd_model_round(args[1:])
        case "pool-expand":
            cmd_model_pool_expand(args[1:])
        case _:
            print("Usage: shares model <round|pool-expand>")
            print()
            print("Scenarios:")
            print("  round <amount> <pre-money>       Simulate funding round dilution")
            print("  pool-expand <pool> <additional>   Model pool expansion impact")


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
    vested = _vested_lookup(data)
    for r in ct:
        v = vested.get((r["holder_id"], r["class"]), r["held"])
        print(f"  {r['holder']}  {r['class']}  held={r['held']} ({r['pct']}%)  vested={v}")
    print()

    print("## availability")
    ca = datalib.class_availability(data)
    for r in ca:
        print(f"  {r['class']}  issued={r['issued']}/{r['authorised']}  available={r['available']}")


# --- Mutation commands ---


def cmd_grant(args):
    if len(args) < 3:
        die("usage: shares grant <holder-id> <class> <quantity> [--vesting-months N] [--cliff-months N]")
    holder, cls, qty = args[0], args[1], int(args[2])

    # Parse optional flags
    vesting_months = None
    cliff_months = None
    i = 3
    while i < len(args):
        if args[i] == "--vesting-months" and i + 1 < len(args):
            vesting_months = int(args[i + 1])
            i += 2
        elif args[i] == "--cliff-months" and i + 1 < len(args):
            cliff_months = int(args[i + 1])
            i += 2
        else:
            i += 1

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
    event = {
        "event_date": today,
        "event_type": "grant",
        "holder_id": holder,
        "share_class": cls,
        "quantity": qty,
    }
    if vesting_months:
        event["vesting_start"] = today
        event["vesting_months"] = vesting_months
        event["cliff_months"] = cliff_months or 0
    data.setdefault("share_events", []).append(event)
    datalib.save("shares", data)

    msg = f"grant {qty} {cls} to {holder}"
    if vesting_months:
        msg += f" (vesting: {vesting_months}m, cliff: {cliff_months or 0}m)"
    datalib.git_commit(msg)

    print(f"Granted {qty} {cls} shares to {hname}")
    if vesting_months:
        print(f"  Vesting: {vesting_months} months, cliff: {cliff_months or 0} months")
    print()
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
    datalib.generate_branded_pdf(output_file, markdown)


def cmd_pdf_table():
    data = datalib.load("shares")
    ct = datalib.cap_table(data)
    total = sum(r["held"] for r in ct)
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{today}-cap-table.pdf")

    lines = [f"# Formabi — Cap Table\n", f"Generated: {today}\n"]

    vested = _vested_lookup(data)
    if total == 0:
        lines.append("No shares issued.")
    else:
        lines.append("| Holder | Class | Held | % | Vested |")
        lines.append("|--------|-------|-----:|--:|-------:|")
        for r in ct:
            v = vested.get((r["holder_id"], r["class"]), r["held"])
            lines.append(f"| {r['holder']} | {r['class']} | {r['held']} | {r['pct']}% | {v} |")
        lines.append(f"\n**Total issued:** {total}")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_history():
    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    events = data.get("share_events", [])
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{today}-share-history.pdf")

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
    output = os.path.join(DOWNLOADS_DIR, f"{today}-{holder_id}-statement.pdf")

    vested = _vested_lookup(data)
    lines = [
        "# Formabi — Holder Statement\n",
        f"**Holder:** {name}\n",
        f"Generated: {today}\n",
        "## Current Holdings\n",
        "| Class | Held | % | Vested |",
        "|-------|-----:|--:|-------:|",
    ]
    for r in holder_ct:
        v = vested.get((r["holder_id"], r["class"]), r["held"])
        lines.append(f"| {r['class']} | {r['held']} | {r['pct']}% | {v} |")

    lines.append(f"\n**Total shares:** {htotal}\n")

    lines.append("## Event History\n")
    lines.append("| Date | Event | Class | Qty |")
    lines.append("|------|-------|-------|----:|")
    for e in holder_events:
        lines.append(f"| {e.get('event_date', '')} | {e['event_type']} | {e['share_class']} | {e['quantity']} |")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_vesting(filter_=""):
    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    vs = datalib.vesting_schedule(data)
    if filter_:
        vs = [v for v in vs if v["holder_id"] == filter_]
    today = date.today().isoformat()
    suffix = f"-{filter_}" if filter_ else ""
    output = os.path.join(DOWNLOADS_DIR, f"{today}-vesting-schedule{suffix}.pdf")

    lines = [f"# Formabi — Vesting Schedule\n", f"Generated: {today}\n"]
    if filter_:
        name = holders_map.get(filter_, filter_)
        lines.append(f"**Holder:** {name}\n")

    lines.append("| Holder | Class | Granted | Vested | Unvested | % Vested | Cliff | Fully Vested |")
    lines.append("|--------|-------|--------:|-------:|---------:|---------:|-------|--------------|")
    for v in vs:
        name = holders_map.get(v["holder_id"], v["holder_id"])
        lines.append(
            f"| {name} | {v['share_class']} | {v['total_granted']} | {v['vested']} "
            f"| {v['unvested']} | {v['pct_vested']}% | {v['cliff_date']} | {v['fully_vested_date']} |"
        )

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_certificate(args):
    if len(args) < 1:
        die("usage: shares pdf certificate <holder> [class]")
    holder_id = args[0]
    cls_filter = args[1] if len(args) > 1 else None

    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if holder_id not in holders_map:
        die(f"unknown holder: {holder_id}")
    name = holders_map[holder_id]

    h = datalib.holdings(data)
    holder_holdings = [r for r in h if r["holder_id"] == holder_id]
    if cls_filter:
        holder_holdings = [r for r in holder_holdings if r["share_class"] == cls_filter]

    if not holder_holdings:
        die(f"no holdings found for {holder_id}" + (f" in class {cls_filter}" if cls_filter else ""))

    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{today}-certificate-{holder_id}.pdf")

    lines = [f"# Share Certificate\n"]
    lines.append(f"**Formabi Ltd**\n")
    lines.append(f"Certificate Date: {today}\n")
    lines.append(f"---\n")
    lines.append(f"This is to certify that **{name}** is the registered holder of:\n")

    for r in holder_holdings:
        lines.append(f"- **{r['shares_held']:,}** {r['share_class']} shares\n")

    lines.append(f"\nGiven under the common seal of the company.\n")
    lines.append(f"\n---\n")
    lines.append(f"Director: ____________________\n")
    lines.append(f"\nSecretary: ____________________\n")

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_transfer(args):
    if len(args) < 4:
        die("usage: shares pdf transfer <from> <to> <class> <qty>")
    frm, to, cls, qty = args[0], args[1], args[2], int(args[3])

    data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in data.get("holders", [])}
    if frm not in holders_map:
        die(f"unknown holder: {frm}")
    if to not in holders_map:
        die(f"unknown holder: {to}")

    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{today}-transfer-{frm}-{to}.pdf")

    lines = [f"# Stock Transfer Form\n"]
    lines.append(f"**Formabi Ltd**\n")
    lines.append(f"Date: {today}\n")
    lines.append(f"---\n")
    lines.append(f"**Transferor:** {holders_map[frm]}\n")
    lines.append(f"**Transferee:** {holders_map[to]}\n")
    lines.append(f"**Share class:** {cls}\n")
    lines.append(f"**Quantity:** {qty:,}\n")
    lines.append(f"\n---\n")
    lines.append(f"Signed by Transferor: ____________________\n")
    lines.append(f"\nSigned by Transferee: ____________________\n")
    lines.append(f"\nWitnessed by: ____________________\n")

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
        case "vesting":
            cmd_pdf_vesting(args[1] if len(args) > 1 else "")
        case "certificate":
            cmd_pdf_certificate(args[1:])
        case "transfer":
            cmd_pdf_transfer(args[1:])
        case _:
            print("Usage: shares pdf <table|history|holder <id>|vesting [holder]|certificate <holder> [class]|transfer <from> <to> <class> <qty>>")
            print()
            print("Report types:")
            print("  table                          Cap table summary as PDF")
            print("  history                        Full share event history as PDF")
            print("  holder <id>                    Individual holder statement as PDF")
            print("  vesting [holder]               Vesting schedule as PDF")
            print("  certificate <holder> [class]   Share certificate as PDF")
            print("  transfer <from> <to> <class> <qty>  Stock transfer form as PDF")
            print()
            print("PDFs are saved to downloads/")


def cmd_help():
    print("shares — cap table management")
    print()
    print("Usage: shares <command> [args]")
    print()
    print("Read:")
    print("  table                              Cap table with percentages")
    print("  export                             Cap table as CSV")
    print("  holders                            List all shareholders")
    print("  history [holder]                   Share events (optionally filtered)")
    print("  vesting [holder]                   Vesting schedules")
    print("  pools                              Pool budgets and usage")
    print("  check                              Validate consistency")
    print("  brief                              Context dump for agent warm-up")
    print()
    print("Modelling:")
    print("  model round <amount> <pre-money>   Simulate funding round dilution")
    print("  model pool-expand <pool> <qty>     Model pool expansion impact")
    print()
    print("Write:")
    print("  grant <holder> <class> <qty> [--vesting-months N] [--cliff-months N]")
    print("  transfer <from> <to> <class> <qty> Transfer shares")
    print('  add-holder <id> "Name"             Add a shareholder')
    print("  add-pool <name> <class> <budget>   Create a share pool")
    print("  pool-add <pool> <holder>           Add holder to pool")
    print()
    print("Export:")
    print("  pdf <table|history|holder|vesting|certificate|transfer>")
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
        case "vesting":
            cmd_vesting(args[1] if len(args) > 1 else "")
        case "pools":
            cmd_pools()
        case "check":
            cmd_check()
        case "brief":
            cmd_brief()
        case "model":
            cmd_model(args[1:])
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
