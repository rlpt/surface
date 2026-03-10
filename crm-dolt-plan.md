# CRM in Dolt

Formabi's CRM lives in the same Dolt database as the ledger and cap table. No separate tool. The company-as-code principle: if it has identity and lifecycle, it goes in Dolt.

## Why

We sell to a small number of high-value customers. We don't need Salesforce. We need a queryable, version-controlled record of every company we're talking to, what we've said, and what happens next. Something an LLM can read and act on.

Dolt gives us:
- Full history of every relationship (`dolt log --tables contacts`)
- Branch to model scenarios (`dolt checkout -b what-if-acme-churns`)
- Diff pipeline changes day over day (`dolt diff HEAD~1 HEAD --tables deals`)
- SQL queries from any shell, any script, any LLM
- No vendor lock-in, no per-seat pricing, no API rate limits

## Schema

Extends the existing surface data module (`modules/data/schema.sql`). Four new tables, two new views.

```sql
-- ============================================================
-- CRM
-- ============================================================

CREATE TABLE contacts (
  id VARCHAR(50) PRIMARY KEY,
  company VARCHAR(200) NOT NULL,
  name VARCHAR(200) NOT NULL,
  email VARCHAR(200),
  role VARCHAR(100),
  source VARCHAR(50),              -- inbound, referral, outbound, event
  stage VARCHAR(20) NOT NULL DEFAULT 'lead'
    CHECK (stage IN ('lead', 'prospect', 'customer', 'churned', 'dormant')),
  notes TEXT,
  created_at DATE NOT NULL DEFAULT (CURRENT_DATE),
  last_contacted DATE,
  next_action_date DATE,
  next_action TEXT
);

CREATE TABLE interactions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  contact_id VARCHAR(50) NOT NULL,
  interaction_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  channel VARCHAR(20) NOT NULL
    CHECK (channel IN ('email', 'call', 'meeting', 'demo', 'slack', 'event', 'other')),
  direction VARCHAR(10) NOT NULL DEFAULT 'outbound'
    CHECK (direction IN ('inbound', 'outbound')),
  summary TEXT NOT NULL,
  follow_up TEXT,
  FOREIGN KEY (contact_id) REFERENCES contacts(id),
  INDEX idx_interaction_date (interaction_date)
);

CREATE TABLE deals (
  id VARCHAR(50) PRIMARY KEY,
  contact_id VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  stage VARCHAR(20) NOT NULL DEFAULT 'qualifying'
    CHECK (stage IN ('qualifying', 'proposal', 'negotiation', 'closed-won', 'closed-lost')),
  value_gbp DECIMAL(10,2),
  recurring VARCHAR(10) CHECK (recurring IN ('monthly', 'annual', 'one-off')),
  opened_date DATE NOT NULL DEFAULT (CURRENT_DATE),
  closed_date DATE,
  lost_reason TEXT,
  notes TEXT,
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE tags (
  contact_id VARCHAR(50) NOT NULL,
  tag VARCHAR(50) NOT NULL,
  PRIMARY KEY (contact_id, tag),
  FOREIGN KEY (contact_id) REFERENCES contacts(id)
);
```

### Views

```sql
CREATE VIEW pipeline AS
SELECT
  d.stage,
  COUNT(*) AS deals,
  SUM(d.value_gbp) AS total_value,
  GROUP_CONCAT(c.company ORDER BY d.value_gbp DESC) AS companies
FROM deals d
JOIN contacts c ON c.id = d.contact_id
WHERE d.stage NOT IN ('closed-won', 'closed-lost')
GROUP BY d.stage
ORDER BY FIELD(d.stage, 'qualifying', 'proposal', 'negotiation');

CREATE VIEW stale_contacts AS
SELECT
  id, company, name, stage, last_contacted, next_action, next_action_date
FROM contacts
WHERE stage IN ('lead', 'prospect')
  AND (last_contacted IS NULL OR last_contacted < DATE_SUB(CURRENT_DATE, INTERVAL 14 DAY))
ORDER BY last_contacted ASC;
```

### Relationship to existing tables

The `contacts` table is the CRM view of relationships. The `customers` table (if/when we add it to surface) is the operational view of provisioned instances. A contact becomes a customer when their deal closes:

```
contact (stage=prospect) → deal (stage=closed-won) → customer (provisioned instance)
```

The CRM tracks the relationship. The customer record tracks the running service. They link by company name or a foreign key.

## Commands

New commands added to the surface shell, following the existing pattern (`accounts bal`, `shares cap`, `data sql`):

```bash
# Pipeline overview
crm pipeline                     # pipeline view — stages, counts, values

# Contact management
crm contacts                     # list all contacts
crm contacts active              # leads + prospects with upcoming actions
crm stale                        # contacts we haven't talked to in 14+ days
crm find <term>                  # search contacts by company/name/tag

# Interactions
crm log <contact-id> "summary"   # log an interaction (prompts for channel)
crm history <contact-id>         # show interaction history for a contact

# Deals
crm deals                        # list open deals
crm deals won                    # closed-won deals
crm deals lost                   # closed-lost deals with reasons

# Reporting
crm digest                       # weekly digest: pipeline, stale, next actions
crm forecast                     # revenue forecast from pipeline

# Raw SQL (escape hatch)
data sql "SELECT * FROM contacts WHERE company LIKE '%acme%';"
```

