# CRM Module — LLM Context

Customer contract management stored in Dolt. Define commercial relationships as structured data, output legal documents as PDF.

## Tables

- `customers` — counterparties (id, company, company_number, address, notes, created_at)
- `contacts` — people at customers (id, customer_id, name, email, role, notes, created_at)
- `contracts` — master contract records (id, customer_id, title, status, effective_date, term_months, auto_renew, payment_terms, currency, governing_law, jurisdiction, notice_period_days, notes, created_at)
- `contract_lines` — commercial line items (contract_id, seq, description, quantity, unit_price, frequency)
- `contract_clauses` — legal terms (contract_id, seq, heading, body)

## Views

- `contract_summary` — contracts with MRR calculation, line/clause counts
- `renewals_due` — active contracts expiring within 90 days

## Statuses

Contract: `draft` → `active` → `expired` | `terminated`

Line frequency: `monthly`, `quarterly`, `annual`, `one-off`

## Workflow: onboard a new customer and create a contract

```bash
# 1. Add the customer
crm add acme "Acme Corp" 12345678

# 2. Add a contact
crm contact acme "Jane Smith" "jane@acme.com" "Head of Ops"

# 3. Create a draft contract
crm new acme "SaaS Subscription Agreement"

# 4. Set commercial terms
crm set ct-acme-1 effective-date 2026-04-01
crm set ct-acme-1 term 12
crm set ct-acme-1 auto-renew true
crm set ct-acme-1 payment-terms net-30

# 5. Add service lines
crm line ct-acme-1 1 "Platform licence — Standard plan" 200 monthly
crm line ct-acme-1 2 "Onboarding & training" 1500 one-off

# 6. Add standard legal clauses
crm standard-clauses ct-acme-1

# 7. Generate contract PDF
crm pdf ct-acme-1

# 8. Once signed, activate
crm activate ct-acme-1
```

## Commands

Read:
- `crm customers` — list all customers
- `crm customer <customer-id>` — customer detail (contacts, contracts)
- `crm contracts [active|draft]` — list contracts
- `crm contract <contract-id>` — contract detail (terms, lines, clauses)
- `crm renewals` — contracts expiring within 90 days
- `crm find <term>` — search customers by name

Write:
- `crm add <id> "Company" [company-number]` — add a customer
- `crm contact <customer-id> "Name" "email" [role]` — add a contact
- `crm new <customer-id> "Contract Title"` — create a draft contract
- `crm line <contract-id> <seq> "desc" <price> [frequency]` — add a line item
- `crm clause <contract-id> <seq> "heading" "body"` — add a custom clause
- `crm standard-clauses <contract-id>` — add standard legal clauses (12 clauses)
- `crm set <contract-id> <field> <value>` — set contract field
- `crm activate <contract-id>` — mark contract as active

Output:
- `crm pdf <contract-id>` — generate contract PDF (→ downloads/)

## Standard Clauses

`crm standard-clauses` adds 12 boilerplate clauses: Definitions, Services, Fees and Payment, Term and Renewal, Termination, Intellectual Property, Confidentiality, Data Protection, Limitation of Liability, Force Majeure, General, Governing Law and Jurisdiction. These can be customised per contract by updating the clause body via `data sql`.

## Set Fields

Allowed fields for `crm set`: effective-date, term, auto-renew, payment-terms, currency, governing-law, jurisdiction, notice-period, status, notes.
