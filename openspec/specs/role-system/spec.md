## ADDED Requirements

### Requirement: Four roles defined
The system SHALL define four roles: engineering, ops, sales, design. Each role SHALL declare: a description, associated repos, packages, server access level, and context scopes.

#### Scenario: Engineering role definition
- **WHEN** the engineering role is evaluated
- **THEN** it associates repos [formabi-app, latice], packages [elm, nodejs, cargo, rustc], serverAccess "none", and context ["app"]

#### Scenario: Ops role definition
- **WHEN** the ops role is evaluated
- **THEN** it associates repos [cmdr], packages [deploy-rs, age, ssh-to-age], serverAccess "wheel", and context ["ops"]

#### Scenario: Sales role definition
- **WHEN** the sales role is evaluated
- **THEN** it associates repos [deck], packages [marp-cli], serverAccess "none", and context ["sales"]

#### Scenario: Design role definition
- **WHEN** the design role is evaluated
- **THEN** it associates repos [zolanic], packages [nodejs], serverAccess "none", and context ["design"]

### Requirement: Roles control package inclusion
A user's roles SHALL determine which additional packages are included in their shell, beyond the base packages. A user with multiple roles SHALL receive the union of all role packages.

#### Scenario: User with engineering and ops roles
- **WHEN** a user is identified with roles ["engineering", "ops"]
- **THEN** the shell includes packages from both engineering (elm, nodejs, cargo, rustc) and ops (deploy-rs, age, ssh-to-age) in addition to base packages

#### Scenario: User with no matching role
- **WHEN** a user is identified but has an unrecognized role
- **THEN** the shell includes only base packages and logs a warning about the unknown role

### Requirement: Roles are extensible
Adding a new role SHALL require only adding an entry to the role registry. No other files SHALL need modification for the role to be recognized.

#### Scenario: Adding a design role
- **WHEN** a developer adds a "design" entry to the role registry
- **THEN** users with that role receive its declared packages and repo associations
