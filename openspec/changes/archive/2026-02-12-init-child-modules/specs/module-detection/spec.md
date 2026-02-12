## MODIFIED Requirements

### Requirement: Detect sibling repos on disk
The system SHALL discover modules by scanning child directories under `modules/` using `builtins.readDir` instead of checking for sibling repositories in the parent directory. Known external repos (formabi-app, latice, deck, cmdr, zolanic) SHALL be removed from the module registry.

#### Scenario: Child module directory exists
- **WHEN** a directory `modules/<name>/default.nix` exists in the surface repo
- **THEN** the module is discovered and its packages are added to the devShell

#### Scenario: No child modules exist
- **WHEN** the `modules/` directory contains no subdirectories (only `default.nix`)
- **THEN** no module packages are added but the shell still starts with base packages

### Requirement: Each module declares its packages
Each child module's `default.nix` SHALL specify the nix packages it contributes to the devShell. These packages SHALL always be included since child modules are always present.

#### Scenario: Dev module adds Node
- **WHEN** the `modules/dev/default.nix` declares `packages = [ pkgs.nodejs ]`
- **THEN** nodejs is available in the devShell

### Requirement: Module registry enumerates all known modules
The module registry SHALL be derived automatically from child directories under `modules/` using `builtins.readDir`. Adding a new module SHALL require only creating a new directory with a `default.nix` file.

#### Scenario: Adding a new module
- **WHEN** a developer creates `modules/accounts/default.nix` with name, description, and packages
- **THEN** the system discovers the module and includes its packages without changing any other file

### Requirement: Shell banner reports active modules
The shell entry message SHALL display the total count of child modules and list each module's name.

#### Scenario: Three child modules present
- **WHEN** three child module directories exist under `modules/`
- **THEN** the shell banner shows "3 modules" and lists each module name

## REMOVED Requirements

### Requirement: Detect sibling repos on disk (original)
**Reason**: Replaced by child-directory module discovery. External sibling repo detection is no longer used.
**Migration**: Modules are now child directories under `modules/<name>/` instead of sibling repos in the parent directory.
