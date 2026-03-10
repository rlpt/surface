# Shares Module — LLM Context

Share allocation tracking stored in Dolt. Data lives in the `share_classes`, `holders`, `share_events`, `pools`, and `pool_members` tables.

## Tables

- `share_classes` — class definitions (name, nominal_value, nominal_currency, authorised)
- `holders` — shareholder declarations (id, display_name)
- `share_events` — all events chronologically (event_date, event_type, holder_id, share_class, quantity, optional vesting fields)
- `pools` — pool budgets (name, share_class, budget)
- `pool_members` — pool membership (pool_name, holder_id)

## Views

- `holdings` — computed current holdings per holder/class
- `cap_table` — full cap table with percentages
- `class_availability` — issued vs authorised per class

## Workflow: granting shares

```bash
shares add-holder alice "Alice Smith"      # add holder if new
shares grant alice ordinary 500            # grant + validate + dolt commit
```

Or with vesting (use SQL directly):
```sql
data sql "INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity, vesting_start, vesting_months, vesting_cliff_months)
  VALUES ('2026-03-09', 'grant', 'alice', 'ordinary', 500, '2026-03-09', 48, 12);"
```

## Workflow: transferring shares

```bash
shares transfer richard alice ordinary 100   # transfer-out + transfer-in pair, auto-committed
```

## Google Sheets export

Requires two env vars:
- `GOOGLE_SERVICE_ACCOUNT_KEY` — path to service account JSON key file
- `SHARES_SHEET_ID` — the spreadsheet ID from the Google Sheets URL

```bash
shares push all          # push all tabs (Cap Table, History, Holders, Pools)
shares push table        # push just the cap table
```

The service account must have Editor access to the spreadsheet.

## Commands

Read:
- `shares table` — current cap table with percentages
- `shares export` — CSV output
- `shares holders` — list all shareholders with totals
- `shares history [holder]` — all events (optionally filtered)
- `shares pools` — pool budgets, usage, and availability
- `shares check` — validate consistency
- `shares brief` — compact context dump for agent warm-up

Write:
- `shares grant <holder> <class> <qty>` — grant shares (validates + commits)
- `shares transfer <from> <to> <class> <qty>` — transfer shares
- `shares add-holder <id> "Name"` — add a shareholder
- `shares add-pool <name> <class> <budget>` — create a pool
- `shares pool-add <pool> <holder>` — add holder to pool

Export:
- `shares pdf table|history|holder <id>` — generate PDF
- `shares push table|history|holders|pools|all` — push to Google Sheets
