#!/usr/bin/env python3
"""CRM — contacts, deals, pipeline (dolt)"""

import os
import subprocess
import sys
from datetime import date

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
SURFACE_DB = os.environ.get("SURFACE_DB", os.path.join(SURFACE_ROOT, ".surface-db"))


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


def dsql_val(query):
    """Return a single scalar value from a query."""
    rows = dsql_csv(query)
    return rows[0] if rows else ""


def dolt_commit(msg):
    subprocess.run(["dolt", "add", "."], cwd=SURFACE_DB, check=True)
    subprocess.run(["dolt", "commit", "-m", msg], cwd=SURFACE_DB, check=True)


# --- Read commands ---


def cmd_pipeline():
    count = dsql_val(
        "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('closed-won', 'closed-lost');"
    )
    if count == "0":
        print("No open deals in pipeline.")
        return

    dsql("SELECT * FROM pipeline;")
    total = dsql_val(
        "SELECT COALESCE(SUM(value_gbp), 0) FROM deals "
        "WHERE stage NOT IN ('closed-won', 'closed-lost');"
    )
    print(f"\nTotal pipeline value: £{total}")


def cmd_contacts(filter_=""):
    if filter_ == "active":
        dsql(
            "SELECT id, company, name, stage, "
            "next_action_date AS next_date, next_action "
            "FROM contacts "
            "WHERE stage IN ('lead', 'prospect') "
            "ORDER BY next_action_date ASC, company;"
        )
    else:
        dsql(
            "SELECT id, company, name, stage, "
            "last_contacted, next_action_date AS next_date "
            "FROM contacts ORDER BY company, name;"
        )


def cmd_stale():
    dsql("SELECT * FROM stale_contacts;")


def cmd_find(term):
    if not term:
        die("usage: crm find <term>")
    esc = term.replace("'", "''")
    dsql(
        "SELECT DISTINCT c.id, c.company, c.name, c.stage, c.last_contacted "
        "FROM contacts c "
        "LEFT JOIN tags t ON t.contact_id = c.id "
        f"WHERE c.company LIKE '%{esc}%' "
        f"OR c.name LIKE '%{esc}%' "
        f"OR t.tag LIKE '%{esc}%' "
        "ORDER BY c.company;"
    )


def cmd_history(contact):
    if not contact:
        die("usage: crm history <contact-id>")
    cname = dsql_val(f"SELECT name FROM contacts WHERE id = '{contact}';")
    if not cname:
        die(f"unknown contact: {contact}")
    print(f"Contact: {cname}\n")
    dsql(
        "SELECT interaction_date AS date, channel, direction, summary, follow_up "
        f"FROM interactions WHERE contact_id = '{contact}' "
        "ORDER BY interaction_date DESC, id DESC;"
    )


def cmd_log(contact, summary):
    if not contact or not summary:
        die('usage: crm log <contact-id> "summary"')

    cname = dsql_val(f"SELECT name FROM contacts WHERE id = '{contact}';")
    if not cname:
        die(f"unknown contact: {contact}")

    channels = {
        "1": "email",
        "2": "call",
        "3": "meeting",
        "4": "demo",
        "5": "slack",
        "6": "event",
        "7": "other",
    }
    print("Channel:")
    print("  1) email    2) call     3) meeting")
    print("  4) demo     5) slack    6) event    7) other")
    ch = input("Select [1-7]: ").strip()
    channel = channels.get(ch)
    if not channel:
        die("invalid channel")

    direction = input("Direction (inbound/outbound) [outbound]: ").strip() or "outbound"
    if direction not in ("inbound", "outbound"):
        die("direction must be inbound or outbound")

    follow_up = input("Follow-up (optional): ").strip()

    today = date.today().isoformat()
    esc_summary = summary.replace("'", "''")
    esc_follow = follow_up.replace("'", "''")

    dsql(
        "INSERT INTO interactions "
        "(contact_id, interaction_date, channel, direction, summary, follow_up) "
        f"VALUES ('{contact}', '{today}', '{channel}', '{direction}', "
        f"'{esc_summary}', '{esc_follow}');"
    )
    dsql(f"UPDATE contacts SET last_contacted = '{today}' WHERE id = '{contact}';")

    if follow_up:
        next_date = input("Next action date (YYYY-MM-DD, or enter to skip): ").strip()
        if next_date:
            dsql(
                f"UPDATE contacts SET next_action = '{esc_follow}', "
                f"next_action_date = '{next_date}' WHERE id = '{contact}';"
            )

    dolt_commit(f"log {channel} with {cname} ({contact})")
    print(f"\nLogged {channel} with {cname}")


