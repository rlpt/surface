### Requirement: Shares module declaration
The shares module SHALL declare itself as a child module under `modules/shares/default.nix` with name, description, and packages. The module SHALL be auto-discovered by the existing module-detection system.

#### Scenario: Module is discovered
- **WHEN** `modules/shares/default.nix` exists with name `shares`, description, and packages
- **THEN** the shell banner includes "shares" in the module list and SURFACE_MODULES contains "shares"

### Requirement: Share ledger file structure
The module SHALL contain a `cap-table/` directory with plain-text ledger files: `classes.ledger` declaring share classes, `holders.ledger` declaring shareholders, and `events.ledger` recording all share events (grants, transfers, cancellations).

#### Scenario: Files exist and are readable
- **WHEN** the shares module is initialised
- **THEN** `modules/shares/cap-table/classes.ledger`, `holders.ledger`, and `events.ledger` exist and are non-empty with header comments explaining the format

### Requirement: Share class declarations
The `classes.ledger` file SHALL declare each share class with a name, nominal value, and total authorised shares. Format: one class per line as `class <name> <nominal-value> <authorised-count>`.

#### Scenario: Declaring ordinary shares
- **WHEN** `classes.ledger` contains `class ordinary £0.01 1000`
- **THEN** the system recognises a share class named "ordinary" with nominal value £0.01 and 1000 authorised shares

#### Scenario: Multiple share classes
- **WHEN** `classes.ledger` contains entries for "ordinary" and "preference"
- **THEN** both classes are available for use in share events

### Requirement: Shareholder declarations
The `holders.ledger` file SHALL declare each shareholder with an identifier and display name. Format: one holder per line as `holder <id> <display-name>`.

#### Scenario: Declaring a holder
- **WHEN** `holders.ledger` contains `holder richard Richard Targett`
- **THEN** the system recognises "richard" as a valid holder with display name "Richard Targett"

### Requirement: Share event recording
The `events.ledger` file SHALL record share events in chronological order. Each event is a dated entry with format: `<date> <event-type> <holder-id> <share-class> <quantity>` followed by optional indented notes. Event types: `grant`, `transfer-in`, `transfer-out`, `cancel`.

#### Scenario: Recording a share grant
- **WHEN** `events.ledger` contains `2024-06-01 grant richard ordinary 500`
- **THEN** the system records that richard was granted 500 ordinary shares on 2024-06-01

#### Scenario: Recording a share transfer
- **WHEN** `events.ledger` contains `2025-03-01 transfer-out richard ordinary 100` followed by `2025-03-01 transfer-in investor1 ordinary 100`
- **THEN** the system records a transfer of 100 ordinary shares from richard to investor1

#### Scenario: Events reference declared classes and holders
- **WHEN** an event references a holder or class not declared in the respective ledger files
- **THEN** `shares check` SHALL report a validation error

### Requirement: Vesting schedule support
Share events MAY include an indented vesting line with format: `    vesting <start-date> <months> <cliff-months>`. When present, the share grant is subject to time-based vesting.

#### Scenario: Grant with vesting
- **WHEN** an event `2024-06-01 grant richard ordinary 500` is followed by `    vesting 2024-06-01 48 12`
- **THEN** the system records that the 500 shares vest over 48 months with a 12-month cliff starting 2024-06-01

#### Scenario: Grant without vesting
- **WHEN** a grant event has no vesting line
- **THEN** the shares are treated as fully vested immediately

### Requirement: LLM context for share management
The shares module SHALL include a `CLAUDE.md` file that teaches the LLM the ledger format, file layout, share event types, and workflow for adding new share events.

#### Scenario: LLM follows conventions
- **WHEN** the LLM is asked to record a new share allocation
- **THEN** the LLM reads `CLAUDE.md`, checks `classes.ledger` and `holders.ledger` for valid references, and appends a correctly formatted event to `events.ledger`

#### Scenario: LLM validates after writing
- **WHEN** the LLM appends a share event
- **THEN** the LLM runs `shares check` to validate the entry before confirming success
