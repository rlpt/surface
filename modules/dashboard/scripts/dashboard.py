#!/usr/bin/env python3
"""Generate a read-only HTML dashboard from Dolt data."""

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


def query_rows(sql):
    """Run a Dolt SQL query and return list of dicts."""
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", sql],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return []
    reader = csv.DictReader(io.StringIO(r.stdout))
    return list(reader)


def query_val(sql):
    """Run a query and return a single scalar value."""
    rows = query_rows(sql)
    if not rows:
        return ""
    return list(rows[0].values())[0]


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
        ("accounts.html", "Accounts"),
        ("crm.html", "CRM"),
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
<footer>Generated {date.today().isoformat()} from Dolt</footer>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------

def build_index():
    holders = query_val("SELECT COUNT(*) FROM holders")
    shares_issued = query_val(
        "SELECT COALESCE(SUM(shares_held), 0) FROM holdings"
    )
    customers = query_val("SELECT COUNT(*) FROM customers")
    mrr = query_val(
        "SELECT COALESCE(SUM(mrr_gbp), 0) FROM customers WHERE status = 'active'"
    )
    open_deals = query_val(
        "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('closed-won', 'closed-lost')"
    )
    contacts = query_val("SELECT COUNT(*) FROM contacts")
    accounts = query_val("SELECT COUNT(*) FROM accounts")
    txns = query_val("SELECT COUNT(*) FROM transactions")

    cards = f"""
<p class="subtitle">Company snapshot — read-only view of all Dolt data</p>
<div class="cards">
  <div class="card"><div class="label">Shareholders</div><div class="value">{esc(holders)}</div></div>
  <div class="card"><div class="label">Shares Issued</div><div class="value">{esc(shares_issued)}</div></div>
  <div class="card"><div class="label">Customers</div><div class="value">{esc(customers)}</div></div>
  <div class="card"><div class="label">Monthly Revenue</div><div class="value">&pound;{esc(mrr)}</div></div>
  <div class="card"><div class="label">Open Deals</div><div class="value">{esc(open_deals)}</div></div>
  <div class="card"><div class="label">Contacts</div><div class="value">{esc(contacts)}</div></div>
  <div class="card"><div class="label">Accounts</div><div class="value">{esc(accounts)}</div></div>
  <div class="card"><div class="label">Transactions</div><div class="value">{esc(txns)}</div></div>
</div>
"""

    renewals = query_rows(
        "SELECT company, pricing_plan AS plan, status, mrr, days_left "
        "FROM renewals_due ORDER BY days_left LIMIT 5"
    )
    stale = query_rows(
        "SELECT company, name, stage, last_contacted, next_action "
        "FROM stale_contacts LIMIT 5"
    )

    body = cards
    body += "<h2>Upcoming Renewals</h2>\n" + html_table(renewals)
    body += "<h2>Stale Contacts</h2>\n" + html_table(stale)
    return page("Overview", body, "index")


def build_cap_table():
    cap = query_rows("SELECT holder, class, held, pct FROM cap_table")
    classes = query_rows(
        "SELECT class, authorised, issued, available FROM class_availability"
    )
    pools = query_rows(
        "SELECT p.name, p.share_class AS class, p.budget, "
        "GROUP_CONCAT(pm.holder_id) AS members "
        "FROM pools p LEFT JOIN pool_members pm ON pm.pool_name = p.name "
        "GROUP BY p.name, p.share_class, p.budget"
    )
    events = query_rows(
        "SELECT event_date, event_type, holder_id, share_class, quantity "
        "FROM share_events ORDER BY event_date, id"
    )

    body = '<p class="subtitle">Shareholdings, classes, pools, and event history</p>'
    body += "<h2>Holdings</h2>\n" + html_table(cap)
    body += "<h2>Share Classes</h2>\n" + html_table(classes)
    body += "<h2>Pools</h2>\n" + html_table(pools)
    body += "<h2>Event History</h2>\n" + html_table(events)
    return page("Cap Table", body, "cap-table")


def build_accounts():
    balances = query_rows(
        "SELECT account_path, account_type, balance, currency "
        "FROM account_balances ORDER BY account_type, account_path"
    )
    recent_txns = query_rows(
        "SELECT t.txn_date, t.payee, t.description, "
        "p.account_path, p.amount, p.currency "
        "FROM transactions t "
        "JOIN postings p ON p.txn_id = t.id "
        "ORDER BY t.txn_date DESC, t.id DESC LIMIT 30"
    )

    body = '<p class="subtitle">Double-entry bookkeeping — balances and transactions</p>'
    body += "<h2>Account Balances</h2>\n" + html_table(balances)
    body += "<h2>Recent Transactions</h2>\n" + html_table(recent_txns)
    return page("Accounts", body, "accounts")


def build_crm():
    overview = query_rows(
        "SELECT company, pricing_plan, status, mrr, contract_end, contacts, won_value "
        "FROM customer_overview ORDER BY company"
    )
    pipeline = query_rows("SELECT stage, deals, total_value, companies FROM pipeline")
    contacts = query_rows(
        "SELECT c.company, c.name, c.role, c.contact_role, c.stage, "
        "c.last_contacted, c.next_action_date, c.next_action "
        "FROM contacts c ORDER BY c.company, c.name"
    )
    deals = query_rows(
        "SELECT d.title, c.company, d.stage, d.value_gbp AS value, "
        "d.recurring, d.opened_date, d.closed_date "
        "FROM deals d JOIN contacts c ON c.id = d.contact_id "
        "ORDER BY d.opened_date DESC"
    )

    body = '<p class="subtitle">Customers, contacts, deals, and pipeline</p>'
    body += "<h2>Customers</h2>\n" + html_table(overview)
    body += "<h2>Pipeline</h2>\n" + html_table(pipeline)
    body += "<h2>Contacts</h2>\n" + html_table(contacts)
    body += "<h2>Deals</h2>\n" + html_table(deals)
    return page("CRM", body, "crm")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_build(args):
    out_dir = args[0] if args else os.path.join(SURFACE_ROOT, "out", "dashboard")
    os.makedirs(out_dir, exist_ok=True)

    pages = {
        "index.html": build_index,
        "cap-table.html": build_cap_table,
        "accounts.html": build_accounts,
        "crm.html": build_crm,
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
