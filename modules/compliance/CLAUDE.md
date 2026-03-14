# Compliance Module — LLM Context

Statutory compliance calendar stored in `data/compliance.yaml`. Uses `datalib` for loading, saving, and computed views.

## Data keys in compliance.yaml

- `deadlines` — statutory filing deadlines (id, title, due_date, frequency, category, status, filed_date)

## Categories

- `companies-house` — Companies House filings
- `hmrc` — HMRC tax filings
- `other` — other statutory obligations

## Statuses

- `upcoming` — not yet due
- `filed` — completed
- `overdue` — past due date and not filed

## Computed views (via datalib)

- `datalib.compliance_upcoming()` — deadlines due within 90 days

## Commands

Read:
- `compliance upcoming` — deadlines within 90 days, colour-coded
- `compliance list [category]` — all deadlines
- `compliance check` — flag overdue items

Write:
- `compliance add <id> "title" <due-date> <frequency> <category>` — add deadline
- `compliance file <id>` — mark as filed

Output:
- `compliance pdf calendar` — annual compliance calendar PDF
