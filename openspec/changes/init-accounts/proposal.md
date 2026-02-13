## Why

Formabi needs plain-text bookkeeping that lives in the repo alongside everything else. Currently there's no accounts module — financials are tracked outside the system (spreadsheets, Xero, or not at all). Adding hledger-based bookkeeping means the company's books are version-controlled, LLM-queryable, and available in the shell like any other module.

## What Changes

- Add a new `accounts` child module under `modules/accounts/` with hledger as its package
- Create the journal file structure: `main.journal`, `accounts.journal`, and per-year files
- Define journal conventions (date format, payee style, posting indent, currency format)
- Establish LLM usage patterns for transaction entry, categorisation, bulk import, and querying
- Add shell integration (accounts shortcut script, halp updates, LLM context)

## Capabilities

### New Capabilities
- `accounts`: Plain-text double-entry bookkeeping using hledger — module scaffold, journal structure, conventions, LLM interaction patterns, and shell integration

### Modified Capabilities

_(none — this is a new standalone module that plugs into the existing module-detection system without changing it)_

## Impact

- **modules/**: New `accounts/` child directory with `default.nix` and `books/` subdirectory
- **Nix shell**: hledger package added to devShell when module is present (via existing auto-discovery)
- **scripts/**: New `accounts` shortcut script
- **Shell banner**: Module count increases by one (handled automatically by module-detection)
- **Dependencies**: `pkgs.hledger` from nixpkgs (already available, no new flake inputs)
