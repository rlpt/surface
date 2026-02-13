## Context

Formabi tracks company operations as code. The accounts module already handles financial bookkeeping via hledger. Now the company needs to track equity — who holds shares, what class, how many, and any vesting conditions. This information is needed for investor conversations, legal compliance, and internal clarity.

The existing module system auto-discovers child directories under `modules/`, each providing a `default.nix` with name, description, and packages. Shell scripts are wired in `flake.nix`. The accounts module provides a strong pattern to follow.

## Goals / Non-Goals

**Goals:**
- Track share allocations in plain-text, version-controlled files
- Support multiple share classes (ordinary, preference, etc.) and holders
- Provide a `shares` shell command for querying the cap table
- Export cap table as CSV for investors and accountants
- Include LLM context so the AI can help manage share records

**Non-Goals:**
- Real-time share trading or transfer processing
- Integration with Companies House or other registrars (manual for now)
- Complex option/warrant modelling (can be added later)
- Replacing legal share certificates — this is an internal record

## Decisions

### Plain-text ledger format (not JSON or database)

Use a simple plain-text ledger format similar to hledger journals. Each share event (grant, transfer, cancellation) is a dated entry.

**Rationale**: Matches the accounts module pattern. Human-readable, git-diffable, LLM-friendly. No database dependencies.

**Alternatives considered**:
- JSON: Structured but harder to read/diff, verbose for sequential events
- SQLite: Powerful queries but breaks the plain-text philosophy
- hledger commodities: Could model shares as commodities but semantics are awkward — share classes aren't currencies

### Dedicated module (not part of accounts)

Create a separate `modules/shares/` module rather than extending accounts.

**Rationale**: Share register and financial accounts are legally distinct records. The accounts module tracks money flows; the shares module tracks ownership. Separation keeps both focused and avoids coupling.

### Simple shell script with subcommands

The `shares` command will be a bash script that reads the ledger files and computes the current state. Subcommands: `table`, `export`, `holders`, `history`.

**Rationale**: Matches the `accounts` pattern (thin shell wrapper). Bash + awk/jq is sufficient for the small data volumes involved. No additional nix dependencies needed beyond coreutils.

### CSV export format

Export as standard CSV with columns: holder, share_class, shares_held, percentage, vesting_status, notes. This is the format investors and accountants expect.

**Rationale**: CSV is universally readable — Excel, Google Sheets, Numbers all open it. No special tooling needed.

## Risks / Trade-offs

- **[Manual consistency]** → The ledger format is not validated by an external tool like hledger validates journals. Mitigation: the `shares check` subcommand will verify totals balance against declared share capital.
- **[Scale limits]** → Bash parsing won't scale to thousands of transactions. Mitigation: early-stage companies have few share events; this can be revisited if needed.
- **[No legal authority]** → This is an internal record, not a legal register. Mitigation: document this clearly; use as input for legal filings, not as a replacement.
