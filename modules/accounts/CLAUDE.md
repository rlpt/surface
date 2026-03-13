# Accounts Module — LLM Context

Double-entry bookkeeping stored in `data/accounts.toml`. Uses `datalib` for loading and computed views.

## Data keys in accounts.toml

- `accounts` — chart of accounts (path, account_type)
- `transactions` — transaction headers (id, txn_date, payee, description)
- `postings` — line items (txn_id, account_path, amount, currency)

## Computed views (via datalib)

- `datalib.account_balances()` — aggregated balances per account

## Workflow: adding a transaction

Edit `data/accounts.toml` directly:

```toml
[[transactions]]
id = 1
txn_date = "2026-03-09"
payee = "AWS"
description = "Monthly hosting"

[[postings]]
txn_id = 1
account_path = "expenses:infra:hosting"
amount = 45.00
currency = "GBP"

[[postings]]
txn_id = 1
account_path = "assets:bank:tide"
amount = -45.00
currency = "GBP"
```

Then validate and commit:
```bash
accounts check
git add data/ && git commit -m "add AWS hosting payment"
```

Postings must sum to zero per transaction (double-entry). Positive = debit, negative = credit.

## Common commands

- `accounts bal` — current balances across all accounts
- `accounts bal expenses:infra` — balance for a subtree
- `accounts is [-p period]` — income statement
- `accounts bs` — balance sheet
- `accounts reg <acct>` — transaction register for an account
- `accounts stats` — account and transaction counts
- `accounts check` — validate balanced entries and declared accounts
- `accounts list` — list all declared accounts

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
