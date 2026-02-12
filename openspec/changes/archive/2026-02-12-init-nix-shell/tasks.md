## 1. Flake Foundation

- [x] 1.1 Create `flake.nix` with nixpkgs input, `eachDefaultSystem` for x86_64-linux and aarch64-darwin, and an empty default devShell that starts bash
- [x] 1.2 Add `.envrc` with `use flake` for direnv users (optional convenience)
- [x] 1.3 Verify `nix develop` starts a shell with git and jq available on both supported systems

## 2. Roster and Identity

- [x] 2.1 Create `people/roster.json` with seed data (at minimum one real person entry with id, name, email, roles, region, started)
- [x] 2.2 Create `people/default.nix` that reads roster.json via `builtins.fromJSON (builtins.readFile ./roster.json)` and exposes it as a list

## 3. Role Definitions

- [x] 3.1 Create `roles/default.nix` with attrset defining four roles (engineering, ops, sales, design) — each with description, repos, packages function, serverAccess, and context list
- [x] 3.2 Wire roles into the devShell so that role packages are available (initially all role packages included; role-scoping comes with user identity)

## 4. Module Detection

- [x] 4.1 Create `modules/default.nix` with the module registry — list of known sibling repos with name, repo path (relative to parent dir), associated role, and packages
- [x] 4.2 Implement `builtins.pathExists` detection in flake.nix to filter module registry to active modules only
- [x] 4.3 Merge active module packages into the devShell's buildInputs
- [x] 4.4 Export active/inactive module info for the shellHook to display

## 5. Shell Scripts

- [x] 5.1 Create `scripts/halp.sh` — lists available and unavailable commands grouped by role
- [x] 5.2 Create `scripts/whoami.sh` — reads roster.json with jq, matches git email, displays identity/roles/modules
- [x] 5.3 Create `scripts/onboard.sh` — identifies user, shows company context, lists repos to clone, suggests first steps
- [x] 5.4 Wire scripts into devShell PATH (either via `writeShellScriptBin` wrapping or by adding scripts/ to PATH)

## 6. Shell Entry Experience

- [x] 6.1 Implement shellHook in flake.nix that: detects user (git email → roster lookup via jq), displays banner with shell name, active module count, user identity, and hint for `halp` or `onboard`
- [x] 6.2 Pass active module metadata and user identity info to shell scripts as environment variables or via roster.json lookup

## 7. Verification

- [x] 7.1 Test: `nix develop` works with zero sibling repos — base shell with halp, whoami, onboard
- [x] 7.2 Test: `nix develop` with one sibling repo cloned — module detected, extra tools available
- [x] 7.3 Test: `whoami` shows correct identity for a user in roster.json
- [x] 7.4 Test: `whoami` shows "unidentified" for a user not in roster.json
- [x] 7.5 Test: `halp` displays base commands for all users
