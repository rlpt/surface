## Context

Surface is a company-as-code monorepo with auto-discovered Nix modules under `modules/`. Each module provides a `default.nix` with `name`, `description`, and `packages`. Shell scripts in `scripts/` expose CLI subcommands (e.g., `shares`, `accounts`), wired into `flake.nix` as `writeShellScriptBin` derivations available in the devShell.

The `deck` repo at `../deck` is a standalone Nix flake containing Marp slide decks, a Pandoc handbook, Mermaid diagrams, investor documents, and custom themes. It has its own devenv.nix with scripts for serving, building, and previewing content.

## Goals / Non-Goals

**Goals:**
- Move all `deck` source assets into `modules/marketing/` so they're part of surface
- Provide a `marketing` CLI with subcommands matching the original deck workflow (serve, build, handbook, diagrams)
- Follow existing module conventions exactly (auto-discovery via `default.nix`, script in `scripts/`)
- Make `halp` aware of the new commands

**Non-Goals:**
- Porting the `deck` flake's Nix package outputs (diagrams, handbook, viewer derivations) — those are reproducible build artifacts that can be added later
- Migrating the `deck` repo's git history — this is a file copy, not a subtree merge
- Modifying the theme or content of any deck/handbook/investor document
- Adding the `deck` flake as a Nix input to surface

## Decisions

### File layout: flat copy into `modules/marketing/`

Copy the content directories directly:
```
modules/marketing/
  default.nix          # module definition
  decks/               # Marp markdown (company.md, investor.md, product.md)
  themes/              # CSS + HTML templates (formabi.css, handbook.css/html, viewer.*)
  handbook/            # Pandoc markdown (00-introduction.md, 01-how-we-work.md)
  diagrams/            # Mermaid .mmd files
  investor/            # Legal / investor docs (one-pager, SEIS, IP assignment)
```

**Why**: Mirrors the existing `deck` structure. The module auto-discovery reads `modules/marketing/default.nix` — subdirectories are invisible to the framework.

### Script pattern: `scripts/marketing.sh` with subcommand routing

Follow the `shares.sh` pattern: a case-dispatch script with subcommands. The `SURFACE_ROOT` env var locates the module assets at runtime.

Subcommands:
- `marketing serve` — `marp --server` on decks with theme-set
- `marketing build` — render decks to `out/marketing/`
- `marketing handbook-build` — pandoc build to `out/marketing/handbook/`
- `marketing handbook-serve` — build + python HTTP server
- `marketing diagrams` — mmdc render of .mmd files to `out/marketing/diagrams/`
- `marketing help` — usage text

**Why**: Consistent with existing patterns. Users type `marketing serve` just like `shares table`.

### Output directory: `out/marketing/`

Build artifacts go under `out/marketing/` (decks, handbook, diagrams subdirectories) rather than a top-level `out/`. This scopes the marketing output and avoids collision with other modules.

**Why**: The `out/` directory is gitignored. Each module should own its own output namespace.

### Module packages

The `default.nix` declares `marp-cli`, `mermaid-cli`, and `pandoc` — the same tools the deck repo used.

**Why**: These are the minimal tools needed for all marketing content types.

## Risks / Trade-offs

- **Chrome/Puppeteer for mermaid-cli**: The deck repo's devenv.nix auto-detected Chrome for mermaid-cli's Puppeteer. The marketing module won't have this setup automatically. → Mitigation: Document in CLAUDE.md that `PUPPETEER_EXECUTABLE_PATH` may need to be set. The diagrams subcommand is a nice-to-have — decks and handbook work without Chrome.
- **No Nix build outputs**: Users who relied on `nix build` in the deck repo won't have that. → Mitigation: The dev workflow scripts cover the common use cases. Package outputs can be a follow-up change.
- **Theme path coupling**: The themes directory must be at a known path relative to the script. → Mitigation: The script uses `$SURFACE_ROOT/modules/marketing/themes` which is stable.
