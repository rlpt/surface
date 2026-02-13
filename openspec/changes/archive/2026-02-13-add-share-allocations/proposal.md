## Why

Formabi needs to track founder and early investor share allocations as the company takes shape. Currently there is no way to record who holds what percentage of equity, track share classes, or produce investor-facing reports. As fundraising conversations begin, having a single source of truth for the cap table — version-controlled alongside the rest of the company — is essential.

## What Changes

- New `shares` module providing plain-text share allocation tracking
- Cap table data stored as structured journal/ledger files within the module
- Shell command (`shares`) to query allocations, compute dilution, and export reports
- Spreadsheet export (CSV) for sharing cap table snapshots with investors, accountants, and legal

## Capabilities

### New Capabilities
- `share-ledger`: Plain-text share allocation records — share classes, holders, grants, and vesting schedules
- `share-reports`: Shell commands to query the cap table and export CSV spreadsheets for investors

### Modified Capabilities
<!-- No existing spec requirements are changing -->

## Impact

- New `modules/shares/` directory with `default.nix` (auto-discovered by existing module system)
- New shell command `shares` added via `flake.nix` script generation
- No changes to existing modules or accounts — equity accounting remains separate from share register
- No new nix dependencies beyond what is already available (csvkit or similar for export)
