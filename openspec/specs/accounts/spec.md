### Requirement: Accounts module declaration
The accounts module SHALL declare itself as a child module under `modules/accounts/default.nix` with `pkgs.hledger` as its package. The module SHALL be auto-discovered by the existing module-detection system.

#### Scenario: Module is discovered
- **WHEN** `modules/accounts/default.nix` exists with name, description, and packages
- **THEN** hledger is available in the devShell and the shell banner includes "accounts" in the module list

### Requirement: Journal file structure
The module SHALL contain a `books/` directory with an include-based journal structure: `main.journal` as the entry point, `accounts.journal` for the chart of accounts, and one file per financial year.

#### Scenario: hledger reads the journal tree
- **WHEN** a user runs `hledger -f modules/accounts/books/main.journal stats`
- **THEN** hledger reports the journal's date range, transaction count, and accounts used without errors

#### Scenario: Year file isolation
- **WHEN** transactions exist in `2025.journal` and `2026.journal`
- **THEN** running `hledger -f modules/accounts/books/main.journal reg -p 2026` shows only 2026 transactions

### Requirement: Chart of accounts declares all valid accounts
The `accounts.journal` file SHALL declare the full account tree using hledger `account` directives. All postings in year files SHALL use accounts declared in this file.

#### Scenario: Validation catches undeclared account
- **WHEN** a transaction posts to an account not declared in `accounts.journal`
- **THEN** `hledger -f modules/accounts/books/main.journal check accounts` reports an error

#### Scenario: All existing postings use declared accounts
- **WHEN** a user runs `hledger -f modules/accounts/books/main.journal check accounts`
- **THEN** the check passes with no errors

### Requirement: Transaction format conventions
Transactions SHALL follow these style rules: date as `YYYY-MM-DD`, payee and description separated by ` | `, four-space indent for postings, currency symbol before amount with no space (e.g. `£34.21`), one blank line between transactions.

#### Scenario: Well-formed transaction
- **WHEN** a transaction is entered as `2026-02-07 AWS | Cloud services feb` with posting `    expenses:infra:cloud             £34.21`
- **THEN** `hledger check` passes and the transaction is parseable

### Requirement: LLM-assisted transaction entry
The LLM SHALL be able to read the chart of accounts and existing journal style, then append correctly formatted transactions to the current year file based on natural language descriptions from the user.

#### Scenario: Natural language to journal entry
- **WHEN** a user tells the LLM "I paid £200 to Companies House for the confirmation statement, came out of Tide on the 10th"
- **THEN** the LLM reads `accounts.journal` for account names, reads the current year file for style, and appends a correctly formatted transaction to the year file

#### Scenario: LLM asks about ambiguous categorisation
- **WHEN** the user describes a transaction that could map to multiple accounts
- **THEN** the LLM asks which account to use rather than guessing

### Requirement: LLM query translation
The LLM SHALL translate natural language financial questions into hledger CLI commands, run them, and summarise the results.

#### Scenario: Balance query
- **WHEN** a user asks "how much have we spent on infra this year?"
- **THEN** the LLM runs an appropriate `hledger bal` command filtered to `expenses:infra` and summarises the result

#### Scenario: Income statement query
- **WHEN** a user asks "summarise February"
- **THEN** the LLM runs `hledger is` and `hledger bs` for the period and presents a summary of revenue, expenses, net, and balances

### Requirement: Accounts shell script
An `accounts` script SHALL be available in the shell that acts as a shortcut for `hledger -f $SURFACE_ROOT/modules/accounts/books/main.journal`, passing through all arguments.

#### Scenario: Shortcut invocation
- **WHEN** a user runs `accounts bal expenses:infra`
- **THEN** the output is identical to running `hledger -f modules/accounts/books/main.journal bal expenses:infra`

### Requirement: LLM context for bookkeeping
The accounts module SHALL include context (CLAUDE.md or equivalent) that teaches the LLM the journal conventions, account tree, common hledger commands, and the workflow of reading `accounts.journal` before appending to year files.

#### Scenario: LLM follows conventions without prompting
- **WHEN** the LLM is asked to add a transaction without specific formatting instructions
- **THEN** the LLM produces a transaction matching the style rules (date format, payee separator, indent, currency format) because it has read the context file

#### Scenario: LLM validates after writing
- **WHEN** the LLM appends a transaction to a year file
- **THEN** the LLM runs `hledger check` to validate the entry before confirming success
