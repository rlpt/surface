## 1. Module scaffold

- [x] 1.1 Create `modules/accounts/default.nix` declaring name, description, and `pkgs.hledger` as package
- [x] 1.2 Create `modules/accounts/books/` directory
- [x] 1.3 Create `modules/accounts/books/accounts.journal` with initial chart of accounts
- [x] 1.4 Create `modules/accounts/books/main.journal` with includes for accounts.journal and year files
- [x] 1.5 Create empty year files: `2024.journal`, `2025.journal`, `2026.journal`
- [x] 1.6 Verify: `nix develop` picks up the module and `hledger --version` works

## 2. Journal validation

- [x] 2.1 Run `hledger -f modules/accounts/books/main.journal stats` — confirm it parses without error
- [x] 2.2 Run `hledger -f modules/accounts/books/main.journal check accounts` — confirm all postings use declared accounts

## 3. Shell integration

- [x] 3.1 Add `accounts` script to `scripts/` that wraps `hledger -f $SURFACE_ROOT/modules/accounts/books/main.journal "$@"`
- [x] 3.2 Update `halp.sh` to list the `accounts` command

## 4. LLM context

- [x] 4.1 Create `modules/accounts/CLAUDE.md` documenting journal conventions, account tree, common hledger commands, and the read-then-append workflow
- [x] 4.2 Document validation step: always run `hledger check` after writing entries
