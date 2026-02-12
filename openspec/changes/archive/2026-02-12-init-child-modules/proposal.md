## Why

Surface currently defines modules as external sibling repositories detected on disk via `--impure` evaluation. This experimental repo needs a self-contained module structure where all modules live as child directories within the surface repo itself, removing the dependency on external repos existing alongside it. This enables future child modules (e.g., `dev`, `accounts`) to be added directly as subdirectories.

## What Changes

- **BREAKING**: Replace sibling-repo detection with child-directory module structure — modules will live under `modules/<name>/` instead of being detected in the parent directory
- Remove all references to external repos (formabi-app, latice, deck, cmdr, zolanic) from the module registry
- Update `flake.nix` to source modules from child directories rather than scanning the parent directory
- Simplify module activation — child modules are always present, no impure path detection needed
- Prepare the module structure so new child modules (dev, accounts, etc.) can be added as subdirectories in the future

## Capabilities

### New Capabilities

- `child-modules`: Defines the child-directory module structure under `modules/<name>/`, how modules declare their packages and metadata, and how new modules are added

### Modified Capabilities

- `module-detection`: Detection logic changes from scanning parent directory for sibling repos to discovering child directories within the surface repo itself
- `nix-flake`: Flake no longer requires `--impure` for module detection; module imports change from sibling-repo scanning to direct child-directory imports

## Impact

- `modules/default.nix` — complete rewrite to child-directory structure
- `flake.nix` — module discovery and activation logic changes, `--impure` may no longer be needed for modules
- Shell scripts (`whoami.sh`, `onboard.sh`, `halp.sh`) — module status display updates since modules are always present
- Existing module references (formabi-app, latice, etc.) are removed entirely
