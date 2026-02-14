# Modules — LLM Context

Auto-discovered child directories under `modules/`. Each module is a `default.nix` that receives `{ pkgs, surface, ... }` and returns an attrset.

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

Custom attributes (e.g. `brand.identity`) pass through the normaliser untouched and are accessible to sibling modules and the flake via `modulesByName`.

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

Modules can read sibling module data via `surface.modules`, a lazy attrset keyed by module name. This works because Nix evaluates attributes on demand — accessing `surface.modules.brand` only forces the brand module to evaluate, not the caller.

### Pattern: reference with fallback

```nix
{ pkgs, surface, ... }:

let
  # Safe cross-reference — falls back if the brand module is absent.
  colors =
    if (surface.modules ? brand)
    then surface.modules.brand.identity.colors
    else { primary = "#6366f1"; accent = "#a78bfa"; bg = "#0a0a1a"; text = "#e0e0e0"; };
in
{
  name = "my-module";
  # ... use colors ...
}
```

### Rules

1. **Check before access** — always guard with `surface.modules ? <name>` and provide a fallback.
2. **No self-reference** — a module must not access itself via `surface.modules`. That creates a strict cycle and Nix will error.
3. **No circular chains** — if A reads B and B reads A, Nix will infinite-loop. Keep the dependency graph acyclic.
4. **Prefer data, not packages** — cross-references are best for static data (colours, paths, config). Depending on another module's packages is usually unnecessary since they all end up in the same shell.

### Working example

`modules/marketing/default.nix` imports brand identity from `modules/brand/` with a full fallback:

```nix
brandIdentity =
  if (surface.modules ? brand)
  then surface.modules.brand.identity
  else { name = "Formabi"; strapLine = "..."; colors = { ... }; logoPath = "..."; };
```

The resolved `brandIdentity` is then exposed as a module attribute, so the flake can also access it via `modulesByName.marketing.brandIdentity`.

## How auto-discovery works

`modules/default.nix`:
1. Reads all subdirectories that contain a `default.nix` (others are ignored).
2. Imports each one, passing `{ pkgs, surface }` where `surface` includes `roster`, `roles`, and `modules` (the lazy sibling attrset).
3. Normalises the result (applies defaults, merges `scripts` into `packages`, strips `scripts` key).
4. Filters out modules with `enabled = false`.
5. Returns the list of enabled, normalised modules to the flake.
