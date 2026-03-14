#!/usr/bin/env python3
"""Board meetings, minutes, and resolutions — CLI backed by TOML data."""

import http.server
import os
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")

COLORS = {
    "primary": os.environ.get("BRAND_PRIMARY", "#6366f1"),
    "accent": os.environ.get("BRAND_ACCENT", "#a78bfa"),
    "bg": os.environ.get("BRAND_BG", "#0a0a1a"),
    "text": os.environ.get("BRAND_TEXT", "#e0e0e0"),
}


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# CLI commands — read
# ---------------------------------------------------------------------------

def cmd_meetings():
    data = datalib.load("board")
    meetings = data.get("board_meetings", [])
    attendees = data.get("board_attendees", [])
    resolutions = data.get("board_resolutions", [])

    if not meetings:
        print("No meetings found.")
        return

    # Count attendees and resolutions per meeting
    att_counts = {}
    for a in attendees:
        mid = a["meeting_id"]
        att_counts[mid] = att_counts.get(mid, 0) + 1

    res_counts = {}
    for r in resolutions:
        mid = r["meeting_id"]
        res_counts[mid] = res_counts.get(mid, 0) + 1

    # Sort by meeting_date descending
    sorted_meetings = sorted(meetings, key=lambda m: m.get("meeting_date", ""), reverse=True)

    print(f"{'ID':<12} {'Date':<12} {'Status':<10} {'Attend':>6} {'Resol':>5}  Title")
    print("-" * 78)
    for m in sorted_meetings:
        mid = m["id"]
        mdate = m.get("meeting_date", "")
        title = m.get("title", "")
        status = m.get("status", "")
        att = att_counts.get(mid, 0)
        res = res_counts.get(mid, 0)
        print(f"{mid:<12} {mdate:<12} {status:<10} {att:>6} {res:>5}  {title}")


def cmd_meeting(meeting_id):
    data = datalib.load("board")
    meetings = [m for m in data.get("board_meetings", []) if m["id"] == meeting_id]
    if not meetings:
        die(f"meeting '{meeting_id}' not found")
    m = meetings[0]
    print(f"Meeting: {m['title']}")
    print(f"Date:    {m['meeting_date']}")
    print(f"Status:  {m['status']}")
    if m.get("location"):
        print(f"Location: {m['location']}")
    if m.get("called_by"):
        print(f"Called by: {m['called_by']}")

    attendees = sorted(
        [a for a in data.get("board_attendees", []) if a["meeting_id"] == meeting_id],
        key=lambda a: (a.get("role", ""), a.get("person_name", ""))
    )
    if attendees:
        print(f"\nAttendees:")
        for a in attendees:
            role_str = f" ({a['role']})" if a.get("role") else ""
            print(f"  - {a['person_name']}{role_str}")

    minutes = sorted(
        [mi for mi in data.get("board_minutes", []) if mi["meeting_id"] == meeting_id],
        key=lambda mi: mi.get("seq", 0)
    )
    if minutes:
        print(f"\nMinutes:")
        for mi in minutes:
            print(f"  {mi['seq']}. {mi['item_text']}")

    resolutions = sorted(
        [r for r in data.get("board_resolutions", []) if r["meeting_id"] == meeting_id],
        key=lambda r: r.get("id", "")
    )
    if resolutions:
        print(f"\nResolutions:")
        for r in resolutions:
            status_mark = {"passed": "[PASSED]", "failed": "[FAILED]", "pending": "[PENDING]"}.get(r["status"], f"[{r['status']}]")
            proposer = f" (proposed by {r['proposed_by']})" if r.get("proposed_by") else ""
            print(f"  {r['id']}: {status_mark} {r['resolution_text']}{proposer}")


