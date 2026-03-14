# Charges Module — LLM Context

Register of charges (secured loans and debentures) stored in `data/charges.yaml`. Uses `datalib` for loading, saving, and schema validation.

## Data keys in charges.yaml

- `charges` — charge records (id, charge_code, created_date, description, chargee, amount, currency, status, delivered_date, satisfied_date)

## Statuses

- `outstanding` — charge is active
- `satisfied` — charge has been discharged

## Commands

Read:
- `charges list` — list all charges with status
- `charges show <id>` — show charge details
- `charges check` — validate charge data

Write:
- `charges register <id> "description" <chargee> <amount>` — register a new charge
- `charges satisfy <id>` — mark charge as satisfied

Output:
- `charges pdf register` — generate register of charges PDF
