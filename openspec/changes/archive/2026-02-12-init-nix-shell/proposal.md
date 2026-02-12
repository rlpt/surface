## Why

Surface is the top-level entry point to the formabi company-as-code system. Anyone — employee, contributor, or LLM — should be able to `git clone` and `nix develop` to get a working shell. Today the repo has only a plan document and no Nix setup. Without a flake, there's no shell, no tooling, no onboarding path. This is the foundation everything else builds on.

## What Changes

- Add `flake.nix` as the root Nix composition layer with nixpkgs as the sole input
- Add a default devShell providing base tools (git, jq) and shell scripts (halp, whoami, onboard)
- Add module detection system using `builtins.pathExists` to find sibling repos on disk (formabi-app, latice, deck, cmdr, zolanic) and extend the shell with their tools
- Add role definitions in `roles/` (engineering, ops, sales, design) that map to packages and repo access
- Add `people/roster.json` reading so the shell can identify the current user by git email and scope their experience by role
- Add shell entry banner showing active modules, person identity, and available commands
- Add `scripts/halp.sh`, `scripts/whoami.sh`, `scripts/onboard.sh` as base shell commands

## Capabilities

### New Capabilities
- `nix-flake`: Root flake.nix with nixpkgs input, devShell output, and graceful degradation via pathExists
- `module-detection`: Sibling repo detection system — scans parent directory for known repos and conditionally adds tools/context
- `role-system`: Role definitions (engineering, ops, sales, design) that declare packages, repo associations, server access levels, and context scopes
- `user-identity`: Roster-based user identification — reads roster.json, matches git email, resolves roles, scopes the shell experience
- `shell-scripts`: Base shell commands (halp, whoami, onboard) available to everyone in the devShell

### Modified Capabilities
<!-- No existing capabilities to modify — this is the first change. -->

## Impact

- **New files**: flake.nix, flake.lock, roles/*.nix, people/roster.json, people/default.nix, base/default.nix, scripts/*.sh, modules/*.nix
- **Dependencies**: nixpkgs (only public dependency; all private repos detected on disk, never as flake inputs)
- **Systems**: Local development only — no server changes. The flake will eventually grow nixosConfigurations.hull but that's out of scope for this change.
- **Users**: After this change, anyone can `nix develop` in the surface repo and get a working shell. Employees in roster.json get a role-scoped experience. Unknown users get the base shell.
