#!/usr/bin/env bash
set -euo pipefail

exec hledger -f "${SURFACE_ROOT}/modules/accounts/books/main.journal" "$@"
