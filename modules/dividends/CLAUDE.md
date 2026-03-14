# Dividends Module — LLM Context

Dividend declarations and payments stored in `data/dividends.yaml`. Uses `datalib` for loading, saving, and schema validation.

## Data keys in dividends.yaml

- `dividends` — dividend records (id, declaration_date, payment_date, share_class, amount_per_share, currency, tax_voucher_ref, status, resolution_id)

## Statuses

- `declared` — dividend declared but not yet paid
- `paid` — dividend paid to shareholders
- `cancelled` — dividend cancelled

## Commands

Read:
- `dividends list` — list all dividends
- `dividends show <id>` — show dividend details
- `dividends check` — validate dividend data

Write:
- `dividends declare <class> <amount> [resolution_id]` — declare a dividend
- `dividends pay <id>` — mark dividend as paid

Output:
- `dividends pdf register` — generate dividend register PDF
- `dividends pdf voucher <id>` — generate tax voucher PDF with per-holder amounts