def cmd_resolutions(filter_status):
    data = datalib.load("board")
    meetings_map = {m["id"]: m for m in data.get("board_meetings", [])}
    resolutions = data.get("board_resolutions", [])

    if filter_status == "pending":
        resolutions = [r for r in resolutions if r.get("status") == "pending"]
    elif filter_status == "passed":
        resolutions = [r for r in resolutions if r.get("status") == "passed"]

    # Sort by meeting_date desc, then resolution id
    resolutions = sorted(
        resolutions,
        key=lambda r: (meetings_map.get(r["meeting_id"], {}).get("meeting_date", ""), r.get("id", "")),
        reverse=True,
    )

    if not resolutions:
        print("No resolutions found.")
        return
    print(f"{'ID':<12} {'Date':<12} {'Status':<10} Resolution")
    print("-" * 78)
    for r in resolutions:
        meeting = meetings_map.get(r["meeting_id"], {})
        mdate = meeting.get("meeting_date", "")
        text = r["resolution_text"][:50] + ("..." if len(r["resolution_text"]) > 50 else "")
        print(f"{r['id']:<12} {mdate:<12} {r['status']:<10} {text}")


def cmd_minutes(meeting_id):
    data = datalib.load("board")
    meetings = [m for m in data.get("board_meetings", []) if m["id"] == meeting_id]
    if not meetings:
        die(f"meeting '{meeting_id}' not found")
    m = meetings[0]
    print(f"Minutes — {m['title']} ({m['meeting_date']})")
    print("=" * 60)

    minutes = sorted(
        [mi for mi in data.get("board_minutes", []) if mi["meeting_id"] == meeting_id],
        key=lambda mi: mi.get("seq", 0)
    )
    if not minutes:
        print("No minutes recorded.")
        return
    for mi in minutes:
        print(f"\n{mi['seq']}. {mi['item_text']}")


# ---------------------------------------------------------------------------
# CLI commands — write
# ---------------------------------------------------------------------------

def cmd_new(args):
    if len(args) < 2:
        die("usage: board new <date> <title>")
    meeting_date = args[0]
    title = " ".join(args[1:])
    mid = f"bm-{meeting_date}"

    data = datalib.load("board")
    if "board_meetings" not in data:
        data["board_meetings"] = []
    if "board_attendees" not in data:
        data["board_attendees"] = []
    if "board_minutes" not in data:
        data["board_minutes"] = []
    if "board_resolutions" not in data:
        data["board_resolutions"] = []

    data["board_meetings"].append({
        "id": mid,
        "meeting_date": meeting_date,
        "title": title,
        "status": "scheduled",
    })
    datalib.save("board", data)
    datalib.git_commit(f"board: schedule meeting {mid} — {title}")
    print(f"Created meeting: {mid}")


def cmd_attend(args):
    if len(args) < 2:
        die("usage: board attend <meeting-id> <person> [role]")
    meeting_id = args[0]
    person = args[1]
    role = args[2] if len(args) > 2 else "director"

    data = datalib.load("board")
    if "board_attendees" not in data:
        data["board_attendees"] = []
    data["board_attendees"].append({
        "meeting_id": meeting_id,
        "person_name": person,
        "role": role,
    })
    datalib.save("board", data)
    datalib.git_commit(f"board: {person} attending {meeting_id} as {role}")
    print(f"Added {person} ({role}) to {meeting_id}")


def cmd_minute(args):
    if len(args) < 3:
        die("usage: board minute <meeting-id> <seq> \"text\"")
    meeting_id = args[0]
    seq = int(args[1])
    text = " ".join(args[2:])

    data = datalib.load("board")
    if "board_minutes" not in data:
        data["board_minutes"] = []
    data["board_minutes"].append({
        "meeting_id": meeting_id,
        "seq": seq,
        "item_text": text,
    })
    datalib.save("board", data)
    datalib.git_commit(f"board: minute {seq} for {meeting_id}")
    print(f"Added minute item {seq}")


def cmd_resolve(args):
    if len(args) < 2:
        die("usage: board resolve <meeting-id> \"resolution text\"")
    meeting_id = args[0]
    text = " ".join(args[1:])

    data = datalib.load("board")
    if "board_resolutions" not in data:
        data["board_resolutions"] = []
    count = len([r for r in data["board_resolutions"] if r["meeting_id"] == meeting_id])
    seq = count + 1
    rid = f"{meeting_id}-r{seq}"

    data["board_resolutions"].append({
        "id": rid,
        "meeting_id": meeting_id,
        "resolution_text": text,
        "status": "pending",
    })
    datalib.save("board", data)
    datalib.git_commit(f"board: propose resolution {rid}")
    print(f"Proposed resolution: {rid}")


