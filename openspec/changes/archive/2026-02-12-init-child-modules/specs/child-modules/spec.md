## ADDED Requirements

### Requirement: Child module directory structure
Each module SHALL be a directory under `modules/<name>/` containing a `default.nix` file. The `default.nix` SHALL return an attribute set with at minimum: `name` (string), `description` (string), and `packages` (list of nix packages).

#### Scenario: Valid child module
- **WHEN** a directory `modules/dev/default.nix` exists and returns `{ name = "dev"; description = "Development tools"; packages = [ pkgs.nodejs ]; }`
- **THEN** the module is discovered and its packages are included in the devShell

#### Scenario: Child module with no packages
- **WHEN** a child module returns an empty packages list
- **THEN** the module is still discovered and listed but contributes no additional packages

### Requirement: Auto-discovery of child modules
The `modules/default.nix` SHALL use `builtins.readDir` to discover all child directories and import each one's `default.nix`. No explicit module list SHALL be maintained — adding a module directory is sufficient to register it.

#### Scenario: Adding a new child module
- **WHEN** a developer creates `modules/accounts/default.nix` with valid module attributes
- **THEN** the module is automatically discovered and included without editing any other file

#### Scenario: Non-module files in modules directory
- **WHEN** the `modules/` directory contains files that are not directories (e.g., `default.nix` itself)
- **THEN** only subdirectories are treated as modules; files are ignored

### Requirement: All child modules are always active
Since child modules exist within the repo tree, all discovered modules SHALL be treated as active. There SHALL be no concept of "inactive" or "missing" child modules.

#### Scenario: All modules available
- **WHEN** the shell starts
- **THEN** every child module directory contributes its packages to the devShell
