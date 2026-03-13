# CRM Module — LLM Context

Customer contract management stored in `data/crm.toml`. Uses `datalib` for loading, saving, and computed views.

## Data keys in crm.toml

- `customers` — counterparties (id, company, company_number, address, notes, created_at)
- `contacts` — people at customers (id, customer_id, name, email, role, notes, created_at)
- `contracts` — master contract records (id, customer_id, title, status, effective_date, term_months, auto_renew, payment_terms, currency, governing_law, jurisdiction, notice_period_days, notes, created_at)
- `contract_lines` — commercial line items (contract_id, seq, description, quantity, unit_price, frequency)
- `contract_clauses` — legal terms (contract_id, seq, heading, body)

## Computed views (via datalib)

- `datalib.contract_summary()` — contracts with MRR calculation, line/clause counts
- `datalib.renewals_due()` — active contracts expiring within 90 days

## Statuses

Contract: `draft` → `active` → `expired` | `terminated`

Line frequency: `monthly`, `quarterly`, `annual`, `one-off`

## Workflow: onboard a new customer

```bash
crm add acme "Acme Corp" 12345678
crm contact acme "Jane Smith" "jane@acme.com" "Head of Ops"
crm new acme "SaaS Subscription Agreement"
crm set ct-acme-1 effective-date 2026-04-01
crm set ct-acme-1 term 12
crm set ct-acme-1 auto-renew true
crm line ct-acme-1 1 "Platform licence" 200 monthly
crm standard-clauses ct-acme-1
crm pdf ct-acme-1
crm activate ct-acme-1
```

## Commands

Read:
- `crm customers` — list all customers
- `crm customer <id>` — customer detail
- `crm contracts [active|draft]` — list contracts
- `crm contract <id>` — contract detail
- `crm renewals` — contracts expiring within 90 days
- `crm find <term>` — search customers

Write:
- `crm add <id> "Company" [company-number]` — add a customer
- `crm contact <customer-id> "Name" "email" [role]` — add a contact
- `crm new <customer-id> "Title"` — create a draft contract
- `crm line <contract-id> <seq> "desc" <price> [frequency]` — add a line
- `crm clause <contract-id> <seq> "heading" "body"` — add a clause
- `crm standard-clauses <contract-id>` — add 12 standard clauses
- `crm set <contract-id> <field> <value>` — set contract field
- `crm activate <contract-id>` — mark contract as active

Output:
- `crm pdf <contract-id>` — generate contract PDF

## Standard Clauses

`crm standard-clauses` adds 12 clauses: Definitions, Services, Fees and Payment, Term and Renewal, Termination, IP, Confidentiality, Data Protection, Limitation of Liability, Force Majeure, General, Governing Law.

## Set Fields

Allowed: effective-date, term, auto-renew, payment-terms, currency, governing-law, jurisdiction, notice-period, status, notes.