def cmd_vote(args):
    if len(args) < 2:
        die("usage: board vote <resolution-id> passed|failed")
    rid = args[0]
    outcome = args[1]
    if outcome not in ("passed", "failed"):
        die("outcome must be 'passed' or 'failed'")

    data = datalib.load("board")
    found = False
    for r in data.get("board_resolutions", []):
        if r["id"] == rid:
            r["status"] = outcome
            r["voted_date"] = date.today().isoformat()
            found = True
            break
    if not found:
        die(f"resolution '{rid}' not found")

    datalib.save("board", data)
    datalib.git_commit(f"board: resolution {rid} {outcome}")
    print(f"Resolution {rid}: {outcome}")


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "allotment": {
        "description": "Allot shares to a holder",
        "resolution": "RESOLVED that the directors allot {qty} {share_class} shares to {holder_name}, credited as fully paid.",
        "minute": "The board resolved to allot {qty} {share_class} shares to {holder_name}.",
    },
    "appointment": {
        "description": "Appoint a director",
        "resolution": "RESOLVED that {person_name} be appointed as a director of the company with effect from {date}.",
        "minute": "The board resolved to appoint {person_name} as director.",
    },
    "resignation": {
        "description": "Accept director resignation",
        "resolution": "RESOLVED that the resignation of {person_name} as director be accepted with effect from {date}.",
        "minute": "The board noted and accepted the resignation of {person_name} as director.",
    },
    "dividend": {
        "description": "Declare a dividend",
        "resolution": "RESOLVED that an interim dividend of {amount} per {share_class} share be declared, payable on {date}.",
        "minute": "The board declared an interim dividend of {amount} per {share_class} share.",
    },
    "accounts": {
        "description": "Approve annual accounts",
        "resolution": "RESOLVED that the annual accounts for the period ending {date} be approved and signed.",
        "minute": "The board approved the annual accounts for the period ending {date}.",
    },
    "bank-mandate": {
        "description": "Update bank mandate",
        "resolution": "RESOLVED that the bank mandate be updated to add {person_name} as an authorised signatory.",
        "minute": "The board resolved to update the bank mandate to add {person_name}.",
    },
}


def cmd_template_list():
    print(f"{'Template':<16} Description")
    print("-" * 50)
    for name, t in sorted(TEMPLATES.items()):
        print(f"{name:<16} {t['description']}")


