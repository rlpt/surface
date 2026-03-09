# Accounts Module — LLM Context

Double-entry bookkeeping stored in Dolt. Data lives in the `accounts`, `transactions`, and `postings` tables.

## Tables

- `accounts` — chart of accounts (path, account_type)
- `transactions` — transaction headers (txn_date, payee, description)
- `postings` — line items (txn_id, account_path, amount, currency)

## Views

- `account_balances` — aggregated balances per account

## Workflow: adding a transaction

1. Check valid accounts: `data sql "SELECT path FROM accounts ORDER BY path;"`
2. Insert the transaction:
   ```sql
   INSERT INTO transactions (txn_date, payee, description)
     VALUES ('2026-03-09', 'AWS', 'Monthly hosting');
   INSERT INTO postings (txn_id, account_path, amount)
     VALUES (LAST_INSERT_ID(), 'expenses:infra:hosting', 45.00);
   INSERT INTO postings (txn_id, account_path, amount)
     VALUES (LAST_INSERT_ID(), 'assets:bank:tide', -45.00);
   ```
3. Validate: `accounts check`
4. Commit: `data commit -m "add AWS hosting payment"`

Postings must sum to zero per transaction (double-entry). Positive = debit, negative = credit.

## Workflow: adding an account

```sql
INSERT INTO accounts (path, account_type) VALUES ('expenses:marketing:ads', 'expenses');
```

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

New accounts: INSERT into `accounts` table, then use in postings.
