## ADDED Requirements

### Requirement: Module provides image-upload command
The `image-upload` module SHALL register an `image-upload` shell command in the surface devShell via the module's `scripts` attribute.

#### Scenario: Command is available in devShell
- **WHEN** a user enters the surface devShell
- **THEN** the `image-upload` command SHALL be available on `PATH`

### Requirement: Upload session creation
The `image-upload` command SHALL create an upload session by sending a `POST` request to the backend API at `https://upload.zolanic.space/api/session` and SHALL extract the `session_id` and `upload_url` from the JSON response.

#### Scenario: Successful session creation
- **WHEN** the user runs `image-upload`
- **THEN** the command SHALL create a session and display the upload URL as a QR code in the terminal

#### Scenario: Backend unreachable
- **WHEN** the backend API returns an error or the `session_id` is null
- **THEN** the command SHALL print an error message and exit with code 1

### Requirement: QR code display
The command SHALL display the upload URL as a UTF-8 QR code in the terminal using `qrencode`, followed by the plaintext URL as a fallback.

#### Scenario: QR code shown after session creation
- **WHEN** a session is successfully created
- **THEN** the terminal SHALL display a scannable QR code and the plaintext URL

### Requirement: Poll for upload completion
The command SHALL poll `GET /<session_id>/status` every 2 seconds until the status is `ready` or a 5-minute timeout is reached. Progress dots SHALL be printed every 10 seconds.

#### Scenario: Image uploaded within timeout
- **WHEN** the backend status becomes `ready` within 5 minutes
- **THEN** the command SHALL proceed to download the image

#### Scenario: Timeout exceeded
- **WHEN** 5 minutes elapse without the status becoming `ready`
- **THEN** the command SHALL print a timeout error and exit with code 1

### Requirement: Image download to out directory
The command SHALL download the uploaded image to `$SURFACE_ROOT/out/image-upload/<session-id>/<filename>`, creating directories as needed.

#### Scenario: Successful download
- **WHEN** the upload status is `ready`
- **THEN** the command SHALL download the image from `GET /<session_id>/image` to the output path and print the local file path

### Requirement: Clipboard copy
The command SHALL copy the downloaded file path to the system clipboard using `pbcopy` when available.

#### Scenario: pbcopy available (macOS)
- **WHEN** the image is downloaded and `pbcopy` is on PATH
- **THEN** the file path SHALL be copied to the clipboard and a confirmation message printed

#### Scenario: pbcopy not available
- **WHEN** the image is downloaded and `pbcopy` is not on PATH
- **THEN** the command SHALL skip clipboard copy without error

### Requirement: Help output
The command SHALL display usage help when invoked with `help` as the first argument or with no arguments that trigger the upload flow.

#### Scenario: Help displayed
- **WHEN** the user runs `image-upload help`
- **THEN** the command SHALL print a usage summary and exit 0

### Requirement: Module declares dependencies
The module SHALL declare `curl`, `jq`, and `qrencode` in its `packages` list so they are available in the devShell.

#### Scenario: Dependencies available
- **WHEN** the module is loaded
- **THEN** `curl`, `jq`, and `qrencode` SHALL be on PATH in the devShell

### Requirement: Module provides help text for halp
The module SHALL provide a `helpText` attribute so the `halp` command includes image-upload in its output.

#### Scenario: halp includes image-upload
- **WHEN** the user runs `halp`
- **THEN** the output SHALL include the image-upload command and its description
