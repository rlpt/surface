## ADDED Requirements

### Requirement: Shares shell command
A `shares` shell script SHALL be available in the devShell that provides subcommands for querying and exporting share data. The script SHALL read from `$SURFACE_ROOT/modules/shares/cap-table/`.

#### Scenario: Command is available
- **WHEN** a user types `shares` in the shell
- **THEN** the command executes and shows usage information listing available subcommands

### Requirement: Cap table display
The `shares table` subcommand SHALL compute the current cap table from all events and display it as a formatted table showing: holder name, share class, shares held, percentage of total issued, and vesting status.

#### Scenario: Display current cap table
- **WHEN** a user runs `shares table`
- **THEN** the output shows each holder's position computed from all grant/transfer/cancel events, with percentages calculated against total issued shares

#### Scenario: Vesting status shown
- **WHEN** a holder has shares with a vesting schedule
- **THEN** `shares table` shows the number of shares vested as of today and the total granted

### Requirement: CSV export
The `shares export` subcommand SHALL output the cap table as CSV to stdout. Columns: `holder,share_class,shares_held,percentage,vested,total_granted,notes`. The output SHALL be valid CSV with a header row.

#### Scenario: Export to file
- **WHEN** a user runs `shares export > cap-table.csv`
- **THEN** the resulting file is a valid CSV that opens correctly in Excel or Google Sheets

#### Scenario: Export includes all holders
- **WHEN** multiple holders have shares across different classes
- **THEN** each holder-class combination appears as a separate row in the CSV

### Requirement: Holder detail query
The `shares holders` subcommand SHALL list all declared holders with their current total shareholding across all classes.

#### Scenario: List holders
- **WHEN** a user runs `shares holders`
- **THEN** the output lists each holder with their display name and total shares held

### Requirement: Event history query
The `shares history` subcommand SHALL display all share events in chronological order, optionally filtered by holder.

#### Scenario: Full history
- **WHEN** a user runs `shares history`
- **THEN** all events from `events.ledger` are displayed in date order

#### Scenario: Filtered history
- **WHEN** a user runs `shares history richard`
- **THEN** only events involving holder "richard" are displayed

### Requirement: Validation check
The `shares check` subcommand SHALL validate the ledger files: all events reference declared classes and holders, no holder has negative shares after applying all events, and total issued shares do not exceed authorised shares per class.

#### Scenario: Valid ledger passes
- **WHEN** all events are consistent with declarations
- **THEN** `shares check` exits with code 0 and prints "OK"

#### Scenario: Over-allocation detected
- **WHEN** total granted shares for a class exceed the authorised count in `classes.ledger`
- **THEN** `shares check` exits with code 1 and reports which class is over-allocated

#### Scenario: Unknown holder detected
- **WHEN** an event references a holder not declared in `holders.ledger`
- **THEN** `shares check` exits with code 1 and reports the unknown holder

### Requirement: LLM query translation for shares
The LLM SHALL translate natural language questions about share allocations into `shares` subcommands, run them, and summarise the results.

#### Scenario: Cap table query
- **WHEN** a user asks "who owns what percentage of the company?"
- **THEN** the LLM runs `shares table` and summarises the output

#### Scenario: Export request
- **WHEN** a user asks "generate a spreadsheet of the cap table for our investor"
- **THEN** the LLM runs `shares export`, saves the output to a CSV file, and provides the file path
