# Shares Module — LLM Context

Plain-text share allocation tracking. Ledger files live at `modules/shares/cap-table/`.

## File layout

- `classes.ledger` — share class declarations (name, nominal value, authorised count)
- `holders.ledger` — shareholder declarations (id, display name)
- `events.ledger` — all share events in chronological order
- `pools.ledger` — pool budgets and member assignments

## Ledger formats

### classes.ledger

```
class <name> <nominal-value> <authorised-count>
```

Example: `class ordinary £0.01 1000`

### holders.ledger

```
holder <id> <display-name>
```

Example: `holder richard Richard Targett`

### events.ledger

```
<date> <event-type> <holder-id> <share-class> <quantity>
    vesting <start-date> <months> <cliff-months>
```

Event types: `grant`, `transfer-in`, `transfer-out`, `cancel`

The vesting line is optional and indented with 4 spaces. If omitted, shares are fully vested immediately.

Example:
```
2024-06-01 grant richard ordinary 500
    vesting 2024-06-01 48 12
```

### pools.ledger

```
pool <name> <share-class> <budget>
    member <holder-id>
```

The member line is optional and indented with 4 spaces. Pools without members track unallocated reserves.

Example:
```
pool supporter ordinary 1000
    member mark
    member emma
```

## Workflow: adding a share event

1. Read `classes.ledger` to find valid share class names
2. Read `holders.ledger` to find valid holder IDs (add new holder first if needed)
3. Read `events.ledger` to see existing events and match style
4. Append the new event to `events.ledger`
5. Run `shares check` to validate

Always follow this order. Never skip the validation step.

## Common shares commands

All commands use the `shares` shell alias.

- `shares table` — current cap table with percentages and vesting
- `shares export` — CSV output to stdout (pipe to file for spreadsheet)
- `shares holders` — list all shareholders with totals
- `shares history` — all events chronologically
- `shares history <holder-id>` — events for a specific holder
- `shares pools` — show pool budgets, usage, and remaining availability
- `shares check` — validate ledger consistency
- `shares pdf table --output cap-table.pdf` — cap table as PDF
- `shares pdf history --output history.pdf` — full event history as PDF
- `shares pdf holder <id> --output statement.pdf` — individual holder statement as PDF

PDF reports use pandoc + typst. Omit `--output` to write PDF to stdout.
