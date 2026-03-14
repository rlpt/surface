#!/usr/bin/env python3
"""Generate a read-only HTML dashboard from TOML data via datalib."""

import http.server
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")

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
# HTML generation
# ---------------------------------------------------------------------------

def html_table(rows, highlight_col=None):
    """Render a list of dicts as an HTML table."""
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
            cls = ' class="num"' if is_numeric(val) else cls
            out.append(f'<td{cls}>{esc(val)}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return "\n".join(out)


def esc(val):
    """Escape HTML."""
    return str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def is_numeric(val):
    if val is None or val == "":
        return False
    try:
        float(str(val).replace(",", ""))
        return True
    except ValueError:
        return False


def page(title, body, nav_active=""):
    """Wrap body HTML in a full page with nav."""
    nav_items = [
        ("index.html", "Overview"),
        ("cap-table.html", "Cap Table"),
        ("officers.html", "Officers"),
        ("compliance.html", "Compliance"),
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
<title>{esc(title)} — Formabi</title>
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
td.num {{
  text-align: right;
  font-variant-numeric: tabular-nums;
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


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------

def build_index():
    shares_data = datalib.load("shares")
    officers_data = datalib.load("officers")
    comp_data = datalib.load("compliance")

    # Shares metrics
    h = datalib.holdings(shares_data)
    holder_ids = set(r["holder_id"] for r in h)
    holders = len(holder_ids)
    shares_issued = sum(r["shares_held"] for r in h)

    # Officers metrics
    officers = [o for o in officers_data.get("officers", []) if not o.get("resigned_date")]
    num_officers = len(officers)

    # Compliance metrics
    upcoming = datalib.compliance_upcoming(comp_data)
    num_upcoming = len(upcoming)

    cards = f"""
<p class="subtitle">Company snapshot — read-only view of all company data</p>
<div class="cards">
  <div class="card"><div class="label">Shareholders</div><div class="value">{esc(holders)}</div></div>
  <div class="card"><div class="label">Shares Issued</div><div class="value">{esc(shares_issued)}</div></div>
  <div class="card"><div class="label">Officers</div><div class="value">{esc(num_officers)}</div></div>
  <div class="card"><div class="label">Compliance Due</div><div class="value">{esc(num_upcoming)}</div></div>
</div>
"""

    upcoming_display = [
        {
            "title": d["title"],
            "due_date": d["due_date"],
            "category": d["category"],
            "status": d["status"],
            "days_left": d["days_left"],
        }
        for d in upcoming[:5]
    ]

    # Recent changes
    changes = []
    for domain in ["shares", "officers", "compliance", "board"]:
        changes.extend(
            {**c, "domain": domain} for c in datalib.changelog(domain)[:5]
        )
    changes.sort(key=lambda c: c["date"], reverse=True)
    changes = changes[:10]

    body = cards
    body += "<h2>Upcoming Compliance Deadlines</h2>\n" + html_table(upcoming_display)
    if changes:
        body += "<h2>Recent Changes</h2>\n" + html_table(changes)
    return page("Overview", body, "index")


def build_cap_table():
    shares_data = datalib.load("shares")

    cap = datalib.cap_table(shares_data)
    cap_display = [
        {"holder": r["holder"], "class": r["class"], "held": r["held"], "pct": r["pct"]}
        for r in cap
    ]

    classes = datalib.class_availability(shares_data)
    classes_display = [
        {"class": r["class"], "authorised": r["authorised"], "issued": r["issued"], "available": r["available"]}
        for r in classes
    ]

    # Pools with members
    pools_raw = shares_data.get("pools", [])
    pool_members_raw = shares_data.get("pool_members", [])
    members_by_pool = {}
    for pm in pool_members_raw:
        members_by_pool.setdefault(pm["pool_name"], []).append(pm["holder_id"])
    pools_display = [
        {
            "name": p["name"],
            "class": p["share_class"],
            "budget": p["budget"],
            "members": ", ".join(members_by_pool.get(p["name"], [])),
        }
        for p in pools_raw
    ]

    # Share events
    events_raw = shares_data.get("share_events", [])
    events_display = [
        {
            "event_date": e["event_date"],
            "event_type": e["event_type"],
            "holder_id": e["holder_id"],
            "share_class": e["share_class"],
            "quantity": e["quantity"],
        }
        for e in sorted(events_raw, key=lambda e: (str(e.get("event_date", "")), e.get("id", 0)))
    ]

    body = '<p class="subtitle">Shareholdings, classes, pools, and event history</p>'
    body += "<h2>Holdings</h2>\n" + html_table(cap_display)
    body += "<h2>Share Classes</h2>\n" + html_table(classes_display)
    body += "<h2>Pools</h2>\n" + html_table(pools_display)
    body += "<h2>Event History</h2>\n" + html_table(events_display)
    return page("Cap Table", body, "cap-table")


def build_officers():
    data = datalib.load("officers")
    officers = data.get("officers", [])

    current = [
        {
            "name": o["person_name"],
            "role": o["role"],
            "appointed": o.get("appointed_date", ""),
        }
        for o in officers if not o.get("resigned_date")
    ]
    former = [
        {
            "name": o["person_name"],
            "role": o["role"],
            "appointed": o.get("appointed_date", ""),
            "resigned": o.get("resigned_date", ""),
        }
        for o in officers if o.get("resigned_date")
    ]

    body = '<p class="subtitle">Company officers — directors, secretary, and PSC</p>'
    body += "<h2>Current Officers</h2>\n" + html_table(current)
    if former:
        body += "<h2>Former Officers</h2>\n" + html_table(former)
    return page("Officers", body, "officers")


def build_compliance():
    data = datalib.load("compliance")
    upcoming = datalib.compliance_upcoming(data)

    upcoming_display = [
        {
            "title": d["title"],
            "due_date": d["due_date"],
            "category": d["category"],
            "status": d["status"],
            "days_left": d["days_left"],
        }
        for d in upcoming
    ]

    all_deadlines = [
        {
            "title": d["title"],
            "due_date": d["due_date"],
            "frequency": d["frequency"],
            "category": d["category"],
            "status": d.get("status", "upcoming"),
        }
        for d in data.get("deadlines", [])
    ]

    body = '<p class="subtitle">Statutory compliance deadlines and filing calendar</p>'
    body += "<h2>Upcoming (90 days)</h2>\n" + html_table(upcoming_display)
    body += "<h2>All Deadlines</h2>\n" + html_table(all_deadlines)
    return page("Compliance", body, "compliance")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_build(args):
    out_dir = args[0] if args else os.path.join(SURFACE_ROOT, "out", "dashboard")
    os.makedirs(out_dir, exist_ok=True)

    pages = {
        "index.html": build_index,
        "cap-table.html": build_cap_table,
        "officers.html": build_officers,
        "compliance.html": build_compliance,
    }

    for filename, builder in pages.items():
        path = os.path.join(out_dir, filename)
        with open(path, "w") as f:
            f.write(builder())
        print(f"  {filename}")

    print(f"\ndashboard built → {out_dir}/")


def cmd_serve(args):
    out_dir = args[0] if args else os.path.join(SURFACE_ROOT, "out", "dashboard")
    cmd_build([out_dir])
    print("\nserving on http://localhost:8000 (ctrl-c to stop)")
    os.chdir(out_dir)
    server = http.server.HTTPServer(("", 8000), http.server.SimpleHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/dashboard/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "build":
            cmd_build(args[1:])
        case "serve":
            cmd_serve(args[1:])
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