def cmd_template_apply(args):
    if len(args) < 2:
        die("usage: board template <name> <meeting-id> [key=value ...]")
    tname = args[0]
    meeting_id = args[1]

    if tname not in TEMPLATES:
        die(f"unknown template: {tname} (use 'board template list')")

    # Parse key=value args
    kwargs = {"date": date.today().isoformat()}
    for arg in args[2:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            kwargs[k] = v

    template = TEMPLATES[tname]
    try:
        resolution_text = template["resolution"].format(**kwargs)
        minute_text = template["minute"].format(**kwargs)
    except KeyError as e:
        die(f"missing template parameter: {e} (pass as key=value)")

    data = datalib.load("board")

    # Ensure meeting exists
    meeting_ids = {m["id"] for m in data.get("board_meetings", [])}
    if meeting_id not in meeting_ids:
        die(f"meeting '{meeting_id}' not found")

    # Add resolution
    if "board_resolutions" not in data:
        data["board_resolutions"] = []
    count = len([r for r in data["board_resolutions"] if r["meeting_id"] == meeting_id])
    seq = count + 1
    rid = f"{meeting_id}-r{seq}"
    data["board_resolutions"].append({
        "id": rid,
        "meeting_id": meeting_id,
        "resolution_text": resolution_text,
        "status": "pending",
    })

    # Add minute item
    if "board_minutes" not in data:
        data["board_minutes"] = []
    existing_seqs = [mi["seq"] for mi in data["board_minutes"] if mi["meeting_id"] == meeting_id]
    next_seq = max(existing_seqs, default=0) + 1
    data["board_minutes"].append({
        "meeting_id": meeting_id,
        "seq": next_seq,
        "item_text": minute_text,
    })

    datalib.save("board", data)
    datalib.git_commit(f"board: apply template '{tname}' to {meeting_id}")
    print(f"Applied template '{tname}' to {meeting_id}")
    print(f"  Resolution: {rid}")
    print(f"  Minute item: {next_seq}")


def cmd_template(args):
    subcmd = args[0] if args else "list"
    match subcmd:
        case "list":
            cmd_template_list()
        case _:
            cmd_template_apply(args)


# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

def esc(val):
    return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def html_table(rows, highlight_col=None):
    if not rows:
        return '<p class="empty">No data.</p>'
    headers = list(rows[0].keys())
    out = ['<table>', '<thead><tr>']
    for h in headers:
        out.append(f'<th>{esc(h)}</th>')
    out.append('</tr></thead><tbody>')
    for row in rows:
        out.append('<tr>')
        for h in headers:
            val = row.get(h, "")
            cls = ' class="highlight"' if h == highlight_col else ""
            out.append(f'<td{cls}>{esc(val)}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def html_page(title, body, nav_active=""):
    nav_items = [
        ("index.html", "Meetings"),
        ("resolutions.html", "Resolutions"),
    ]
    nav_html = []
    for href, label in nav_items:
        active = ' class="active"' if href.replace(".html", "") == nav_active else ""
        nav_html.append(f'<a href="{href}"{active}>{label}</a>')
    nav = "\n".join(nav_html)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — Board — Formabi</title>
<style>
:root {{
  --primary: {COLORS["primary"]};
  --accent: {COLORS["accent"]};
  --bg: {COLORS["bg"]};
  --text: {COLORS["text"]};
  --surface: #141428;
  --border: #2a2a4a;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}}
nav {{
  display: flex;
  gap: 0;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 1rem;
}}
nav a {{
  color: var(--text);
  text-decoration: none;
  padding: 0.75rem 1.25rem;
  opacity: 0.6;
  border-bottom: 2px solid transparent;
  transition: opacity 0.2s;
}}
nav a:hover {{ opacity: 0.9; }}
nav a.active {{
  opacity: 1;
  border-bottom-color: var(--primary);
  color: var(--primary);
}}
main {{
  max-width: 960px;
  margin: 0 auto;
  padding: 2rem 1rem;
}}
h1 {{
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
  color: var(--primary);
}}
h2 {{
  font-size: 1.1rem;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  color: var(--accent);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.25rem;
}}
h3 {{
  font-size: 1rem;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--text);
}}
p.subtitle {{
  color: var(--accent);
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}}
table {{
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
  font-size: 0.85rem;
}}
th {{
  text-align: left;
  padding: 0.5rem 0.75rem;
  border-bottom: 2px solid var(--border);
  color: var(--accent);
  font-weight: 600;
  white-space: nowrap;
}}
td {{
  padding: 0.4rem 0.75rem;
  border-bottom: 1px solid var(--border);
}}
td.highlight {{
  color: var(--primary);
  font-weight: 600;
}}
tr:hover {{
  background: rgba(99, 102, 241, 0.05);
}}
.cards {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}}
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
}}
.card .label {{
  font-size: 0.75rem;
  color: var(--accent);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}}