def cmd_deals(filter_=""):
    if filter_ == "won":
        dsql(
            "SELECT d.id, c.company, d.title, d.value_gbp AS value, "
            "d.recurring, d.closed_date "
            "FROM deals d JOIN contacts c ON c.id = d.contact_id "
            "WHERE d.stage = 'closed-won' ORDER BY d.closed_date DESC;"
        )
    elif filter_ == "lost":
        dsql(
            "SELECT d.id, c.company, d.title, d.value_gbp AS value, "
            "d.closed_date, d.lost_reason "
            "FROM deals d JOIN contacts c ON c.id = d.contact_id "
            "WHERE d.stage = 'closed-lost' ORDER BY d.closed_date DESC;"
        )
    else:
        dsql(
            "SELECT d.id, c.company, d.title, d.stage, "
            "d.value_gbp AS value, d.recurring, d.opened_date "
            "FROM deals d JOIN contacts c ON c.id = d.contact_id "
            "WHERE d.stage NOT IN ('closed-won', 'closed-lost') "
            "ORDER BY FIELD(d.stage, 'qualifying', 'proposal', 'negotiation'), "
            "d.value_gbp DESC;"
        )


def cmd_digest():
    today = date.today().isoformat()
    print(f"# CRM Digest — {today}\n")

    print("## Pipeline")
    open_count = dsql_val(
        "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('closed-won', 'closed-lost');"
    )
    if open_count == "0":
        print("No open deals.")
    else:
        dsql("SELECT * FROM pipeline;")
        total = dsql_val(
            "SELECT COALESCE(SUM(value_gbp), 0) FROM deals "
            "WHERE stage NOT IN ('closed-won', 'closed-lost');"
        )
        print(f"Total pipeline: £{total}")
    print()

    print("## Stale Contacts (14+ days)")
    stale_count = dsql_val("SELECT COUNT(*) FROM stale_contacts;")
    if stale_count == "0":
        print("None — all contacts are fresh.")
    else:
        dsql("SELECT * FROM stale_contacts;")
    print()

    print("## Next Actions")
    actions_count = dsql_val(
        "SELECT COUNT(*) FROM contacts "
        "WHERE next_action IS NOT NULL AND next_action_date IS NOT NULL "
        "AND stage IN ('lead', 'prospect');"
    )
    if actions_count == "0":
        print("No upcoming actions.")
    else:
        dsql(
            "SELECT id, company, next_action_date AS date, next_action "
            "FROM contacts "
            "WHERE next_action IS NOT NULL AND next_action_date IS NOT NULL "
            "AND stage IN ('lead', 'prospect') "
            "ORDER BY next_action_date ASC;"
        )
    print()

    print("## Customers")
    cust_count = dsql_val(
        "SELECT COUNT(*) FROM customers WHERE status IN ('active', 'onboarding');"
    )
    mrr = dsql_val(
        "SELECT COALESCE(SUM(mrr_gbp), 0) FROM customers "
        "WHERE status IN ('active', 'onboarding');"
    )
    print(f"Active customers: {cust_count} — MRR: £{mrr}")
    renewal_count = dsql_val("SELECT COUNT(*) FROM renewals_due;")
    if renewal_count != "0":
        dsql("SELECT * FROM renewals_due;")
    print()

    print("## Recent Activity (7 days)")
    recent_count = dsql_val(
        "SELECT COUNT(*) FROM interactions "
        "WHERE interaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY);"
    )
    if recent_count == "0":
        print("No interactions in the last 7 days.")
    else:
        dsql(
            "SELECT i.interaction_date AS date, c.company, i.channel, i.summary "
            "FROM interactions i "
            "JOIN contacts c ON c.id = i.contact_id "
            "WHERE i.interaction_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY) "
            "ORDER BY i.interaction_date DESC;"
        )


def cmd_forecast():
    print("# Revenue Forecast\n")
    open_count = dsql_val(
        "SELECT COUNT(*) FROM deals WHERE stage NOT IN ('closed-won', 'closed-lost');"
    )
    if open_count == "0":
        print("No open deals to forecast.")
        return

    dsql(
        "SELECT d.stage, COUNT(*) AS deals, SUM(d.value_gbp) AS total, "
        "CASE d.stage "
        "WHEN 'qualifying' THEN ROUND(SUM(d.value_gbp) * 0.2, 2) "
        "WHEN 'proposal' THEN ROUND(SUM(d.value_gbp) * 0.5, 2) "
        "WHEN 'negotiation' THEN ROUND(SUM(d.value_gbp) * 0.8, 2) "
        "END AS weighted "
        "FROM deals d "
        "WHERE d.stage NOT IN ('closed-won', 'closed-lost') "
        "GROUP BY d.stage "
        "ORDER BY FIELD(d.stage, 'qualifying', 'proposal', 'negotiation');"
    )

    weighted = dsql_val(
        "SELECT ROUND(SUM(CASE stage "
        "WHEN 'qualifying' THEN value_gbp * 0.2 "
        "WHEN 'proposal' THEN value_gbp * 0.5 "
        "WHEN 'negotiation' THEN value_gbp * 0.8 END), 2) "
        "FROM deals WHERE stage NOT IN ('closed-won', 'closed-lost');"
    )
    print(f"\nWeighted forecast: £{weighted}")

    won = dsql_val(
        "SELECT COALESCE(SUM(value_gbp), 0) FROM deals WHERE stage = 'closed-won';"
    )
    print(f"\nClosed-won to date: £{won}")


