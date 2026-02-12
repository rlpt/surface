## ADDED Requirements

### Requirement: Identify user from roster by git email
The system SHALL read `people/roster.json` and match the current user's `git config user.email` against the email field to identify them. Identification SHALL happen at shell entry time (shellHook), not flake evaluation time.

#### Scenario: Known user enters shell
- **WHEN** a user with git email "alice@formabi.com" runs `nix develop` and roster.json contains an entry with email "alice@formabi.com"
- **THEN** the shell identifies them as "Alice" with their declared roles

#### Scenario: Unknown user enters shell
- **WHEN** a user with git email "stranger@example.com" runs `nix develop` and no roster entry matches
- **THEN** the shell treats them as an unidentified user with base access only, and suggests running `onboard`

#### Scenario: No git email configured
- **WHEN** a user has no `git config user.email` set
- **THEN** the shell treats them as unidentified and suggests configuring git

### Requirement: Roster JSON schema
The roster file `people/roster.json` SHALL be a JSON array of person objects. Each person object SHALL contain: id (string), name (string), email (string), roles (array of strings), region (string), started (date string). Optional fields: github (string), sshKeys (array of strings).

#### Scenario: Valid roster entry
- **WHEN** roster.json contains `{"id": "alice", "name": "Alice", "email": "alice@formabi.com", "roles": ["engineering", "ops"], "region": "uk", "started": "2024-06-01"}`
- **THEN** the system can identify Alice, resolve her roles, and scope her shell experience

### Requirement: Role resolution from roster
When a user is identified, the system SHALL resolve their roles array against the role registry to determine which packages and repo associations apply.

#### Scenario: Multi-role user resolution
- **WHEN** Alice is identified with roles ["engineering", "ops"]
- **THEN** the system merges packages and repo lists from both engineering and ops roles

### Requirement: Unidentified users get full base experience
Users not found in the roster SHALL receive the complete base shell experience including all base commands. They SHALL NOT be blocked or degraded beyond not receiving role-specific packages.

#### Scenario: Unidentified user can still work
- **WHEN** an unidentified user enters the shell
- **THEN** they have git, jq, halp, whoami, and onboard available and can use the repo