.card .value {{
  font-size: 1.5rem;
  color: var(--primary);
  font-weight: 700;
  margin-top: 0.25rem;
}}
.status-passed {{ color: #22c55e; font-weight: 600; }}
.status-failed {{ color: #ef4444; font-weight: 600; }}
.status-pending {{ color: #eab308; font-weight: 600; }}
.minute-item {{
  margin-bottom: 0.75rem;
  padding: 0.5rem 0.75rem;
  border-left: 3px solid var(--border);
}}
.minute-item .seq {{
  color: var(--accent);
  font-weight: 600;
  margin-right: 0.5rem;
}}
.resolution-box {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}}
.resolution-box .res-id {{
  font-size: 0.75rem;
  color: var(--accent);
}}
.empty {{
  color: var(--accent);
  font-style: italic;
  padding: 1rem 0;
}}
footer {{
  text-align: center;
  padding: 2rem 1rem;
  font-size: 0.75rem;
  color: var(--accent);
  opacity: 0.5;
}}
</style>
</head>
<body>
<nav>
{nav}
</nav>
<main>
<h1>{esc(title)}</h1>
{body}
</main>
<footer>Generated {date.today().isoformat()} from data/</footer>
</body>
</html>"""


def build_meetings_page():
    data = datalib.load("board")
    meetings = data.get("board_meetings", [])
    attendees = data.get("board_attendees", [])
    resolutions = data.get("board_resolutions", [])

    total = len(meetings)
    passed = len([r for r in resolutions if r.get("status") == "passed"])
    pending = len([r for r in resolutions if r.get("status") == "pending"])

    cards = f"""
<p class="subtitle">Board governance — meetings, minutes, and resolutions</p>
<div class="cards">
  <div class="card"><div class="label">Meetings</div><div class="value">{esc(total)}</div></div>
  <div class="card"><div class="label">Resolutions Passed</div><div class="value">{esc(passed)}</div></div>
  <div class="card"><div class="label">Pending Resolutions</div><div class="value">{esc(pending)}</div></div>
</div>
"""

    sorted_meetings = sorted(meetings, key=lambda m: m.get("meeting_date", ""), reverse=True)

    body = cards
    for m in sorted_meetings:
        mid = m["id"]
        body += f'<h2><a href="{esc(mid)}.html" style="color: var(--accent); text-decoration: none;">'
        body += f'{esc(m["meeting_date"])} — {esc(m["title"])}</a></h2>\n'

        meeting_attendees = sorted(
            [a for a in attendees if a["meeting_id"] == mid],
            key=lambda a: (a.get("role", ""), a.get("person_name", ""))
        )
        if meeting_attendees:
            body += "<p><strong>Attendees:</strong> "
            body += ", ".join(
                f'{esc(a["person_name"])} ({esc(a["role"])})'
                for a in meeting_attendees
            )
            body += "</p>\n"

        meeting_resolutions = sorted(
            [r for r in resolutions if r["meeting_id"] == mid],
            key=lambda r: r.get("id", "")
        )
        if meeting_resolutions:
            for r in meeting_resolutions:
                status_cls = f"status-{r['status']}"
                body += f'<div class="resolution-box">'
                body += f'<span class="res-id">{esc(r["id"])}</span> '
                body += f'<span class="{status_cls}">[{esc(r["status"].upper())}]</span> '
                body += f'{esc(r["resolution_text"])}</div>\n'

    return html_page("Board Meetings", body, "index")


def build_meeting_detail(meeting_id):
    data = datalib.load("board")
    meetings = [m for m in data.get("board_meetings", []) if m["id"] == meeting_id]
    if not meetings:
        return None
    m = meetings[0]

    body = f'<p class="subtitle">{esc(m["meeting_date"])} — {esc(m["status"])}'
    if m.get("location"):
        body += f' — {esc(m["location"])}'
    body += "</p>\n"

    meeting_attendees = sorted(
        [a for a in data.get("board_attendees", []) if a["meeting_id"] == meeting_id],
        key=lambda a: (a.get("role", ""), a.get("person_name", ""))
    )
    if meeting_attendees:
        body += "<h2>Attendees</h2>\n"
        body += html_table(meeting_attendees)

    minutes = sorted(
        [mi for mi in data.get("board_minutes", []) if mi["meeting_id"] == meeting_id],
        key=lambda mi: mi.get("seq", 0)
    )
    if minutes:
        body += "<h2>Minutes</h2>\n"
        for mi in minutes:
            body += f'<div class="minute-item"><span class="seq">{esc(mi["seq"])}.</span> '
            body += f'{esc(mi["item_text"])}</div>\n'

    meeting_resolutions = sorted(
        [r for r in data.get("board_resolutions", []) if r["meeting_id"] == meeting_id],
        key=lambda r: r.get("id", "")
    )
    if meeting_resolutions:
        body += "<h2>Resolutions</h2>\n"
        for r in meeting_resolutions:
            status_cls = f"status-{r['status']}"
            body += f'<div class="resolution-box">'
            body += f'<span class="res-id">{esc(r["id"])}</span> '
            body += f'<span class="{status_cls}">[{esc(r["status"].upper())}]</span> '
            body += f'{esc(r["resolution_text"])}'
            if r.get("proposed_by"):
                body += f' <em>— proposed by {esc(r["proposed_by"])}</em>'
            if r.get("voted_date"):
                body += f' <em>(voted {esc(r["voted_date"])})</em>'
            body += "</div>\n"

    return html_page(m["title"], body)


def build_resolutions_page():
    data = datalib.load("board")
    meetings_map = {m["id"]: m for m in data.get("board_meetings", [])}
    resolutions = data.get("board_resolutions", [])

    # Sort by meeting_date desc, then resolution id
    resolutions = sorted(
        resolutions,
        key=lambda r: (meetings_map.get(r["meeting_id"], {}).get("meeting_date", ""), r.get("id", "")),
        reverse=True,
    )

    body = '<p class="subtitle">All board resolutions — passed, pending, and failed</p>\n'

    if not resolutions:
        body += '<p class="empty">No resolutions recorded.</p>'
    else:
        for r in resolutions:
            meeting = meetings_map.get(r["meeting_id"], {})
            mdate = meeting.get("meeting_date", "")
            status_cls = f"status-{r['status']}"
            body += f'<div class="resolution-box">'
            body += f'<span class="res-id">{esc(r["id"])} — {esc(mdate)}</span><br>'
            body += f'<span class="{status_cls}">[{esc(r["status"].upper())}]</span> '
            body += f'{esc(r["resolution_text"])}'
            if r.get("proposed_by"):
                body += f' <em>— {esc(r["proposed_by"])}</em>'
            body += "</div>\n"

    return html_page("Resolutions", body, "resolutions")


def cmd_html(args):
    out_dir = args[0] if args else os.path.join(SURFACE_ROOT, "out", "board")
    os.makedirs(out_dir, exist_ok=True)

    # index page (all meetings)
    path = os.path.join(out_dir, "index.html")
    with open(path, "w") as f:
        f.write(build_meetings_page())
    print("  index.html")

    # resolutions page
    path = os.path.join(out_dir, "resolutions.html")
    with open(path, "w") as f:
        f.write(build_resolutions_page())
    print("  resolutions.html")

    # individual meeting pages
    data = datalib.load("board")
    meetings = sorted(
        data.get("board_meetings", []),
        key=lambda m: m.get("meeting_date", ""),
        reverse=True,
    )
    for m in meetings:
        mid = m["id"]
        detail = build_meeting_detail(mid)
        if detail:
            fname = f"{mid}.html"
            path = os.path.join(out_dir, fname)
            with open(path, "w") as f:
                f.write(detail)
            print(f"  {fname}")

    print(f"\nboard pack built → {out_dir}/")


def cmd_serve(args):
    out_dir = args[0] if args else os.path.join(SURFACE_ROOT, "out", "board")
    cmd_html([out_dir])
    print("\nserving on http://localhost:8001 (ctrl-c to stop)")
    os.chdir(out_dir)
    server = http.server.HTTPServer(("", 8001), http.server.SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


# ---------------------------------------------------------------------------
# PDF output
# ---------------------------------------------------------------------------

def generate_pdf(output_file, markdown):
    datalib.generate_branded_pdf(output_file, markdown)


def meeting_markdown(meeting_id):
    """Build markdown for a single meeting."""
    data = datalib.load("board")
    meetings = [m for m in data.get("board_meetings", []) if m["id"] == meeting_id]
    if not meetings:
        return None
    m = meetings[0]

    lines = [f"# {m['title']}\n"]
    lines.append(f"**Date:** {m['meeting_date']}")
    lines.append(f"**Status:** {m['status']}")
    if m.get("location"):
        lines.append(f"**Location:** {m['location']}")
    if m.get("called_by"):
        lines.append(f"**Called by:** {m['called_by']}")
    lines.append("")

    attendees = sorted(
        [a for a in data.get("board_attendees", []) if a["meeting_id"] == meeting_id],
        key=lambda a: (a.get("role", ""), a.get("person_name", ""))
    )
    if attendees:
        lines.append("## Attendees\n")
        lines.append("| Name | Role |")
        lines.append("|------|------|")
        for a in attendees:
            lines.append(f"| {a['person_name']} | {a.get('role', '')} |")
        lines.append("")

    minutes = sorted(
        [mi for mi in data.get("board_minutes", []) if mi["meeting_id"] == meeting_id],
        key=lambda mi: mi.get("seq", 0)
    )
    if minutes:
        lines.append("## Minutes\n")
        for mi in minutes:
            lines.append(f"{mi['seq']}. {mi['item_text']}\n")

    resolutions = sorted(
        [r for r in data.get("board_resolutions", []) if r["meeting_id"] == meeting_id],
        key=lambda r: r.get("id", "")
    )
    if resolutions:
        lines.append("## Resolutions\n")
        lines.append("| ID | Resolution | Status | Proposed by | Voted |")
        lines.append("|----|------------|--------|-------------|-------|")
        for r in resolutions:
            lines.append(
                f"| {r['id']} | {r['resolution_text']} "
                f"| {r['status'].upper()} "
                f"| {r.get('proposed_by', '')} "
                f"| {r.get('voted_date', '')} |"
            )
        lines.append("")

    return "\n".join(lines)


def cmd_pdf_meeting(meeting_id):
    if not meeting_id:
        die("usage: board pdf meeting <meeting-id>")
    md = meeting_markdown(meeting_id)
    if md is None:
        die(f"meeting '{meeting_id}' not found")
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{meeting_id}.pdf")
    generate_pdf(output, md)


def cmd_pdf_resolutions():
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "board-resolutions.pdf")

    data = datalib.load("board")
    meetings_map = {m["id"]: m for m in data.get("board_meetings", [])}
    resolutions = sorted(
        data.get("board_resolutions", []),
        key=lambda r: (meetings_map.get(r["meeting_id"], {}).get("meeting_date", ""), r.get("id", "")),
        reverse=True,
    )

    lines = [f"# Board Resolutions\n", f"Generated: {today}\n"]
    if not resolutions:
        lines.append("No resolutions recorded.")
    else:
        lines.append("| ID | Date | Resolution | Status | Proposed by | Voted |")
        lines.append("|----|------|------------|--------|-------------|-------|")
        for r in resolutions:
            meeting = meetings_map.get(r["meeting_id"], {})
            mdate = meeting.get("meeting_date", "")
            lines.append(
                f"| {r['id']} | {mdate} "
                f"| {r['resolution_text']} | {r['status'].upper()} "
                f"| {r.get('proposed_by', '')} "
                f"| {r.get('voted_date', '')} |"
            )

    generate_pdf(output, "\n".join(lines))


def cmd_pdf_pack():
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, "board-pack.pdf")

    data = datalib.load("board")
    meetings = sorted(
        data.get("board_meetings", []),
        key=lambda m: m.get("meeting_date", ""),
        reverse=True,
    )
    resolutions = data.get("board_resolutions", [])

    total = len(meetings)
    passed = len([r for r in resolutions if r.get("status") == "passed"])
    pending = len([r for r in resolutions if r.get("status") == "pending"])

    sections = [f"# Board Pack\n", f"Generated: {today}\n"]
    sections.append(f"**Meetings:** {total} | **Resolutions passed:** {passed} | **Pending:** {pending}\n")
    sections.append("---\n")

    for m in meetings:
        md = meeting_markdown(m["id"])
        if md:
            sections.append(md)
            sections.append("---\n")

    generate_pdf(output, "\n".join(sections))


def cmd_pdf(args):
    subcmd = args[0] if args else ""
    match subcmd:
        case "meeting":
            cmd_pdf_meeting(args[1] if len(args) > 1 else "")
        case "resolutions":
            cmd_pdf_resolutions()
        case "pack":
            cmd_pdf_pack()
        case _:
            print("Usage: board pdf <pack|meeting <id>|resolutions>")


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/board/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "meetings":
            cmd_meetings()
        case "meeting":
            if len(args) < 2:
                die("usage: board meeting <meeting-id>")
            cmd_meeting(args[1])
        case "resolutions":
            cmd_resolutions(args[1] if len(args) > 1 else "all")
        case "minutes":
            if len(args) < 2:
                die("usage: board minutes <meeting-id>")
            cmd_minutes(args[1])
        case "html":
            cmd_html(args[1:])
        case "pdf":
            cmd_pdf(args[1:])
        case "serve":
            cmd_serve(args[1:])
        case "new":
            cmd_new(args[1:])
        case "attend":
            cmd_attend(args[1:])
        case "minute":
            cmd_minute(args[1:])
        case "resolve":
            cmd_resolve(args[1:])
        case "vote":
            cmd_vote(args[1:])
        case "template":
            cmd_template(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
