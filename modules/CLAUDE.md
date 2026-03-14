# Modules — LLM Context

Auto-discovered child directories under `modules/`. Each module is a `default.nix` that receives `{ pkgs, surface, ... }` and returns an attrset.

## Data layer

Structured data (shares, pools, holders, officers, compliance, board) is stored as YAML files in `data/` at the project root, versioned by git. The shared library `modules/data/scripts/datalib.py` loads/saves YAML, provides schema linting (`datalib.lint()`), referential integrity checks (`datalib.validate_refs()`), and computed views (holdings, cap table, vesting schedules, compliance deadlines). Query with Python: `datalib.load("shares")`. Version data changes with `git commit`.

## Module contract

| Attribute   | Required | Default | Description                                    |
|-------------|----------|---------|------------------------------------------------|
| `name`      | yes      | —       | Unique module identifier                       |
| `description` | no     | `""`    | One-line summary                               |
| `packages`  | no       | `[]`    | Derivations added to the devShell               |
| `scripts`   | no       | `[]`    | `writeShellScriptBin` derivations (merged into packages) |
| `helpText`  | no       | `""`    | Multi-line help shown by `halp`                |
| `shellHook` | no       | `""`    | Bash run during shell initialisation           |
| `enabled`   | no       | `true`  | Set `false` to exclude from the shell          |

Custom attributes pass through the normaliser untouched and are accessible to sibling modules and the flake via `modulesByName`.

## Minimal module

```nix
{ pkgs, ... }:

{
  name = "example";
  packages = with pkgs; [ curl ];
}
```

Everything except `name` is optional — the normaliser in `modules/default.nix` fills in defaults.

## Cross-module references

Modules can read sibling module data via `surface.modules`, a lazy attrset keyed by module name. This works because Nix evaluates attributes on demand — accessing `surface.modules.foo` only forces that module to evaluate, not the caller.

### Rules

1. **Check before access** — always guard with `surface.modules ? <name>` and provide a fallback.
2. **No self-reference** — a module must not access itself via `surface.modules`. That creates a strict cycle and Nix will error.
3. **No circular chains** — if A reads B and B reads A, Nix will infinite-loop. Keep the dependency graph acyclic.
4. **Prefer data, not packages** — cross-references are best for static data (colours, paths, config). Depending on another module's packages is usually unnecessary since they all end up in the same shell.

## How auto-discovery works

`modules/default.nix`:
1. Reads all subdirectories that contain a `default.nix` (others are ignored).
2. Imports each one, passing `{ pkgs, surface }` where `surface` includes `modules` (the lazy sibling attrset).
3. Normalises the result (applies defaults, merges `scripts` into `packages`, strips `scripts` key).
4. Filters out modules with `enabled = false`.
5. Returns the list of enabled, normalised modules to the flake.
