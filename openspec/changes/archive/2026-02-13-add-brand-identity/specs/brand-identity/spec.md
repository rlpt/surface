## ADDED Requirements

### Requirement: Brand module structure
The system SHALL include a `modules/brand/default.nix` that exposes `name = "brand"`, a `description`, and an `identity` attribute set containing the brand data. The module SHALL be auto-discovered by the existing module directory scanner. The module SHALL NOT require any additional packages.

#### Scenario: Module appears in devShell
- **WHEN** a user enters the surface devShell with `nix develop`
- **THEN** the shell banner lists `brand` as a loaded module

### Requirement: SVG logo asset
The module directory SHALL contain the Formabi logo as an SVG file at `modules/brand/logo.svg`. The SVG SHALL be a vector conversion of the canonical EPS source, preserving all paths and colours.

#### Scenario: Logo file exists and is valid SVG
- **WHEN** the module is installed
- **THEN** `modules/brand/logo.svg` exists and contains a valid SVG document with vector paths (not an embedded raster image)

### Requirement: Brand identity data
The `default.nix` SHALL expose an `identity` attribute set containing:
- `name` — the company name (`"Formabi"`)
- `strapLine` — the company strap line
- `colors.primary` — the primary brand colour hex value
- `colors.accent` — the accent brand colour hex value
- `colors.bg` — the background colour hex value
- `colors.text` — the text colour hex value
- `logoPath` — a string path to the SVG logo file relative to the repo root

#### Scenario: Identity attributes are accessible in nix
- **WHEN** a nix expression imports the brand module
- **THEN** `identity.name` evaluates to `"Formabi"` and `identity.colors.primary` evaluates to a hex colour string and `identity.logoPath` evaluates to `"modules/brand/logo.svg"`

### Requirement: Brand module help text
The module SHALL expose a `helpText` string describing available brand data. The `halp` command SHALL display a "Brand" section listing the brand module's purpose.

#### Scenario: Brand section in halp output
- **WHEN** a user runs `halp`
- **THEN** the output includes a "Brand" section describing the brand identity data available in the module
