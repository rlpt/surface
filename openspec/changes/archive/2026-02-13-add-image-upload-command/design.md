## Context

Surface modules provide shell commands for company operations (marketing decks, accounts, shares, etc.). The image-upload backend service already runs at `upload.zolanic.space` — it creates sessions, serves a mobile upload page, and stores images. A working CLI script exists in cmdr (`scripts/image-upload.nix`) but it's not available in the surface devShell.

The goal is to port this capability into a surface module following established patterns (subcommand routing, `$SURFACE_ROOT` paths, help text, `out/` directory for output).

## Goals / Non-Goals

**Goals:**
- Provide an `image-upload` command in the surface devShell
- Follow the same module contract and script patterns as marketing/accounts/shares
- Download images to `out/image-upload/` (not `/tmp/`)
- Display QR code for phone-based upload workflow
- Copy downloaded image path to clipboard

**Non-Goals:**
- Modifying the backend service (`upload.zolanic.space`) — it stays as-is
- Running the backend locally for development
- Batch upload support (single session per invocation is sufficient)
- Cross-module integration (marketing/brand can reference images manually for now)
- Gallery management or session history

## Decisions

### 1. Port as a surface module, not a symlink or wrapper to cmdr

**Choice**: Rewrite the script as a standalone bash script (`image-upload.sh`) following surface conventions, rather than calling into cmdr.

**Why**: Surface modules use `$SURFACE_ROOT`, output to `out/`, and declare packages via Nix — cmdr scripts use hardcoded nix store paths (`${pkgs.curl}/bin/curl`). A clean port is more maintainable and consistent with sibling modules. The script is only ~60 lines; porting is trivial.

**Alternative rejected**: Wrapping cmdr's script via PATH — would create a cross-repo dependency and break if cmdr isn't checked out.

### 2. Download to `out/image-upload/` with session subdirectories

**Choice**: `$SURFACE_ROOT/out/image-upload/<session-id>/<filename>`

**Why**: Follows the `out/<module>/` convention (marketing uses `out/marketing/`). Session subdirectories prevent filename collisions across uploads. The `out/` directory is gitignored.

**Alternative rejected**: `/tmp/image-upload/` (cmdr's approach) — ephemeral, doesn't follow surface conventions.

### 3. Single-command UX (no subcommands initially)

**Choice**: `image-upload` with no arguments starts the upload flow. Add `help` as the only subcommand.

**Why**: The workflow is a single linear flow (create session → show QR → poll → download). Subcommands add complexity without value when there's only one action. The `help` subcommand follows convention.

**Alternative considered**: Subcommands like `image-upload start`, `image-upload status <id>` — over-engineered for the use case. Can be added later if needed.

### 4. Package dependencies via module `packages`

**Choice**: Declare `curl`, `jq`, and `qrencode` in the module's `packages` list.

**Why**: These tools are called directly in the script (not via nix store paths). The surface module system adds them to the devShell PATH automatically.

## Risks / Trade-offs

- **[Backend unavailable]** → The script already handles this: curl failure or null session_id produces an error message and exits 1. No additional mitigation needed.
- **[macOS-specific `pbcopy`]** → The clipboard copy uses `pbcopy`. Guard with a check for `pbcopy` availability; skip clipboard copy with a message on non-macOS systems.
- **[5-minute timeout]** → Matches cmdr's existing behavior. Sufficient for phone camera workflow. User sees progress dots while waiting.