def cmd_customers(filter_=""):
    if filter_ == "active":
        dsql(
            "SELECT id, company, pricing_plan, mrr, contract_end, contacts "
            "FROM customer_overview WHERE status = 'active' "
            "ORDER BY mrr DESC;"
        )
    elif filter_ == "all":
        dsql("SELECT * FROM customer_overview ORDER BY status, company;")
    else:
        dsql(
            "SELECT id, company, pricing_plan, status, mrr, contract_end, contacts "
            "FROM customer_overview ORDER BY status, company;"
        )

    total = dsql_val(
        "SELECT COALESCE(SUM(mrr_gbp), 0) FROM customers "
        "WHERE status IN ('active', 'onboarding');"
    )
    count = dsql_val(
        "SELECT COUNT(*) FROM customers WHERE status IN ('active', 'onboarding');"
    )
    print(f"\n{count} active customers — MRR: £{total}")


def cmd_customer(cust_id):
    if not cust_id:
        die("usage: crm customer <customer-id>")

    company = dsql_val(f"SELECT company FROM customers WHERE id = '{cust_id}';")
    if not company:
        die(f"unknown customer: {cust_id}")

    print(f"# {company}\n")
    dsql(
        "SELECT id, company, pricing_plan, status, mrr_gbp AS mrr, "
        "contract_start, contract_end, instance_id, notes "
        f"FROM customers WHERE id = '{cust_id}';"
    )

    print("\n## Contacts")
    dsql(
        "SELECT id, name, email, role, contact_role "
        f"FROM contacts WHERE customer_id = '{cust_id}' ORDER BY contact_role, name;"
    )

    print("\n## Deals")
    dsql(
        "SELECT d.id, d.title, d.stage, d.value_gbp AS value, d.recurring "
        "FROM deals d JOIN contacts c ON c.id = d.contact_id "
        f"WHERE c.customer_id = '{cust_id}' ORDER BY d.opened_date DESC;"
    )

    print("\n## Recent Interactions")
    dsql(
        "SELECT i.interaction_date AS date, c.name, i.channel, i.summary "
        "FROM interactions i "
        "JOIN contacts c ON c.id = i.contact_id "
        f"WHERE c.customer_id = '{cust_id}' "
        "ORDER BY i.interaction_date DESC LIMIT 10;"
    )


def cmd_renewals():
    count = dsql_val("SELECT COUNT(*) FROM renewals_due;")
    if count == "0":
        print("No renewals due in the next 90 days.")
        return

    dsql("SELECT * FROM renewals_due;")
    total = dsql_val(
        "SELECT COALESCE(SUM(mrr_gbp), 0) FROM customers "
        "WHERE status IN ('active', 'churning') "
        "AND contract_end IS NOT NULL "
        "AND contract_end <= DATE_ADD(CURRENT_DATE, INTERVAL 90 DAY);"
    )
    print(f"\nAt-risk MRR: £{total}")


def cmd_help():
    print("crm — contacts, deals, pipeline, customers (dolt)")
    print()
    print("Usage: crm <command> [args]")
    print()
    print("Read:")
    print("  pipeline                               Pipeline overview")
    print("  contacts [active]                      List contacts (or active only)")
    print("  customers [active|all]                 List customer organisations")
    print("  customer <customer-id>                 Customer detail (contacts, deals, activity)")
    print("  stale                                  Contacts not contacted in 14+ days")
    print("  renewals                               Renewals due in next 90 days")
    print("  find <term>                            Search by company/name/tag")
    print("  history <contact-id>                   Interaction history")
    print("  deals [won|lost]                       List deals (open, won, or lost)")
    print()
    print("Write:")
    print('  log <contact-id> "summary"             Log an interaction (guided)')
    print()
    print("Reports:")
    print("  digest                                 Weekly digest")
    print("  forecast                               Revenue forecast from pipeline")
    print()
    print('For raw operations, use: data sql "..."')


# --- Routing ---

def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        case "pipeline":
            cmd_pipeline()
        case "contacts":
            cmd_contacts(args[1] if len(args) > 1 else "")
        case "customers":
            cmd_customers(args[1] if len(args) > 1 else "")
        case "customer":
            cmd_customer(args[1] if len(args) > 1 else "")
        case "renewals":
            cmd_renewals()
        case "stale":
            cmd_stale()
        case "find":
            cmd_find(args[1] if len(args) > 1 else "")
        case "history":
            cmd_history(args[1] if len(args) > 1 else "")
        case "log":
            cmd_log(
                args[1] if len(args) > 1 else "",
                args[2] if len(args) > 2 else "",
            )
        case "deals":
            cmd_deals(args[1] if len(args) > 1 else "")
        case "digest":
            cmd_digest()
        case "forecast":
            cmd_forecast()
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
