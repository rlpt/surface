## Context

Surface is the root repo of the formabi company-as-code system. It currently contains only `company-as-code-plan.md`. The plan describes a comprehensive system where `flake.nix` is the composition layer — reading JSON data, detecting sibling repos, and producing role-scoped devShells.

This is the first implementation step: get `nix develop` working so anyone can clone the repo and enter a shell. The shell must work with zero configuration and zero sibling repos, then progressively enhance as repos are cloned and the user is identified in the roster.

Constraints:
- Nix flakes only (no devenv, no nix-shell)
- Only nixpkgs in flake inputs — private repos are never flake inputs
- Must work on macOS and Linux (the team spans UK and Singapore)
- Shell scripts over custom tooling (KISS principle)

## Goals / Non-Goals

**Goals:**
- A `nix develop` that works immediately after cloning, with zero sibling repos
- Graceful module detection — each sibling repo found on disk adds tools to the shell
- User identification from `people/roster.json` matched by git email
- Role-scoped experience — tools and context vary by role
- Shell entry banner showing identity, active modules, available commands
- Base commands: `halp`, `whoami`, `onboard` available to everyone

**Non-Goals:**
- Server configuration (nixosConfigurations.hull) — deferred to a later change
- The datom log / transact / derive tooling — separate concern
- AI context assembly (CLAUDE.md generation) — separate concern
- Secrets management (agenix) — separate concern
- CI/CD pipelines — separate concern
- Named devShells per person (`nix develop .#alice`) — start with a single default shell that detects the user at runtime

## Decisions

### Single default devShell with runtime user detection
**Decision**: One `devShell.default` that detects the user at shell entry via `git config user.email`, rather than per-person devShells like `.#alice`.

**Rationale**: Per-person shells require knowing who will use the repo at flake eval time. Runtime detection is simpler — the flake evaluates once, the shellHook identifies the user. This matches how the plan describes `nix develop` (not `nix develop .#alice`).

**Alternative considered**: Per-person devShells. Rejected because it couples flake evaluation to roster data, complicates caching, and requires the user to know their shell name.

### builtins.pathExists for sibling repo detection
**Decision**: Detect sibling repos at flake eval time using `builtins.pathExists (../. + "/<repo-name>")`.

**Rationale**: This is exactly what the plan specifies. Missing repos = fewer tools, never an error. No network access needed. Pure filesystem check.

**Alternative considered**: Flake inputs with `follows`. Rejected because flake inputs resolve at lock time — if you can't access a private repo, the entire lock fails.

### Roles as nix attrsets, not files
**Decision**: For this initial change, define roles as attrsets in a single `roles/default.nix` rather than one file per role.

**Rationale**: With 4 roles and simple definitions, separate files add navigation overhead without benefit. When roles grow complex (agent configs, secret access scopes), they can be split. Start simple.

**Alternative considered**: One `.nix` file per role as shown in the plan. Can migrate later when complexity warrants it.

### roster.json as a seed file, manually maintained for now
**Decision**: Ship a `people/roster.json` that is manually edited. The datom log + derive tooling that generates it comes later.

**Rationale**: The datom layer is a separate change. The shell needs roster data now. JSON is the universal format — nix reads it with `builtins.fromJSON`, scripts read it with `jq`, LLMs read it directly. Starting with manual JSON means the shell works before the transact/derive pipeline exists.

### Shell scripts as standalone .sh files, wrapped into PATH by nix
**Decision**: Scripts live in `scripts/` as plain bash files. The devShell adds them to PATH via `makeShellPath` or wraps them with `writeShellScriptBin`.

**Rationale**: KISS — plain bash files are readable, editable, and debuggable without nix knowledge. Nix just puts them in PATH.

## Risks / Trade-offs

- **builtins.pathExists is impure** → This is a known nix limitation. The flake will need `--impure` flag or we use the `path` type carefully. Acceptable trade-off for the graceful degradation model. → Mitigation: Document that `nix develop --impure` is required, or use a shellHook-based detection that runs at shell entry instead of eval time.

- **Runtime user detection can fail** → If the user hasn't configured `git config user.email` or their email isn't in roster.json, they get the base shell. → Mitigation: The base shell is fully functional. `onboard` script guides them through setup. Failing gracefully is the design.

- **roster.json is manually maintained for now** → Risk of drift or stale data. → Mitigation: This is temporary. The datom layer change will make roster.json a derived view. For a team of 3, manual JSON is fine.

- **Module detection at eval time vs shellHook time** → pathExists at eval time means `nix develop` must be re-run after cloning a sibling repo. A shellHook approach would detect at every shell entry but can't change nix packages. → Mitigation: Document this. `exit` + `nix develop` after cloning new repos. The shell banner shows active modules so missing ones are visible.
