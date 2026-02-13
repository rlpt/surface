## Context

Surface uses a child-module auto-discovery system: any directory under `modules/` with a `default.nix` is picked up by the flake and its packages are added to the devShell. The accounts module plugs into this existing mechanism — no changes to the flake or module-detection logic needed.

The company currently has no structured bookkeeping in the repo. hledger is a CLI-first, double-entry bookkeeping tool that stores journals as plain text files. This makes it git-friendly, LLM-readable, and nix-packageable.

## Goals / Non-Goals

**Goals:**
- Accounts module is auto-discovered and hledger is available in the shell
- Journal files live in `modules/accounts/books/` with clear conventions
- LLMs can read journals, append transactions, and run hledger queries
- Chart of accounts reflects Formabi's actual expense/revenue categories

**Non-Goals:**
- Multi-currency support (add when needed)
- Invoicing (separate concern)
- Bank feed automation (manual or LLM-assisted paste is fine at current scale)
- Payroll calculations (done by payroll provider — just record journal entries)
- Historical data backfill (Phase 2 — separate change after scaffold exists)

## Decisions

### hledger over alternatives
- **vs ledger** — hledger has better error messages, stricter parsing, and `--output-format json`
- **vs beancount** — hledger is in nixpkgs without Python dependency overhead, simpler file format
- **vs SaaS (Xero, etc)** — no auth, no API keys, the LLM reads/writes files and runs CLI commands directly. Fits the "repo is the company" model.

### One journal include tree, year-file splitting
- `main.journal` includes `accounts.journal` + per-year files
- Keeps individual files small and diffable
- Year boundaries are natural for financial reporting

### Chart of accounts scoped to Formabi's current operations
- Starts with known categories: Tide bank, business CC, infra/tools/admin expenses, sales/consulting revenue
- New accounts added to `accounts.journal` as needed — no schema migration

## Risks / Trade-offs

- **Journal files committed to git** — financial data is visible to anyone with repo access. Acceptable for a small team where all members are trusted. If the team grows, accounts could move to a private module repo.
- **No automated bank import** — manual entry or LLM-assisted paste. Fine at current transaction volume. Revisit if volume grows significantly.
- **hledger version drift** — pinned via nixpkgs, so version is consistent across machines. Journal format is stable across hledger versions.
