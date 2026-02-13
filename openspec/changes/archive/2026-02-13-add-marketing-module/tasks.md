## 1. Copy source assets

- [x] 1.1 Create `modules/marketing/` directory
- [x] 1.2 Copy `decks/` from `../deck/decks/` (company.md, investor.md, product.md)
- [x] 1.3 Copy `themes/` from `../deck/themes/` (formabi.css, handbook.css, handbook.html, viewer.css, viewer.html, viewer.js)
- [x] 1.4 Copy `handbook/` from `../deck/handbook/` (00-introduction.md, 01-how-we-work.md)
- [x] 1.5 Copy `diagrams/` from `../deck/diagrams/` (data-engine.mmd, form-lifecycle.mmd, rbac.mmd)
- [x] 1.6 Copy `investor/` from `../deck/investor/` (ip-assignment-agreement.md, one-pager.md, seis-eis-advance-assurance.md)

## 2. Module definition

- [x] 2.1 Create `modules/marketing/default.nix` with name, description, and packages (marp-cli, mermaid-cli, pandoc)

## 3. CLI script

- [x] 3.1 Create `scripts/marketing.sh` with subcommand routing (serve, build, handbook-build, handbook-serve, diagrams, help)
- [x] 3.2 Implement `serve` subcommand — marp live-preview server with theme-set
- [x] 3.3 Implement `build` subcommand — render decks to `out/marketing/`
- [x] 3.4 Implement `handbook-build` subcommand — pandoc render to `out/marketing/handbook/`
- [x] 3.5 Implement `handbook-serve` subcommand — build + python HTTP server
- [x] 3.6 Implement `diagrams` subcommand — mmdc render of .mmd to `out/marketing/diagrams/`

## 4. Flake integration

- [x] 4.1 Add `marketing` script derivation to `flake.nix` (writeShellScriptBin, add to buildInputs)

## 5. Halp integration

- [x] 5.1 Add "Marketing" section to `scripts/halp.sh` listing all marketing subcommands

## 6. Verification

- [x] 6.1 Enter devShell and confirm `marketing` is on PATH and module appears in banner
- [x] 6.2 Run `marketing help` and verify all subcommands are listed
- [x] 6.3 Run `halp` and verify Marketing section appears
