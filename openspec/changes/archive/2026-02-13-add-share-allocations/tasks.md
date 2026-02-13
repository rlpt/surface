## 1. Module scaffolding

- [x] 1.1 Create `modules/shares/default.nix` with name, description, and packages (no extra nix deps needed)
- [x] 1.2 Create `modules/shares/cap-table/` directory with `classes.ledger`, `holders.ledger`, and `events.ledger` seed files
- [x] 1.3 Create `modules/shares/CLAUDE.md` with ledger format docs, file layout, event types, and workflow

## 2. Seed data

- [x] 2.1 Add initial share class declaration in `classes.ledger` (e.g. `class ordinary £0.01 1000`)
- [x] 2.2 Add Richard as founding shareholder in `holders.ledger`
- [x] 2.3 Add founding share grant event in `events.ledger`

## 3. Shell command — shares script

- [x] 3.1 Create `scripts/shares.sh` with subcommand routing (table, export, holders, history, check, help)
- [x] 3.2 Implement `shares check` — validate classes/holders refs, no negatives, no over-allocation
- [x] 3.3 Implement `shares table` — compute current cap table from events and display formatted
- [x] 3.4 Implement `shares export` — output cap table as CSV to stdout with header row
- [x] 3.5 Implement `shares holders` — list all holders with total shareholding
- [x] 3.6 Implement `shares history [holder]` — display events chronologically, optional holder filter

## 4. Flake integration

- [x] 4.1 Add `shares` script to `flake.nix` (writeShellScriptBin + add to basePackages)
- [x] 4.2 Verify module auto-discovery picks up shares module (check shell banner)

## 5. Validation

- [x] 5.1 Run `shares check` against seed data — confirm exit 0
- [x] 5.2 Run `shares table` and verify output matches seed allocations
- [x] 5.3 Run `shares export > /tmp/test.csv` and verify valid CSV with correct columns
- [x] 5.4 Test `shares history` and `shares history richard` for correct filtering
