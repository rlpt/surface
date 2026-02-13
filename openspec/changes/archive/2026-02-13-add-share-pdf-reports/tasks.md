## 1. Module dependencies

- [x] 1.1 Add `pandoc` and `typst` to `modules/shares/default.nix` packages list

## 2. PDF generation functions

- [x] 2.1 Add `generate_pdf()` helper to `shares.sh` that takes markdown on stdin and outputs PDF (using pandoc + typst)
- [x] 2.2 Add `--output` flag parsing to route PDF to file or stdout
- [x] 2.3 Implement `cmd_pdf_table` — generate markdown cap table report and convert to PDF
- [x] 2.4 Implement `cmd_pdf_history` — generate markdown history report and convert to PDF
- [x] 2.5 Implement `cmd_pdf_holder` — generate markdown holder statement (summary + filtered history) and convert to PDF

## 3. Command routing

- [x] 3.1 Add `pdf` subcommand to the case statement in `shares.sh` with sub-routing for `table`, `history`, `holder`
- [x] 3.2 Update `cmd_help` to include `pdf` subcommand and its report types

## 4. LLM context

- [x] 4.1 Update `modules/shares/CLAUDE.md` to document the `pdf` subcommand and its report types

## 5. Validation

- [x] 5.1 Run `shares pdf table --output /tmp/test-table.pdf` and verify valid PDF output
- [x] 5.2 Run `shares pdf history --output /tmp/test-history.pdf` and verify valid PDF output
- [x] 5.3 Run `shares pdf holder richard --output /tmp/test-holder.pdf` and verify valid PDF output
- [x] 5.4 Test `shares pdf holder unknown-id` produces error exit
- [x] 5.5 Test stdout mode: `shares pdf table > /tmp/test-stdout.pdf` and verify valid PDF