## Workflows

### New lead comes in

```bash
data sql "INSERT INTO contacts (id, company, name, email, role, source, stage)
  VALUES ('acme-jane', 'Acme Corp', 'Jane Smith', 'jane@acme.com', 'Head of Ops', 'inbound', 'lead');"
data sql "INSERT INTO tags (contact_id, tag) VALUES ('acme-jane', 'fintech'), ('acme-jane', 'uk');"
data commit -m "add lead: Jane Smith at Acme Corp (inbound)"
```

### Log an interaction

```bash
data sql "INSERT INTO interactions (contact_id, interaction_date, channel, direction, summary, follow_up)
  VALUES ('acme-jane', '2026-03-10', 'call', 'outbound', 'Intro call. They have 50+ complex forms across 3 departments. Current solution is PDF + email.', 'Send product overview deck');"
data sql "UPDATE contacts SET last_contacted = '2026-03-10', stage = 'prospect',
  next_action = 'Send deck + book demo', next_action_date = '2026-03-12'
  WHERE id = 'acme-jane';"
data commit -m "call with Jane@Acme — moved to prospect, demo next week"
```

### Create a deal

```bash
data sql "INSERT INTO deals (id, contact_id, title, stage, value_gbp, recurring)
  VALUES ('acme-2026', 'acme-jane', 'Acme Corp — form engine rollout', 'qualifying', 2400.00, 'annual');"
data commit -m "open deal: Acme Corp annual (£2,400)"
```

### Close a deal

```bash
data sql "UPDATE deals SET stage = 'closed-won', closed_date = '2026-04-01' WHERE id = 'acme-2026';"
data sql "UPDATE contacts SET stage = 'customer' WHERE id = 'acme-jane';"
data commit -m "closed-won: Acme Corp"
```

### Review pipeline

```bash
data sql "SELECT * FROM pipeline;"
data sql "SELECT * FROM stale_contacts;"
dolt diff HEAD~7 HEAD --tables deals    # what changed this week
```

## Vibe coding it

The CRM is designed to be extended by conversation. Because the schema is SQL and the data is in Dolt, Claude can:

1. **Add fields** — "add a `tier` column to contacts" → ALTER TABLE + backfill
2. **Build reports** — "show me revenue by source" → SQL query, optionally saved as a view
3. **Create automations** — "email me every Monday with stale contacts" → shell script + cron
4. **Enrich data** — "look up company info for all contacts missing a website" → script that queries + updates
5. **Model scenarios** — "what does the pipeline look like if we lose the two biggest deals?" → dolt branch, update, query, discard

The CLAUDE.md in the data module already teaches the LLM the conventions. We extend it with CRM context.

## Implementation plan

### Phase 1 — Schema + seed (now)

1. Add CRM tables to `modules/data/schema.sql`
2. Add seed data for existing contacts (port from wherever they live today)
3. Add views (`pipeline`, `stale_contacts`)
4. Run `data reset` to rebuild

### Phase 2 — Shell commands

1. Create `modules/crm/` module with scripts
2. `crm pipeline`, `crm contacts`, `crm stale`, `crm find`
3. `crm log` — guided interaction logging (prompts for channel, summary)
4. `crm digest` — weekly summary

### Phase 3 — LLM integration

1. Add CRM context to `modules/crm/CLAUDE.md`
2. Claude can query and update the CRM directly via `data sql`
3. "What's the status with Acme?" → reads contacts + interactions + deals
4. "Draft a follow-up email to Jane at Acme" → reads last interaction, writes in formabi voice
5. "Update the pipeline — we lost the Acme deal, they went with Typeform" → UPDATE + commit

### Phase 4 — Automation

1. `crm digest` as a weekly cron job (outputs markdown, optionally sends to Slack/email)
2. Stale contact alerts
3. Stripe sync — pull payment status into deal records
4. Connect to latice's billing: when a deal closes in the CRM, create the customer in the product

## What we're not building

- No web UI. The shell and SQL are the interface. LLMs are the UX layer.
- No email integration. Log interactions manually or via scripts.
- No permissions model. Everyone in the guild can see and edit everything. Dolt commit log is the audit trail.
- No marketing automation. We're 3 people selling to a small number of companies.

## Fits the architecture

```
surface/
├── modules/
│   ├── data/           ← Dolt database (existing)
│   │   ├── schema.sql  ← add CRM tables here
│   │   └── seed.sql    ← add CRM seed data here
│   ├── accounts/       ← double-entry bookkeeping (existing)
│   ├── shares/         ← cap table (existing)
│   └── crm/            ← new module
│       ├── default.nix ← shell commands
│       ├── CLAUDE.md   ← LLM context
│       └── scripts/
│           ├── crm.sh         ← main CLI (pipeline, contacts, stale, find, log, etc.)
│           └── crm-digest.sh  ← weekly digest generator
```

The CRM is just another module that reads from and writes to the same Dolt database. Same `data sql`, same `data commit`, same `data diff`. No new infrastructure. Just new tables and scripts.
