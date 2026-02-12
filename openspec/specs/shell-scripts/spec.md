## ADDED Requirements

### Requirement: halp command shows available commands
The `halp` command SHALL display all available commands in the current shell, grouped by availability. Commands available to the user's role SHALL be shown as available. Commands requiring a different role SHALL be shown as unavailable with the required role noted.

#### Scenario: Base user runs halp
- **WHEN** an unidentified user runs `halp`
- **THEN** the output shows base commands (halp, whoami, onboard) as available

#### Scenario: Ops user runs halp
- **WHEN** a user with the ops role runs `halp`
- **THEN** the output shows base commands plus ops-specific commands as available

### Requirement: whoami command shows identity and state
The `whoami` command SHALL display the current user's identity (name, roles, region) and their module status (which sibling repos are active, which are inactive and why).

#### Scenario: Known user runs whoami
- **WHEN** Alice (engineering, ops, uk) runs `whoami` with formabi-app and cmdr cloned
- **THEN** the output shows her name, roles, region, and module list with formabi-app and cmdr as active, others as inactive with reason (not cloned or not her role)

#### Scenario: Unknown user runs whoami
- **WHEN** an unidentified user runs `whoami`
- **THEN** the output shows "Unidentified" for name, no roles, and suggests running `onboard` or checking git email

### Requirement: onboard command guides new users
The `onboard` command SHALL identify the user from the roster and provide a guided setup experience: which repos to clone, what their role covers, current priorities, and how to get started.

#### Scenario: Known user runs onboard
- **WHEN** a user found in the roster runs `onboard`
- **THEN** the script shows their identity, role description, repos to clone, and first steps

#### Scenario: Unknown user runs onboard
- **WHEN** an unidentified user runs `onboard`
- **THEN** the script explains the repo, suggests contacting an admin to be added to the roster, and shows how to configure git email

### Requirement: Shell entry banner
On shell entry, a banner SHALL display: the shell name ("surface"), active module count, base tools available, and a hint to run `onboard` if the user is unidentified or `halp` for commands.

#### Scenario: First entry with no modules
- **WHEN** a user enters the shell for the first time with no sibling repos
- **THEN** the banner shows "surface shell — 0 of 5 modules active", lists base tools, and suggests `onboard`

#### Scenario: Entry with modules and identified user
- **WHEN** Alice enters the shell with 3 sibling repos cloned
- **THEN** the banner shows her name, "3 of 5 modules active", and lists the active modules
