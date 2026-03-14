# Officers Module — LLM Context

Company officers register stored in `data/officers.yaml`. Uses `datalib` for loading, saving, and schema validation.

## Data keys in officers.yaml

- `officers` — officer records (id, person_name, role, appointed_date, resigned_date)

## Roles

- `director` — company director
- `secretary` — company secretary
- `psc` — person with significant control

## Commands

Read:
- `officers list` — current officers with roles and dates
- `officers history` — full appointment/resignation history
- `officers check` — validate officer data

Write:
- `officers appoint <id> "Name" <role>` — appoint a new officer
- `officers resign <id>` — record officer resignation

Output:
- `officers pdf register` — generate register of directors PDF
