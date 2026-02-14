## Why

The image-upload backend service (at `upload.zolanic.space`) already exists and works, and cmdr already has a script that calls its API. But surface has no way to use it — anyone working in the surface devShell has to switch to cmdr to upload an image from their phone. Adding an `image-upload` command as a surface module makes the capability available where the assets are actually needed (marketing decks, brand work, etc.).

## What Changes

- Add a new `image-upload` module under `modules/image-upload/`
- Provide an `image-upload` shell command with subcommands for creating upload sessions, polling status, and retrieving images
- Downloaded images land in `out/image-upload/` following the surface output convention
- QR code display in terminal for mobile phone camera workflow
- Help text integrated into `halp` via the module system

## Capabilities

### New Capabilities
- `image-upload-command`: CLI command that creates upload sessions against the backend API, displays a QR code for mobile upload, polls for completion, downloads the image locally, and copies the path to clipboard

### Modified Capabilities

_(none — no existing spec requirements change)_

## Impact

- **New module**: `modules/image-upload/default.nix` + scripts + help text
- **Packages**: adds `curl`, `jq`, `qrencode` as module dependencies
- **External dependency**: relies on the existing `upload.zolanic.space` backend service (no changes to that service)
- **Output directory**: creates `out/image-upload/` for downloaded images
- **No breaking changes** to existing modules or commands
