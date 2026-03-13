# CRM Module — LLM Context

Lightweight CRM stored in Dolt alongside the ledger and cap table. Tracks customers (organisations), contacts (people), interactions, deals, and tags.

## Tables

- `customers` — customer organisations (id, company, pricing_plan, status, contract_start, contract_end, mrr_gbp, instance_id, notes, created_at)
- `contacts` — people we're talking to (id, customer_id, company, name, email, role, contact_role, source, stage, notes, created_at, last_contacted, next_action_date, next_action)
- `interactions` — logged touchpoints (contact_id, interaction_date, channel, direction, summary, follow_up)
- `deals` — revenue opportunities (id, contact_id, title, stage, value_gbp, recurring, opened_date, closed_date, lost_reason, notes)
- `tags` — freeform labels on contacts (contact_id, tag)

## Views

- `pipeline` — open deals grouped by stage with totals
- `stale_contacts` — leads/prospects not contacted in 14+ days
- `customer_overview` — customer orgs with contact count and won deal value
- `renewals_due` — customers with contracts ending within 90 days

## Stages

Contact stages: `lead` → `prospect` → `customer` | `churned` | `dormant`

Contact roles (within a customer): `champion`, `admin`, `billing`, `user`, `executive`

Customer statuses: `onboarding` → `active` | `churning` → `churned`

Deal stages: `qualifying` → `proposal` → `negotiation` → `closed-won` | `closed-lost`

## Workflow: add a new lead

```bash
data sql "INSERT INTO contacts (id, company, name, email, role, source, stage)
  VALUES ('acme-jane', 'Acme Corp', 'Jane Smith', 'jane@acme.com', 'Head of Ops', 'inbound', 'lead');"
data sql "INSERT INTO tags (contact_id, tag) VALUES ('acme-jane', 'fintech'), ('acme-jane', 'uk');"
data commit -m "add lead: Jane Smith at Acme Corp (inbound)"
```

## Workflow: log interaction and advance stage

```bash
crm log acme-jane "Intro call. They have 50+ forms across 3 depts."
# or manually:
data sql "INSERT INTO interactions (contact_id, interaction_date, channel, direction, summary)
  VALUES ('acme-jane', '2026-03-10', 'call', 'outbound', 'Intro call...');"
data sql "UPDATE contacts SET last_contacted = '2026-03-10', stage = 'prospect' WHERE id = 'acme-jane';"
data commit -m "call with Jane@Acme — moved to prospect"
```

## Workflow: close deal and create customer

When a deal closes, create the customer org and link contacts:

```bash
# 1. Create customer organisation
data sql "INSERT INTO customers (id, company, pricing_plan, status, contract_start, contract_end, mrr_gbp)
  VALUES ('acme', 'Acme Corp', 'standard', 'onboarding', '2026-04-01', '2027-04-01', 200.00);"

# 2. Link contacts to customer and set stage
data sql "UPDATE contacts SET customer_id = 'acme', stage = 'customer' WHERE id = 'acme-jane';"

# 3. Close the deal
data sql "UPDATE deals SET stage = 'closed-won', closed_date = '2026-04-01' WHERE id = 'acme-2026';"

data commit -m "closed-won: Acme Corp — customer created"
```

## Workflow: add more contacts to existing customer

```bash
data sql "INSERT INTO contacts (id, customer_id, company, name, email, role, contact_role, stage)
  VALUES ('acme-bob', 'acme', 'Acme Corp', 'Bob Chen', 'bob@acme.com', 'IT Admin', 'admin', 'customer');"
data commit -m "add contact: Bob Chen at Acme (admin)"
```

## Commands

Read:
- `crm pipeline` — pipeline overview (stages, counts, values)
- `crm contacts [active]` — list all or active contacts
- `crm customers [active|all]` — list customer organisations
- `crm customer <customer-id>` — customer detail (contacts, deals, activity)
- `crm renewals` — renewals due in next 90 days
- `crm stale` — contacts not contacted in 14+ days
- `crm find <term>` — search by company/name/tag
- `crm history <contact-id>` — interaction history
- `crm deals [won|lost]` — list deals

Write:
- `crm log <contact-id> "summary"` — guided interaction logging

Reports:
- `crm digest` — weekly digest (pipeline, stale, customers, actions, activity)
- `crm forecast` — weighted revenue forecast
