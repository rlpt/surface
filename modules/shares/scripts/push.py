#!/usr/bin/env python3
"""Push shares data to Google Sheets."""

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib

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


def write_sheet(service, spreadsheet_id, sheet_name, rows):
    """Clear and write rows to a named sheet tab."""
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
    share_data = datalib.load("shares")
    ct = datalib.cap_table(share_data)
    total = sum(r["held"] for r in ct)

    rows = [["Holder", "Class", "Held", "Percentage", "Vested"]]
    for r in ct:
        rows.append([r["holder"], r["class"], str(r["held"]), f"{r['pct']}%", str(r["held"])])
    rows.append(["", "", str(total), "", ""])
    write_sheet(service, spreadsheet_id, "Cap Table", rows)


def push_history(service, spreadsheet_id):
    share_data = datalib.load("shares")
    holders_map = {h["id"]: h["display_name"] for h in share_data.get("holders", [])}
    events = share_data.get("share_events", [])

    rows = [["Date", "Event", "Holder", "Class", "Qty"]]
    for e in events:
        rows.append([
            str(e["event_date"]),
            e["event_type"],
            holders_map.get(e["holder_id"], e["holder_id"]),
            e["share_class"],
            str(e["quantity"]),
        ])
    write_sheet(service, spreadsheet_id, "History", rows)


def push_holders(service, spreadsheet_id):
    share_data = datalib.load("shares")
    h = datalib.holdings(share_data)
    holdings_map = defaultdict(int)
    for r in h:
        holdings_map[r["holder_id"]] += r["shares_held"]

    rows = [["ID", "Name", "Total"]]
    for holder in sorted(share_data.get("holders", []), key=lambda x: x["id"]):
        rows.append([holder["id"], holder["display_name"], str(holdings_map.get(holder["id"], 0))])
    write_sheet(service, spreadsheet_id, "Holders", rows)


def push_pools(service, spreadsheet_id):
    share_data = datalib.load("shares")
    h = datalib.holdings(share_data)
    holders_map = {r["id"]: r["display_name"] for r in share_data.get("holders", [])}
    holdings_map = {}
    for r in h:
        holdings_map[(r["holder_id"], r["share_class"])] = r["shares_held"]

    rows = [["Pool", "Class", "Budget", "Issued", "Available", "Members"]]
    for pool in sorted(share_data.get("pools", []), key=lambda x: x["name"]):
        members = [
            pm for pm in share_data.get("pool_members", [])
            if pm["pool_name"] == pool["name"]
        ]
        issued = sum(
            holdings_map.get((pm["holder_id"], pool["share_class"]), 0)
            for pm in members
        )
        member_strs = [
            f"{holders_map.get(pm['holder_id'], pm['holder_id'])} ({holdings_map.get((pm['holder_id'], pool['share_class']), 0)})"
            for pm in members
        ]
        rows.append([
            pool["name"],
            pool["share_class"],
            str(pool["budget"]),
            str(issued),
            str(pool["budget"] - issued),
            ", ".join(member_strs) if member_strs else "-",
        ])
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
