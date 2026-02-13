## Why

Brand identity data — logo, colours, strap line — lives nowhere canonical in surface. The logo exists only as an EPS file outside the repo, colours are embedded in a Marp CSS theme, and the strap line isn't recorded at all. A company-as-code repo should own these assets in version control as structured, nix-accessible data so every module (marketing decks, PDFs, onboarding) can reference a single source of truth.

## What Changes

- Convert the Formabi EPS logo to SVG and commit it to the repo
- Create a `brand` module that exposes identity data: logo path, brand colours, and strap line
- Expose brand values as nix-accessible attributes so other modules can reference them
- Keep the marketing module's CSS theme as a downstream consumer (no breaking changes)

## Capabilities

### New Capabilities

- `brand-identity`: Canonical store for Formabi brand assets (SVG logo, colour palette, strap line) exposed as nix module attributes

### Modified Capabilities

_(none — the marketing theme CSS continues to work as-is; it just gains an upstream source of truth)_

## Impact

- **New directory**: `modules/brand/` with logo SVG, identity data, and `default.nix`
- **Nix flake**: Automatically discovered as a new module (existing auto-discovery, no flake changes)
- **Downstream**: Marketing themes can optionally be updated later to derive colours from the brand module — out of scope for this change
