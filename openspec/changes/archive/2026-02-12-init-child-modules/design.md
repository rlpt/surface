## Context

Surface currently models modules as external sibling repositories detected at flake evaluation time using `--impure` and `builtins.getEnv`. The module registry in `modules/default.nix` lists five external repos (formabi-app, latice, deck, cmdr, zolanic) with their packages.

This is an experimental repo. The goal is to make it fully self-contained — all modules should be child directories within the surface repo, with no references to external repos. Future modules (e.g., `dev`, `accounts`) will be added as child directories to mock various domains.

## Goals / Non-Goals

**Goals:**
- All modules live as child directories under `modules/<name>/`
- Each child module directory contains its own `default.nix` declaring metadata and packages
- `modules/default.nix` discovers child directories automatically
- Remove all references to external sibling repos
- Eliminate the need for `--impure` flag for module detection

**Non-Goals:**
- Creating actual child module implementations (dev, accounts, etc.) — those come later
- Changing the role system, people system, or shell scripts beyond what's needed for module status display
- Supporting a mix of child modules and external sibling repos

## Decisions

### Child module directory structure
Each module lives at `modules/<name>/default.nix` and exports an attribute set with `name`, `description`, `packages`, and optional metadata.

**Rationale**: Using `default.nix` per module follows standard Nix convention and keeps each module self-contained. The parent `modules/default.nix` imports all child directories.

**Alternative considered**: A single flat registry file — rejected because per-directory modules are easier to extend and keep concerns separated.

### Module discovery via directory listing
`modules/default.nix` will use `builtins.readDir` to discover child module directories and import each one. This is a pure Nix operation — no `--impure` needed.

**Rationale**: `builtins.readDir` is pure and works at eval time. Since child modules always exist in the repo, there's no need for runtime path detection.

**Alternative considered**: Keeping an explicit list in `modules/default.nix` — rejected because auto-discovery means adding a module is just adding a directory.

### Remove --impure requirement for modules
Since child modules are always present in the repo tree, `builtins.getEnv` and `builtins.pathExists` for parent-directory scanning are no longer needed for module detection.

**Rationale**: Pure evaluation is simpler and more reproducible. The `--impure` flag may still be needed for other features (e.g., git email detection in shellHook) but not for module discovery.

### Module status simplification
Since all child modules are always present, the active/inactive distinction changes. All child modules are always "active" — the concept of missing modules goes away.

**Rationale**: Child directories are always part of the repo. The banner and scripts should reflect this — showing all modules as available rather than tracking cloned/not-cloned state.

## Risks / Trade-offs

- [Breaking change] Existing module references to formabi-app, latice, etc. are removed entirely → Users who relied on sibling-repo detection will need to adapt. **Mitigation**: This is an experimental repo; no external users depend on the old behavior.
- [Simplified model] Losing the active/inactive module concept → Some shell script logic becomes simpler but the "clone this repo" onboarding flow no longer applies to modules. **Mitigation**: Future child modules will define their own onboarding if needed.
