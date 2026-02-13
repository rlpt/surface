## Why

The `deck` repo contains all Formabi marketing collateral — pitch decks (Marp), company handbook (Pandoc), investor documents, and Mermaid diagrams — as a standalone Nix flake. Consolidating it into surface as a `marketing` module brings it under the company-as-code umbrella, eliminates a separate repo, and lets it share surface's devShell, module auto-discovery, and scripting patterns.

## What Changes

- Copy `decks/`, `themes/`, `handbook/`, `diagrams/`, and `investor/` from `../deck` into `modules/marketing/`
- Create `modules/marketing/default.nix` following the surface module convention (name, description, packages)
- Add a `marketing` shell script (like `shares`, `accounts`) exposing subcommands: `serve`, `build`, `handbook-build`, `handbook-serve`, `diagrams`
- Wire the script into `flake.nix` so it's available in the devShell
- Update `halp` to list the new marketing commands
- **BREAKING**: The standalone `deck` flake's Nix build outputs (diagrams, handbook, viewer, default) are not being ported — only the dev workflow scripts and source assets move over. Nix package builds can be added later if needed.

## Capabilities

### New Capabilities

- `marketing-module`: Surface module housing pitch decks, handbook, investor docs, diagrams, and themes with a unified CLI (`marketing <subcommand>`)

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **New files**: `modules/marketing/` directory tree (decks, themes, handbook, diagrams, investor, default.nix)
- **Modified files**: `flake.nix` (add marketing script), `scripts/halp.sh` (add marketing commands)
- **New file**: `scripts/marketing.sh`
- **Dependencies**: `marp-cli`, `mermaid-cli`, `pandoc` added to the marketing module's packages (already available in nixpkgs)
- **No effect** on existing modules (shares, accounts, hello)
