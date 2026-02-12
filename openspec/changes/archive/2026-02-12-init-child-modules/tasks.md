## 1. Restructure modules to child directories

- [x] 1.1 Remove existing external module entries from `modules/default.nix` (formabi-app, latice, deck, cmdr, zolanic)
- [x] 1.2 Rewrite `modules/default.nix` to use `builtins.readDir` to discover child directories and import each `<name>/default.nix`
- [x] 1.3 Create a sample child module at `modules/hello/default.nix` with name, description, and packages to validate the structure

## 2. Update flake.nix for child module discovery

- [x] 2.1 Replace parent-directory sibling-repo scanning logic in `flake.nix` with direct import of the new `modules/default.nix` auto-discovery
- [x] 2.2 Remove `--impure` dependent module detection code (`builtins.getEnv`, `builtins.pathExists` for parent dir scanning)
- [x] 2.3 Simplify module package collection — all child modules are always active, remove active/inactive filtering
- [x] 2.4 Update environment variables (`SURFACE_ACTIVE_MODULES`, `SURFACE_ALL_MODULES`) to reflect that all modules are always present

## 3. Update shell banner and scripts

- [x] 3.1 Update shell banner in `flake.nix` shellHook to show total module count instead of "X of Y active"
- [x] 3.2 Update `scripts/whoami.sh` to list all modules without active/inactive distinction
- [x] 3.3 Update `scripts/onboard.sh` to remove "repos to clone" section since modules are now child directories
- [x] 3.4 Update `scripts/halp.sh` if any module-related help text references sibling repos

## 4. Verify

- [x] 4.1 Run `nix flake check` to verify flake evaluates correctly
- [x] 4.2 Enter the shell with `nix develop` and confirm the banner, module listing, and scripts work correctly
