## ADDED Requirements

### Requirement: Root flake with nixpkgs input
The flake.nix SHALL declare nixpkgs as its sole flake input. No private repositories SHALL appear as flake inputs. The flake-utils input is permitted for multi-system support.

#### Scenario: Flake evaluates with only nixpkgs
- **WHEN** a user runs `nix flake show` in the surface repo
- **THEN** the flake evaluates successfully with nixpkgs (and flake-utils) as inputs and exposes a `devShells.<system>.default` output

### Requirement: Default devShell provides base packages
The default devShell SHALL include base packages: git, jq, and any nix tools needed for the shell to function. These packages SHALL be available regardless of which modules are present.

#### Scenario: Base shell with no modules
- **WHEN** a user runs `nix develop` with no child module directories
- **THEN** the shell starts successfully with git, jq, and base shell scripts available in PATH

### Requirement: Multi-system support
The flake SHALL produce devShell outputs for both `x86_64-linux` and `aarch64-darwin` systems.

#### Scenario: Shell works on macOS ARM
- **WHEN** a user on an Apple Silicon Mac runs `nix develop`
- **THEN** the shell starts with all base packages compiled for aarch64-darwin

#### Scenario: Shell works on Linux x86_64
- **WHEN** a user on a Linux x86_64 machine runs `nix develop`
- **THEN** the shell starts with all base packages compiled for x86_64-linux

### Requirement: Graceful degradation is the default
The flake SHALL never fail due to missing roster data or missing role definitions. Missing data SHALL result in reduced functionality, never errors. Module discovery SHALL use pure `builtins.readDir` and SHALL NOT require the `--impure` flag.

#### Scenario: Empty roster.json
- **WHEN** roster.json is empty or contains an empty array
- **THEN** the shell starts with base tools and the user is treated as unidentified

#### Scenario: Malformed or missing optional files
- **WHEN** any optional file (roster.json, role definitions) is missing or unreadable
- **THEN** the shell starts with base tools and logs a warning, but does not fail

#### Scenario: No child module directories
- **WHEN** the `modules/` directory has no subdirectories
- **THEN** the shell starts with base packages only and no module-specific packages
