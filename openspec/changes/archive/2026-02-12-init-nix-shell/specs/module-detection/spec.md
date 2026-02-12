## ADDED Requirements

### Requirement: Detect sibling repos on disk
The system SHALL check for known sibling repositories in the parent directory of the surface repo using filesystem path detection. Known repos: formabi-app, latice, deck, cmdr, zolanic.

#### Scenario: Sibling repo exists
- **WHEN** a known repo directory (e.g., `../formabi-app`) exists on disk at flake evaluation time
- **THEN** the module is marked as active and its packages are added to the devShell

#### Scenario: Sibling repo does not exist
- **WHEN** a known repo directory does not exist on disk
- **THEN** the module is marked as inactive, no error occurs, and the shell still starts

### Requirement: Each module declares its packages
Each module definition SHALL specify the nix packages it contributes to the devShell. These packages SHALL only be included when the module is active (its repo is detected on disk).

#### Scenario: Engineering module adds Elm and Node
- **WHEN** the formabi-app repo is detected on disk
- **THEN** elm, nodejs, cargo, and rustc are available in the devShell

#### Scenario: Sales module adds Marp
- **WHEN** the deck repo is detected on disk
- **THEN** marp-cli is available in the devShell

### Requirement: Module registry enumerates all known modules
A module registry SHALL define all known sibling repos with their directory name, associated role, and package list. Adding a new module SHALL require only adding an entry to this registry.

#### Scenario: Adding a new module
- **WHEN** a developer adds a new entry to the module registry with name, repo path, role, and packages
- **THEN** the system detects that repo on disk and includes its packages without changing any other file

### Requirement: Shell banner reports active modules
The shell entry message SHALL display a count of active vs total modules and list each module's status.

#### Scenario: Two of five modules active
- **WHEN** the user has formabi-app and latice cloned but not deck, cmdr, or zolanic
- **THEN** the shell banner shows "2 of 5 modules active" and lists each module with a checkmark or dash
