#!/usr/bin/env python3
"""Push shares data to Google Sheets."""

import csv
import io
import json
import os
import subprocess
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_env(name):
    val = os.environ.get(name)
    if not val:
        print(f"error: {name} not set", file=sys.stderr)
        sys.exit(1)
    return val


def get_service():
    key_path = get_env("GOOGLE_SERVICE_ACCOUNT_KEY")
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def dsql_csv(query):
    db = os.environ.get("SURFACE_DB", os.path.join(os.environ["SURFACE_ROOT"], ".surface-db"))
    result = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=db, capture_output=True, text=True, check=True,
    )
    reader = csv.reader(io.StringIO(result.stdout))
    return list(reader)


def write_sheet(service, spreadsheet_id, sheet_name, rows):
    """Clear and write rows to a named sheet tab."""
    # Ensure the sheet tab exists
    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    existing = [s["properties"]["title"] for s in meta.get("sheets", [])]
    if sheet_name not in existing:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": [{"addSheet": {"properties": {"title": sheet_name}}}]},
        ).execute()

    range_name = f"{sheet_name}!A1"
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id, range=f"{sheet_name}",
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption="RAW", body={"values": rows},
    ).execute()
    print(f"Wrote {len(rows)} rows to '{sheet_name}'")


def push_table(service, spreadsheet_id):
    rows = dsql_csv("""
        SELECT
            ct.holder AS Holder,
            ct.class AS Class,
            ct.held AS Held,
            CONCAT(ct.pct, '%') AS Percentage,
            ct.held AS Vested
        FROM cap_table ct;
    """)
    # Add total row
    total = dsql_csv("SELECT COALESCE(SUM(shares_held), 0) FROM holdings;")
    rows.append(["", "", total[1][0] if len(total) > 1 else "0", "", ""])
    write_sheet(service, spreadsheet_id, "Cap Table", rows)


def push_history(service, spreadsheet_id):
    rows = dsql_csv("""
        SELECT
            se.event_date AS Date,
            se.event_type AS Event,
            h.display_name AS Holder,
            se.share_class AS Class,
            se.quantity AS Qty
        FROM share_events se
        JOIN holders h ON h.id = se.holder_id
        ORDER BY se.event_date, se.id;
    """)
    write_sheet(service, spreadsheet_id, "History", rows)


def push_holders(service, spreadsheet_id):
    rows = dsql_csv("""
        SELECT
            h.id AS ID,
            h.display_name AS Name,
            COALESCE(SUM(ho.shares_held), 0) AS Total
        FROM holders h
        LEFT JOIN holdings ho ON ho.holder_id = h.id
        GROUP BY h.id, h.display_name
        ORDER BY h.id;
    """)
    write_sheet(service, spreadsheet_id, "Holders", rows)


def push_pools(service, spreadsheet_id):
    rows = dsql_csv("""
        SELECT
            p.name AS Pool,
            p.share_class AS Class,
            p.budget AS Budget,
            COALESCE(issued.total, 0) AS Issued,
            p.budget - COALESCE(issued.total, 0) AS Available,
            COALESCE(members.list, '-') AS Members
        FROM pools p
        LEFT JOIN (
            SELECT pm.pool_name, SUM(COALESCE(ho.shares_held, 0)) AS total
            FROM pool_members pm
            LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id
                AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name)
            GROUP BY pm.pool_name
        ) issued ON issued.pool_name = p.name
        LEFT JOIN (
            SELECT pm.pool_name,
                GROUP_CONCAT(CONCAT(h.display_name, ' (', COALESCE(ho.shares_held, 0), ')') SEPARATOR ', ') AS list
            FROM pool_members pm
            JOIN holders h ON h.id = pm.holder_id
            LEFT JOIN holdings ho ON ho.holder_id = pm.holder_id
                AND ho.share_class = (SELECT share_class FROM pools WHERE name = pm.pool_name)
            GROUP BY pm.pool_name
        ) members ON members.pool_name = p.name
        ORDER BY p.name;
    """)
    write_sheet(service, spreadsheet_id, "Pools", rows)


def push_all(service, spreadsheet_id):
    push_table(service, spreadsheet_id)
    push_history(service, spreadsheet_id)
    push_holders(service, spreadsheet_id)
    push_pools(service, spreadsheet_id)


COMMANDS = {
    "table": push_table,
    "history": push_history,
    "holders": push_holders,
    "pools": push_pools,
    "all": push_all,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Usage: shares push <table|history|holders|pools|all>")
        print()
        print("Pushes cap table data to Google Sheets.")
        print()
        print("Required env vars:")
        print("  GOOGLE_SERVICE_ACCOUNT_KEY  Path to service account JSON key")
        print("  SHARES_SHEET_ID             Google Sheets spreadsheet ID")
        sys.exit(1)

    spreadsheet_id = get_env("SHARES_SHEET_ID")
    service = get_service()
    COMMANDS[sys.argv[1]](service, spreadsheet_id)


if __name__ == "__main__":
    main()
