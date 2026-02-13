### Requirement: Marketing module auto-discovery
The system SHALL include a `modules/marketing/default.nix` that exposes `name = "marketing"`, a `description`, and a `packages` list containing `marp-cli`, `mermaid-cli`, and `pandoc`. The module SHALL be auto-discovered by the existing `modules/default.nix` directory scanner.

#### Scenario: Module appears in devShell
- **WHEN** a user enters the surface devShell with `nix develop`
- **THEN** the shell banner lists `marketing` as a loaded module and `marp-cli`, `mermaid-cli`, and `pandoc` are available on `$PATH`

### Requirement: Marketing CLI with subcommand routing
The system SHALL provide a `marketing` shell command available in the devShell. It SHALL accept subcommands: `serve`, `build`, `handbook-build`, `handbook-serve`, `diagrams`, and `help`. Unknown subcommands or no arguments SHALL display help text.

#### Scenario: Running marketing with no arguments
- **WHEN** a user runs `marketing` with no arguments
- **THEN** the system prints usage help listing all available subcommands

#### Scenario: Running an unknown subcommand
- **WHEN** a user runs `marketing unknown`
- **THEN** the system prints usage help

### Requirement: Deck live preview
The `marketing serve` command SHALL start a Marp live-preview server for all decks in `modules/marketing/decks/` using the custom themes from `modules/marketing/themes/`.

#### Scenario: Starting live preview
- **WHEN** a user runs `marketing serve`
- **THEN** Marp starts an HTTP server with hot reload serving all `.md` files from the decks directory with the formabi theme applied

### Requirement: Deck build
The `marketing build` command SHALL render all Marp decks from `modules/marketing/decks/` to HTML files in `out/marketing/`.

#### Scenario: Building decks
- **WHEN** a user runs `marketing build`
- **THEN** each `.md` file in `modules/marketing/decks/` is compiled to an HTML slide deck in `out/marketing/` using the formabi theme

### Requirement: Handbook build
The `marketing handbook-build` command SHALL render the handbook markdown files from `modules/marketing/handbook/` to HTML using pandoc, outputting to `out/marketing/handbook/`.

#### Scenario: Building handbook
- **WHEN** a user runs `marketing handbook-build`
- **THEN** all `.md` files in `modules/marketing/handbook/` are compiled to a single-page HTML document at `out/marketing/handbook/handbook.html`

### Requirement: Handbook serve
The `marketing handbook-serve` command SHALL build the handbook and then serve it via a local HTTP server.

#### Scenario: Serving handbook
- **WHEN** a user runs `marketing handbook-serve`
- **THEN** the handbook is built to `out/marketing/handbook/` and a local HTTP server starts serving it

### Requirement: Diagram build
The `marketing diagrams` command SHALL render all Mermaid `.mmd` files from `modules/marketing/diagrams/` to SVG files in `out/marketing/diagrams/`.

#### Scenario: Building diagrams
- **WHEN** a user runs `marketing diagrams`
- **THEN** each `.mmd` file in `modules/marketing/diagrams/` is compiled to an SVG in `out/marketing/diagrams/`

### Requirement: Marketing content files
The module directory SHALL contain the source assets copied from the deck repo: `decks/` (company.md, investor.md, product.md), `themes/` (formabi.css, handbook.css, handbook.html, viewer.css, viewer.html, viewer.js), `handbook/` (00-introduction.md, 01-how-we-work.md), `diagrams/` (data-engine.mmd, form-lifecycle.mmd, rbac.mmd), and `investor/` (ip-assignment-agreement.md, one-pager.md, seis-eis-advance-assurance.md).

#### Scenario: All source assets present
- **WHEN** the module is installed
- **THEN** all content directories (decks, themes, handbook, diagrams, investor) exist under `modules/marketing/` with their files intact

### Requirement: Halp integration
The `halp` command SHALL list all marketing subcommands in a "Marketing" section.

#### Scenario: Marketing commands in halp output
- **WHEN** a user runs `halp`
- **THEN** the output includes a "Marketing" section listing `marketing serve`, `marketing build`, `marketing handbook-build`, `marketing handbook-serve`, and `marketing diagrams`

### Requirement: Flake integration
The `flake.nix` SHALL define and wire a `marketing` script derivation into the devShell's `buildInputs`, following the same pattern used for `shares` and `accounts`.

#### Scenario: Marketing script in flake
- **WHEN** `flake.nix` is evaluated
- **THEN** the `marketing` script is built from `scripts/marketing.sh` and included in the devShell's `buildInputs`
