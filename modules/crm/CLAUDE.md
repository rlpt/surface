# CRM Module — LLM Context

Lightweight CRM stored in Dolt alongside the ledger and cap table. Tracks contacts, interactions, deals, and tags.

## Tables

- `contacts` — companies/people we're talking to (id, company, name, email, role, source, stage, notes, created_at, last_contacted, next_action_date, next_action)
- `interactions` — logged touchpoints (contact_id, interaction_date, channel, direction, summary, follow_up)
- `deals` — revenue opportunities (id, contact_id, title, stage, value_gbp, recurring, opened_date, closed_date, lost_reason, notes)
- `tags` — freeform labels on contacts (contact_id, tag)

## Views

- `pipeline` — open deals grouped by stage with totals
- `stale_contacts` — leads/prospects not contacted in 14+ days

## Stages

Contact stages: `lead` → `prospect` → `customer` | `churned` | `dormant`

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

## Workflow: create and close a deal

```bash
data sql "INSERT INTO deals (id, contact_id, title, stage, value_gbp, recurring)
  VALUES ('acme-2026', 'acme-jane', 'Acme Corp — form engine', 'qualifying', 2400.00, 'annual');"
data commit -m "open deal: Acme Corp annual (£2,400)"

# Later:
data sql "UPDATE deals SET stage = 'closed-won', closed_date = '2026-04-01' WHERE id = 'acme-2026';"
data sql "UPDATE contacts SET stage = 'customer' WHERE id = 'acme-jane';"
data commit -m "closed-won: Acme Corp"
```

## Commands

Read:
- `crm pipeline` — pipeline overview (stages, counts, values)
- `crm contacts [active]` — list all or active contacts
- `crm stale` — contacts not contacted in 14+ days
- `crm find <term>` — search by company/name/tag
- `crm history <contact-id>` — interaction history
- `crm deals [won|lost]` — list deals

Write:
- `crm log <contact-id> "summary"` — guided interaction logging

Reports:
- `crm digest` — weekly digest (pipeline, stale, actions, activity)
- `crm forecast` — weighted revenue forecast
