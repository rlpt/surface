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

## Workflow: adding a share event

1. Check valid holders: `data sql "SELECT id, display_name FROM holders;"`
2. Check valid classes: `data sql "SELECT name, authorised FROM share_classes;"`
3. Insert the event:
   ```sql
   INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity)
     VALUES ('2026-03-09', 'grant', 'alice', 'ordinary', 500);
   ```
4. Validate: `shares check`
5. Commit: `data commit -m "grant 500 ordinary to alice"`

Event types: `grant`, `transfer-in`, `transfer-out`, `cancel`

For vesting:
```sql
INSERT INTO share_events (event_date, event_type, holder_id, share_class, quantity, vesting_start, vesting_months, vesting_cliff_months)
  VALUES ('2026-03-09', 'grant', 'alice', 'ordinary', 500, '2026-03-09', 48, 12);
```

## Workflow: adding a holder

```sql
INSERT INTO holders (id, display_name) VALUES ('alice', 'Alice Smith');
```

## Common commands

- `shares table` — current cap table with percentages
- `shares export` — CSV output
- `shares holders` — list all shareholders with totals
- `shares history [holder]` — all events (optionally filtered)
- `shares pools` — pool budgets, usage, and availability
- `shares check` — validate consistency
- `shares brief` — compact context dump for agent warm-up
- `shares pdf table` — cap table as PDF
- `shares pdf history` — event history as PDF
- `shares pdf holder <id>` — individual holder statement as PDF
