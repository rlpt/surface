## MODIFIED Requirements

### Requirement: Shares shell command
A `shares` shell script SHALL be available in the devShell that provides subcommands for querying and exporting share data. The script SHALL read from `$SURFACE_ROOT/modules/shares/cap-table/`.

#### Scenario: Command is available
- **WHEN** a user types `shares` in the shell
- **THEN** the command executes and shows usage information listing available subcommands including `pdf`

### Requirement: LLM query translation for shares
The LLM SHALL translate natural language questions about share allocations into `shares` subcommands, run them, and summarise the results.

#### Scenario: Cap table query
- **WHEN** a user asks "who owns what percentage of the company?"
- **THEN** the LLM runs `shares table` and summarises the output

#### Scenario: Export request
- **WHEN** a user asks "generate a spreadsheet of the cap table for our investor"
- **THEN** the LLM runs `shares export`, saves the output to a CSV file, and provides the file path

#### Scenario: PDF report request
- **WHEN** a user asks "create a PDF of the cap table for the board"
- **THEN** the LLM runs `shares pdf table --output cap-table.pdf` and provides the file path
