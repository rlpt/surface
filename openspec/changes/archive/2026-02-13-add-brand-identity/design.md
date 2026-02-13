## Context

Brand data is scattered: colours live in `modules/marketing/themes/formabi.css`, the logo exists only as an EPS outside the repo, and the strap line isn't recorded anywhere. The module system already auto-discovers child directories under `modules/`, so adding a new `brand` module requires no flake changes.

## Goals / Non-Goals

**Goals:**
- Single source of truth for Formabi brand identity inside the repo
- Logo committed as SVG (vector, version-controlled, web-ready)
- Brand values exposed as nix attributes for downstream consumption

**Non-Goals:**
- Refactoring the marketing CSS theme to derive from brand module (future change)
- Font management or typography system
- Brand guidelines documentation

## Decisions

### Module structure: data-only module (no packages, no scripts)

The brand module exposes an `identity` attribute set but needs no packages or scripts. It follows the same `{ pkgs, ... }: { name; description; ... }` pattern as other modules but omits `packages` (defaults to empty). A `helpText` describes the available data.

**Alternatives considered:**
- JSON data file + nix importer — adds indirection for no benefit; nix attribute sets are already structured data
- Top-level `brand.nix` outside modules — breaks the module convention and auto-discovery

### Logo format: SVG converted from EPS

Convert the EPS to SVG using Ghostscript + Inkscape (or `eps2svg` tooling). SVG is the right choice: it's vector, web-native, git-diffable, and supported everywhere. The original EPS is not committed (large, legacy format).

**Alternatives considered:**
- Commit both EPS and SVG — EPS is 2.5MB and serves no purpose once SVG exists
- PNG — loses vector quality, requires multiple resolutions

### Colour values: hardcoded in nix, matching existing CSS

The `identity.colors` attribute set contains the same hex values currently in `formabi.css`. This is intentional duplication for now — the marketing module can be updated later to derive its CSS from these values.

## Risks / Trade-offs

- **[Dual source for colours]** → Accepted short-term; a follow-up change can make the CSS theme derive from the brand module
- **[EPS→SVG fidelity]** → Verify conversion preserves paths and colours; manual inspection after conversion
