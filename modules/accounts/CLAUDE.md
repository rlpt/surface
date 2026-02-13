# Accounts Module — LLM Context

Plain-text double-entry bookkeeping using hledger. Journals live at `modules/accounts/books/`.

## File layout

- `main.journal` — entry point, includes everything below
- `accounts.journal` — chart of accounts (all `account` declarations)
- `2024.journal`, `2025.journal`, `2026.journal` — transactions by year

## Workflow: adding a transaction

1. Read `accounts.journal` to find the correct account names
2. Read the current year file to match the existing style
3. Append the new transaction to the current year file
4. Run `hledger -f modules/accounts/books/main.journal check` to validate

Always follow this order. Never skip the validation step.

## Transaction format

```journal
2026-02-07 Stripe | Customer payments payout
    assets:bank:tide              £1,840.00
    revenue:sales
```

- Date: `YYYY-MM-DD`
- Payee and description separated by ` | `
- Four-space indent for postings
- Currency symbol before amount, no space (`£34.21`)
- One blank line between transactions
- Second posting amount can be omitted (hledger infers the balancing amount)

## Common hledger commands

All commands use `-f modules/accounts/books/main.journal` (or the `accounts` shell alias).

- `accounts bal` — current balances across all accounts
- `accounts bal expenses:infra` — balance for a subtree
- `accounts is -p 'feb 2026'` — income statement for a period
- `accounts bs` — balance sheet
- `accounts reg assets:bank:tide` — transaction register for an account
- `accounts stats` — journal health (date range, txn count)
- `accounts check` — validate balanced entries and declared accounts
- `accounts check accounts` — specifically check all postings use declared accounts

## Account tree (current)

```
assets:bank:tide, assets:bank:savings
liabilities:cc:business, liabilities:tax:vat, liabilities:tax:corp
expenses:infra:{hosting,cloud,domains}
expenses:tools:{design,dev}
expenses:admin:{compliance,insurance}
expenses:travel
expenses:payroll:{salary,pension}
revenue:{sales,consulting}
equity:opening-balances
```

New accounts: add to `accounts.journal`, then use in transactions.
