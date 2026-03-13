#!/usr/bin/env python3
"""Board meetings, minutes, and resolutions — CLI backed by Dolt."""

import csv
import http.server
import io
import os
import subprocess
import sys
from datetime import date

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
SURFACE_DB = os.environ.get("SURFACE_DB", os.path.join(SURFACE_ROOT, ".surface-db"))

COLORS = {
    "primary": os.environ.get("BRAND_PRIMARY", "#6366f1"),
    "accent": os.environ.get("BRAND_ACCENT", "#a78bfa"),
    "bg": os.environ.get("BRAND_BG", "#0a0a1a"),
    "text": os.environ.get("BRAND_TEXT", "#e0e0e0"),
}


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_db():
    if not os.path.isdir(os.path.join(SURFACE_DB, ".dolt")):
        die("database not initialised — run 'data init'")


def dsql(query):
    check_db()
    subprocess.run(
        ["dolt", "sql", "-q", query],
        cwd=SURFACE_DB,
        check=True,
    )


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
    """Run a Dolt SQL query and return list of dicts."""
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    reader = csv.DictReader(io.StringIO(r.stdout))
    return list(reader)


def dsql_val(query):
    rows = dsql_rows(query)
    if not rows:
        return ""
    return list(rows[0].values())[0]


def dolt_commit(msg):
    check_db()
    subprocess.run(["dolt", "add", "."], cwd=SURFACE_DB, check=True)
    subprocess.run(["dolt", "commit", "-m", msg], cwd=SURFACE_DB, check=True)


# ---------------------------------------------------------------------------
# CLI commands — read
# ---------------------------------------------------------------------------

def cmd_meetings():
    rows = dsql_csv(
        "SELECT m.id, m.meeting_date, m.title, m.status, "
        "COUNT(DISTINCT a.person_name) AS attendees, "
        "COUNT(DISTINCT r.id) AS resolutions "
        "FROM board_meetings m "
        "LEFT JOIN board_attendees a ON a.meeting_id = m.id "
        "LEFT JOIN board_resolutions r ON r.meeting_id = m.id "
        "GROUP BY m.id, m.meeting_date, m.title, m.status "
        "ORDER BY m.meeting_date DESC"
    )
    if not rows:
        print("No meetings found.")
        return
    print(f"{'ID':<12} {'Date':<12} {'Status':<10} {'Attend':>6} {'Resol':>5}  Title")
    print("-" * 78)
    for row in rows:
        parts = row.split(",")
        if len(parts) >= 6:
            mid, mdate, title, status, att, res = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
            print(f"{mid:<12} {mdate:<12} {status:<10} {att:>6} {res:>5}  {title}")


def cmd_meeting(meeting_id):
    info = dsql_rows(
        f"SELECT id, meeting_date, title, location, status, called_by "
        f"FROM board_meetings WHERE id = '{meeting_id}'"
    )
    if not info:
        die(f"meeting '{meeting_id}' not found")
    m = info[0]
    print(f"Meeting: {m['title']}")
    print(f"Date:    {m['meeting_date']}")
    print(f"Status:  {m['status']}")
    if m.get("location"):
        print(f"Location: {m['location']}")
    if m.get("called_by"):
        print(f"Called by: {m['called_by']}")

    attendees = dsql_rows(
        f"SELECT person_name, role FROM board_attendees "
        f"WHERE meeting_id = '{meeting_id}' ORDER BY role, person_name"
    )
    if attendees:
        print(f"\nAttendees:")
        for a in attendees:
            role_str = f" ({a['role']})" if a.get("role") else ""
            print(f"  - {a['person_name']}{role_str}")

    minutes = dsql_rows(
        f"SELECT seq, item_text FROM board_minutes "
        f"WHERE meeting_id = '{meeting_id}' ORDER BY seq"
    )
    if minutes:
        print(f"\nMinutes:")
        for mi in minutes:
            print(f"  {mi['seq']}. {mi['item_text']}")

    resolutions = dsql_rows(
        f"SELECT id, resolution_text, status, proposed_by, voted_date "
        f"FROM board_resolutions WHERE meeting_id = '{meeting_id}' ORDER BY id"
    )
    if resolutions:
        print(f"\nResolutions:")
        for r in resolutions:
            status_mark = {"passed": "[PASSED]", "failed": "[FAILED]", "pending": "[PENDING]"}.get(r["status"], f"[{r['status']}]")
            proposer = f" (proposed by {r['proposed_by']})" if r.get("proposed_by") else ""
            print(f"  {r['id']}: {status_mark} {r['resolution_text']}{proposer}")


