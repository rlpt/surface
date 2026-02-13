## Why

The shares module can query and export cap table data to the terminal and CSV, but investors, solicitors, and board members expect polished PDF documents. Generating share history, current allocation summaries, and individual holder statements as PDFs makes it easy to share these outside the repo without giving people shell access.

## What Changes

- New `shares pdf` subcommand with report types: `table`, `history`, `holder <id>`
- PDF generation pipeline using pandoc + typst (lightweight, no LaTeX dependency)
- New nix packages added to the shares module: `pandoc` and `typst`
- Reports include company name, generation date, and formatted tables

## Capabilities

### New Capabilities
- `share-pdf-export`: PDF report generation from share ledger data — cap table summary, full event history, and per-holder statements

### Modified Capabilities
- `share-reports`: Adding `pdf` subcommand to the existing shares shell command

## Impact

- `modules/shares/default.nix` gains `pandoc` and `typst` as packages
- `scripts/shares.sh` gains new `pdf` subcommand with report type routing
- No changes to ledger format or existing subcommands
- Generated PDFs are output files, not tracked in git
