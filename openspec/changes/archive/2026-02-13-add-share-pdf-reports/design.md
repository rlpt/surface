## Context

The shares module already has subcommands (`table`, `export`, `holders`, `history`) that compute cap table state from plain-text ledger files. PDF generation builds on this — the same data, rendered as formatted documents instead of terminal output.

The codebase follows a plain-text-first philosophy. Markdown is the standard document format. The sales role already uses `marp-cli` for presentations, establishing a precedent for document generation tooling.

## Goals / Non-Goals

**Goals:**
- Generate professional PDF reports from share ledger data
- Support three report types: cap table summary, full history, individual holder statement
- Keep the pipeline simple: markdown → PDF via pandoc + typst
- PDFs include company name, date, and clean formatting

**Non-Goals:**
- Custom branding, logos, or complex visual design (plain professional layout is sufficient)
- Interactive or web-based reports
- Automatic PDF generation on ledger changes (manual invocation only)
- PDF templates or user-configurable layouts

## Decisions

### Pandoc + typst pipeline (not LaTeX, not wkhtmltopdf)

The shares script generates markdown, then pipes through `pandoc --pdf-engine=typst` to produce PDF.

**Rationale**: Typst is ~50MB vs ~2GB for a full LaTeX distribution. Pandoc handles markdown-to-PDF conversion cleanly. Both are in nixpkgs. The intermediate markdown is human-readable and consistent with the repo's document format.

**Alternatives considered**:
- LaTeX via pandoc: Excellent output but enormous dependency, slow to build
- wkhtmltopdf: Requires a headless browser, heavier than typst
- Groff: Very lightweight but limited table support, less readable input format
- Typst directly: Would require learning typst markup; pandoc lets us stay in markdown

### Subcommand under `shares pdf` (not separate script)

Add `shares pdf <type> [args]` as a new subcommand rather than a separate `shares-pdf` script.

**Rationale**: Keeps the single `shares` command as the entry point. Follows the existing subcommand pattern. The pdf subcommand reuses the same data loading helpers already in shares.sh.

### Output to stdout by default, with --output flag

`shares pdf table` writes PDF to stdout (for piping). `shares pdf table --output cap-table.pdf` writes to a named file. Default filename suggested in help.

**Rationale**: Stdout output is Unix-idiomatic and composable. Named output is more practical for PDFs (you usually want a file). Supporting both is straightforward.

## Risks / Trade-offs

- **[Package size]** → pandoc + typst add ~100MB to the nix closure. Mitigation: acceptable for a dev shell; these are compile-time deps not runtime server deps.
- **[Formatting limits]** → Pandoc's markdown-to-typst pipeline may not support advanced table formatting. Mitigation: the data is simple tabular content; basic tables are well-supported.
- **[Platform consistency]** → PDF rendering should be identical across macOS and Linux. Mitigation: typst produces deterministic output regardless of platform.