def cmd_resolutions(filter_status):
    where = ""
    if filter_status == "pending":
        where = "WHERE r.status = 'pending'"
    elif filter_status == "passed":
        where = "WHERE r.status = 'passed'"

    rows = dsql_rows(
        f"SELECT r.id, m.meeting_date, r.resolution_text, r.status, r.proposed_by, r.voted_date "
        f"FROM board_resolutions r "
        f"JOIN board_meetings m ON m.id = r.meeting_id "
        f"{where} ORDER BY m.meeting_date DESC, r.id"
    )
    if not rows:
        print("No resolutions found.")
        return
    print(f"{'ID':<12} {'Date':<12} {'Status':<10} Resolution")
    print("-" * 78)
    for r in rows:
        text = r["resolution_text"][:50] + ("..." if len(r["resolution_text"]) > 50 else "")
        print(f"{r['id']:<12} {r['meeting_date']:<12} {r['status']:<10} {text}")


def cmd_minutes(meeting_id):
    info = dsql_rows(
        f"SELECT title, meeting_date FROM board_meetings WHERE id = '{meeting_id}'"
    )
    if not info:
        die(f"meeting '{meeting_id}' not found")
    m = info[0]
    print(f"Minutes — {m['title']} ({m['meeting_date']})")
    print("=" * 60)

    minutes = dsql_rows(
        f"SELECT seq, item_text FROM board_minutes "
        f"WHERE meeting_id = '{meeting_id}' ORDER BY seq"
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
    # generate id from date
    mid = f"bm-{meeting_date}"
    dsql(
        f"INSERT INTO board_meetings (id, meeting_date, title, status) "
        f"VALUES ('{mid}', '{meeting_date}', '{title}', 'scheduled')"
    )
    dolt_commit(f"board: schedule meeting {mid} — {title}")
    print(f"Created meeting: {mid}")


def cmd_attend(args):
    if len(args) < 2:
        die("usage: board attend <meeting-id> <person> [role]")
    meeting_id = args[0]
    person = args[1]
    role = args[2] if len(args) > 2 else "director"
    dsql(
        f"INSERT INTO board_attendees (meeting_id, person_name, role) "
        f"VALUES ('{meeting_id}', '{person}', '{role}')"
    )
    dolt_commit(f"board: {person} attending {meeting_id} as {role}")
    print(f"Added {person} ({role}) to {meeting_id}")


def cmd_minute(args):
    if len(args) < 3:
        die("usage: board minute <meeting-id> <seq> \"text\"")
    meeting_id = args[0]
    seq = args[1]
    text = " ".join(args[2:])
    # escape single quotes for SQL
    text_escaped = text.replace("'", "''")
    dsql(
        f"INSERT INTO board_minutes (meeting_id, seq, item_text) "
        f"VALUES ('{meeting_id}', {seq}, '{text_escaped}')"
    )
    dolt_commit(f"board: minute {seq} for {meeting_id}")
    print(f"Added minute item {seq}")


def cmd_resolve(args):
    if len(args) < 2:
        die("usage: board resolve <meeting-id> \"resolution text\"")
    meeting_id = args[0]
    text = " ".join(args[1:])
    text_escaped = text.replace("'", "''")
    # auto-generate resolution id
    count = dsql_val(f"SELECT COUNT(*) FROM board_resolutions WHERE meeting_id = '{meeting_id}'")
    seq = int(count) + 1 if count else 1
    rid = f"{meeting_id}-r{seq}"
    dsql(
        f"INSERT INTO board_resolutions (id, meeting_id, resolution_text, status) "
        f"VALUES ('{rid}', '{meeting_id}', '{text_escaped}', 'pending')"
    )
    dolt_commit(f"board: propose resolution {rid}")
    print(f"Proposed resolution: {rid}")


def cmd_vote(args):
    if len(args) < 2:
        die("usage: board vote <resolution-id> passed|failed")
    rid = args[0]
    outcome = args[1]
    if outcome not in ("passed", "failed"):
        die("outcome must be 'passed' or 'failed'")
    dsql(
        f"UPDATE board_resolutions SET status = '{outcome}', "
        f"voted_date = CURRENT_DATE WHERE id = '{rid}'"
    )
    dolt_commit(f"board: resolution {rid} {outcome}")
    print(f"Resolution {rid}: {outcome}")


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
<footer>Generated {date.today().isoformat()} from Dolt</footer>
</body>
</html>"""


def build_meetings_page():
    total = dsql_val("SELECT COUNT(*) FROM board_meetings")
    passed = dsql_val("SELECT COUNT(*) FROM board_resolutions WHERE status = 'passed'")
    pending = dsql_val("SELECT COUNT(*) FROM board_resolutions WHERE status = 'pending'")

    cards = f"""
<p class="subtitle">Board governance — meetings, minutes, and resolutions</p>
<div class="cards">
  <div class="card"><div class="label">Meetings</div><div class="value">{esc(total)}</div></div>
  <div class="card"><div class="label">Resolutions Passed</div><div class="value">{esc(passed)}</div></div>
  <div class="card"><div class="label">Pending Resolutions</div><div class="value">{esc(pending)}</div></div>
</div>
"""

    meetings = dsql_rows(
        "SELECT m.id, m.meeting_date, m.title, m.status, m.location, m.called_by "
        "FROM board_meetings m ORDER BY m.meeting_date DESC"
    )

    body = cards
    for m in meetings:
        mid = m["id"]
        body += f'<h2><a href="{esc(mid)}.html" style="color: var(--accent); text-decoration: none;">'
        body += f'{esc(m["meeting_date"])} — {esc(m["title"])}</a></h2>\n'

        attendees = dsql_rows(
            f"SELECT person_name, role FROM board_attendees "
            f"WHERE meeting_id = '{mid}' ORDER BY role, person_name"
        )
        if attendees:
            body += "<p><strong>Attendees:</strong> "
            body += ", ".join(
                f'{esc(a["person_name"])} ({esc(a["role"])})'
                for a in attendees
            )
            body += "</p>\n"

        resolutions = dsql_rows(
            f"SELECT id, resolution_text, status FROM board_resolutions "
            f"WHERE meeting_id = '{mid}' ORDER BY id"
        )
        if resolutions:
            for r in resolutions:
                status_cls = f"status-{r['status']}"
                body += f'<div class="resolution-box">'
                body += f'<span class="res-id">{esc(r["id"])}</span> '
                body += f'<span class="{status_cls}">[{esc(r["status"].upper())}]</span> '
                body += f'{esc(r["resolution_text"])}</div>\n'

    return html_page("Board Meetings", body, "index")


def build_meeting_detail(meeting_id):
    info = dsql_rows(
        f"SELECT id, meeting_date, title, location, status, called_by "
        f"FROM board_meetings WHERE id = '{meeting_id}'"
    )
    if not info:
        return None
    m = info[0]

    body = f'<p class="subtitle">{esc(m["meeting_date"])} — {esc(m["status"])}'
    if m.get("location"):
        body += f' — {esc(m["location"])}'
    body += "</p>\n"

    attendees = dsql_rows(
        f"SELECT person_name, role FROM board_attendees "
        f"WHERE meeting_id = '{meeting_id}' ORDER BY role, person_name"
    )
    if attendees:
        body += "<h2>Attendees</h2>\n"
        body += html_table(attendees)

    minutes = dsql_rows(
        f"SELECT seq, item_text FROM board_minutes "
        f"WHERE meeting_id = '{meeting_id}' ORDER BY seq"
    )
    if minutes:
        body += "<h2>Minutes</h2>\n"
        for mi in minutes:
            body += f'<div class="minute-item"><span class="seq">{esc(mi["seq"])}.</span> '
            body += f'{esc(mi["item_text"])}</div>\n'

    resolutions = dsql_rows(
        f"SELECT id, resolution_text, status, proposed_by, voted_date "
        f"FROM board_resolutions WHERE meeting_id = '{meeting_id}' ORDER BY id"
    )
    if resolutions:
        body += "<h2>Resolutions</h2>\n"
        for r in resolutions:
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
    rows = dsql_rows(
        "SELECT r.id, m.meeting_date, m.title AS meeting, "
        "r.resolution_text, r.status, r.proposed_by, r.voted_date "
        "FROM board_resolutions r "
        "JOIN board_meetings m ON m.id = r.meeting_id "
        "ORDER BY m.meeting_date DESC, r.id"
    )

    body = '<p class="subtitle">All board resolutions — passed, pending, and failed</p>\n'

    if not rows:
        body += '<p class="empty">No resolutions recorded.</p>'
    else:
        for r in rows:
            status_cls = f"status-{r['status']}"
            body += f'<div class="resolution-box">'
            body += f'<span class="res-id">{esc(r["id"])} — {esc(r["meeting_date"])}</span><br>'
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
    meetings = dsql_rows("SELECT id FROM board_meetings ORDER BY meeting_date DESC")
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
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
