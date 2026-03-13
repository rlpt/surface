# Formabi as Code

The repo IS the company. The system is called **formabi**. It is a **guild** — a group of craftspeople who share a workspace, tools, and a ledger.

- **The server** — a single large dedicated machine. The guild hall. Everyone SSHs in, works, and collaborates here. NixOS makes it declarative and reproducible.
- **devenv** — the workbench. Provides each guild member with the right tools for their craft, scoped by role.
- **Dolt** — the ledger. A SQL database with git-like version control. Branch, merge, diff, time travel. The source of truth for anything with identity (people, customers, instances).
- **Git** — tracks configuration, knowledge, decisions, infrastructure. Every change is a commit.
- **SSH** — how you enter the guild hall. Your key is your identity.

Read the repo and you become formabi — you know the mission, the people, the customers, the architecture, the current priorities, and how to make decisions consistent with how formabi operates. SSH into the server and you can query state, make changes, and deploy. Human or LLM — the interface is the same. The company is the program.

Three formats, each for what it's best at:
- **Dolt (SQL)** — structured entity data with built-in versioning. People, customers, instances — anything with identity and lifecycle. `dolt log`, `dolt diff`, `dolt sql -q "SELECT * FROM roster"`. Branch for proposals, merge to apply.
- **Markdown** — company knowledge (mission, processes, voice, decisions, context). Human-readable, LLM-native.
- **Nix** — infrastructure and composition (shells, servers, builds). Reads from Dolt and JSON, produces reproducible outputs.

Git and Dolt together form the company's memory. Git tracks config and prose. Dolt tracks entity data. Both are versioned, diffable, and time-travelable.

## Principles

1. **The LLM never has more permissions than the active user.** This is the hard rule. The LLM runs in the user's shell, with the user's repos, the user's role, the user's git identity. It cannot see repos the user hasn't cloned. It cannot make changes the user's role doesn't allow. It cannot deploy if the user doesn't have ops access. The LLM is never a privilege escalation vector — it is always bounded by the human sitting at the keyboard.
2. **One server, shared workspace** — Everyone SSHs into the same machine. Unix users, groups, and file permissions enforce boundaries. The server IS the company.
3. **Separate repos are the security boundary** — GitHub/Forgejo permissions control who sees what. The root flake never references private repos as inputs.
4. **Works with any/all modules missing** — Zero repos cloned = base shell still works. It never fails, it just gives you less.
5. **One definition, two targets** — `people/alice.nix` produces her devenv shell AND her server access. Change it once, both sides update.
6. **Dolt for entities, markdown for knowledge, nix for infra** — Each format for what it's best at. Dolt gives you SQL + version control without custom tooling.
7. **Git is the audit log** — Every change to roles, servers, and instances is a commit with a reviewer. Dolt provides its own audit log for entity data.
8. **KISS** — Simple files. No custom tooling beyond shell scripts. Dolt replaces the need for custom transact/derive tools.

## The Big Idea

Today you already have two halves:

- **Local**: devenv shells per-repo, each configured independently
- **Server**: NixOS on the server (currently called formrunner), declared in cmdr/deploy/, deployed with deploy-rs

These halves don't know about each other. `users.nix` on the server has hardcoded SSH keys. `devenv.nix` in each repo has hardcoded tools. There's no shared definition of "who works here" or "what they can do."

The idea: a **root flake** that is the single source of truth for the company. It evaluates differently depending on the target:

```
formabi (root flake)
  │
  ├── nix develop .#alice     → devenv shell with her tools, repos, AI context
  ├── nix develop .#ops       → devenv shell for ops role (anyone)
  │
  ├── nixosConfigurations     → server configs that read the same people/roles
  │     └── server            → SSH keys, unix users, services — all derived
  │
  └── packages                → built artifacts (app binary, deck html, etc.)
```

One `people/alice.nix` file produces:
- Her devenv shell (tools for her roles)
- Her SSH authorized key on the server
- Her unix user on the server
- Her CLAUDE.md context
- Her entry in the company handbook "team" page

Change it in one place, deploy, done.

## Architecture

### Directory Layout

```
formabi/                              ← root repo — the company
├── flake.nix                         ← nix composition layer
├── flake.lock
│
├── identity/                         ← WHO formabi is (markdown — LLM context)
│   ├── mission.md                    ← why we exist, what we believe
│   ├── voice.md                      ← how we communicate (tone, style, patterns)
│   └── processes.md                  ← how we work (async-first, ship small, etc.)
│
├── brand/                            ← visual identity (JSON — machine-readable)
│   └── brand.json                    ← { name, strapline, colors, fonts }
│
├── people/                           ← WHO works here
│   └── default.nix                   ← reads from Dolt roster table, exposes to nix
│
├── roles/                            ← WHAT each role can do
│   ├── engineering.nix               ← repos, tools, server access, AI context scope
│   ├── ops.nix
│   ├── sales.nix
│   ├── design.nix
│   └── default.nix                   ← role registry
│
├── state/                            ← WHERE the company is right now (manual JSON)
│   ├── stage.json                    ← { stage, runway_months, funding, focus }
│   ├── priorities.json               ← ordered list: what matters this quarter
│   └── metrics.json                  ← { mrr, active_users, instances, uptime }
│
├── decisions/                        ← WHY we chose what we chose (markdown + index)
│   ├── index.json                    ← [ { id, title, date, status, file } ]
│   ├── 001-elm-frontend.md           ← decision record
│   ├── 002-datalog-architecture.md
│   └── 003-nix-for-infra.md
│
├── modules/                          ← one per sibling repo (nix)
│   ├── app.nix                       ← formabi-app: elm, rust, node
│   ├── cmdr.nix                      ← cmdr: deploy, secrets
│   ├── deck.nix                      ← deck: marp, presentations
│   ├── latice.nix                    ← latice: rust SOA template
│   └── zolanic.nix                   ← zolanic: astro, brand
│
├── server/                           ← NixOS configs (nix)
│   ├── configuration.nix
│   ├── hardware-configuration.nix
│   └── shared/
│       ├── common.nix
│       ├── users.nix                 ← derived from Dolt roster table
│       ├── services.nix              ← derived from Dolt customers table
│       └── forgejo.nix
│
├── context/                          ← AI context fragments (markdown, per-role)
│   ├── base.md                       ← assembled for everyone
│   ├── app.md                        ← engineering sees this
│   ├── ops.md                        ← ops sees this
│   └── sales.md                      ← sales sees this
│
├── secrets/                          ← agenix-encrypted
│   ├── secrets.nix                   ← who can decrypt what (derived from roles)
│   └── *.age                         ← encrypted secret files
│
├── base/
│   └── default.nix                   ← always-on: git, dolt, halp, whoami, onboard
│
└── scripts/
    ├── onboard.sh
    ├── whoami.sh
    └── halp.sh
```

### The Three Layers

```
┌──────────────────────────────────────────────────────────┐
│  KNOWLEDGE (markdown)                                    │
│  identity/mission.md, identity/voice.md,                 │
│  decisions/*.md, context/*.md                            │
│  → LLM reads this and becomes formabi                    │
├──────────────────────────────────────────────────────────┤
│  ENTITIES (Dolt — SQL + git versioning)                  │
│                                                          │
│  roster table     — people, roles, SSH keys, regions     │
│  customers table  — name, domain, tier, port, status     │
│  instances table  — provisioned workspaces               │
│                                                          │
│  Built-in: branch, merge, diff, log, time travel         │
│  Query: dolt sql -q "SELECT * FROM roster"               │
│  History: dolt log, dolt diff HEAD~1 HEAD                │
│  Propose: dolt checkout -b hire-dave, make changes,      │
│           dolt merge hire-dave                            │
│                                                          │
│  NARRATIVE (manual json)                                 │
│  state/stage.json, state/priorities.json                 │
│  brand/brand.json, decisions/index.json                  │
│  → high-level company state, maintained directly         │
├──────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE (nix)                                    │
│  flake.nix, roles/*.nix, modules/*.nix,                  │
│  server/**/*.nix, base/default.nix                       │
│  → reads Dolt + JSON, produces shells + servers          │
└──────────────────────────────────────────────────────────┘
         │
         │  git log + dolt log
         ▼
    HISTORY
    every Dolt commit, every JSON change, every nix edit
    is versioned with an author and a reason
```

### People (Dolt — SQL with version control)

```sql
-- roster table in Dolt
CREATE TABLE roster (
  id VARCHAR(26) PRIMARY KEY,   -- ULID, generated by Dolt
  name VARCHAR(255) NOT NULL,
  github VARCHAR(255),
  email VARCHAR(255) UNIQUE NOT NULL,
  region VARCHAR(50),
  started DATE NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

CREATE TABLE person_roles (
  person_id VARCHAR(26) REFERENCES roster(id),
  role VARCHAR(50) NOT NULL,
  PRIMARY KEY (person_id, role)
);

CREATE TABLE ssh_keys (
  person_id VARCHAR(26) REFERENCES roster(id),
  key_type VARCHAR(50) NOT NULL,
  public_key TEXT NOT NULL,
  PRIMARY KEY (person_id, key_type)
);
```

```bash
# Query the guild roster
dolt sql -q "SELECT r.name, r.email, r.region, GROUP_CONCAT(pr.role) as roles
             FROM roster r
             JOIN person_roles pr ON r.id = pr.person_id
             WHERE r.active = TRUE
             GROUP BY r.id"

# Who has ops access?
dolt sql -q "SELECT r.name FROM roster r
             JOIN person_roles pr ON r.id = pr.person_id
             WHERE pr.role = 'ops' AND r.active = TRUE"
```

Why Dolt:
- SQL is universal — any LLM can query it, any tool can consume it
- Git-like versioning built in — `dolt log`, `dolt diff`, `dolt blame`
- Branch for proposals: `dolt checkout -b hire-dave`, make changes, `dolt merge`
- Time travel: `SELECT * FROM roster AS OF 'HEAD~5'`
- No custom tooling needed — no `formabi-transact`, no `formabi-derive`
- Nix can export to JSON at build time: `dolt sql -q "SELECT ..." -r json`
- Diffable history — hiring/offboarding shows as clear SQL diffs

One roster entry feeds:

| Consumer | What it produces |
|----------|-----------------|
| Nix (local) | devenv shell with engineering + ops tools, repos, AI context |
| Nix (server) | Unix user with SSH key, wheel group (because ops role) |
| Nix (secrets) | agenix access scoped to role |
| LLM | "Alice is an engineer and ops lead in the UK region" |
| Handbook | Team page with name, role, region |
| SQL | Queryable from any shell: `dolt sql -q "SELECT name FROM roster"` |

### Company State (manual JSON — current snapshot)

```json
// state/stage.json
{
  "stage": "pre-seed",
  "focus": "product-market fit",
  "runway_months": 18,
  "team_size": 3,
  "model": "follow-the-sun, 3 product engineers"
}
```

```json
// state/priorities.json
[
  "Ship form engine v1 — complete fill/submit flow",
  "Land 3 pilot customers",
  "Hire Singapore product engineer"
]
```

Customers live in Dolt (entity data with identity), not in JSON:

```sql
-- customers table in Dolt
CREATE TABLE customers (
  id VARCHAR(26) PRIMARY KEY,
  name VARCHAR(255) UNIQUE NOT NULL,
  domain VARCHAR(255) NOT NULL,
  port INTEGER NOT NULL,
  tier VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'active',
  provisioned DATE NOT NULL
);
```

```bash
# List active customers
dolt sql -q "SELECT name, domain, tier, status FROM customers WHERE status = 'active'"

# When was acme provisioned?
dolt sql -q "SELECT name, provisioned FROM customers WHERE name = 'acme-corp'"

# Customer history via Dolt log
dolt log --tables customers
```

This data feeds everything:
- **Nix server config** reads customers (exported as JSON) to generate systemd services + nginx vhosts
- **LLM** reads stage.json and priorities.json to make decisions aligned with current focus
- **Pitch decks** can pull live metrics
- **Onboard script** shows new hires what's happening right now

### Decisions (Markdown + JSON Index)

```json
// decisions/index.json
[
  { "id": "001", "title": "Elm for frontend", "date": "2024-06-15", "status": "accepted" },
  { "id": "002", "title": "Datalog-style EAV architecture", "date": "2024-07-01", "status": "accepted" },
  { "id": "003", "title": "Nix for reproducible infra", "date": "2024-08-20", "status": "accepted" },
  { "id": "004", "title": "Follow-the-sun 3-engineer model", "date": "2024-09-10", "status": "accepted" }
]
```

```markdown
<!-- decisions/001-elm-frontend.md -->
# Elm for Frontend

**Date**: 2024-06-15
**Status**: Accepted

## Context
We need a frontend language for a complex form builder with rich state management.

## Decision
Use Elm 0.19.1. Its type system catches entire categories of bugs at compile time.
No runtime exceptions means fewer production incidents for a small team.

## Consequences
- Smaller hiring pool (Elm developers are rare)
- Excellent refactoring confidence
- No JS interop pain for most features
```

Why this matters for LLMs: when an LLM encounters a design question, it can read the decision log and understand *why* things are the way they are. It won't suggest "let's switch to React" because it knows the reasoning behind Elm. It won't propose a relational schema because it knows the datalog decision.

### Brand (JSON)

```json
// brand/brand.json
{
  "name": "Formabi",
  "strapline": "Complex Forms Made Easy",
  "colors": {
    "bg": "#0a0a1a",
    "bg-card": "#16162a",
    "primary": "#6366f1",
    "primary-mid": "#8b5cf6",
    "accent": "#a78bfa",
    "text": "#e0e0e0",
    "muted": "#888",
    "border": "#2a2a4a"
  }
}
```

Consumed by:
- `deck/flake.nix` for slide themes (already uses this exact color scheme)
- `zolanic/` for website styling
- Handbook generator
- LLMs when generating UI code or marketing copy

### Company Identity (Markdown — the LLM soul)

```markdown
<!-- identity/mission.md -->
# Mission

Formabi makes complex forms easy. We build tools that turn painful,
multi-step form workflows into something people actually enjoy using.

We believe forms are underserved infrastructure. Every industry has them.
Most form tools handle the simple case and break on the complex one.
We handle the complex one.
```

```markdown
<!-- identity/voice.md -->
# Voice

How formabi communicates:

- Direct and concise. No corporate fluff.
- Technical when talking to engineers. Plain when talking to customers.
- We say "we" not "Formabi." We're people, not a brand.
- Confident but not arrogant. We know our thing. We don't claim to know everything.
- Async-first writing: context-rich, self-contained messages.
  Don't assume the reader was in the meeting.
```

```markdown
<!-- identity/processes.md -->
# How We Work

- Distributed, async-first. Three regions, follow-the-sun.
- Ship small, frequent changes. Branch from main, PR, review, merge, deploy.
- The person who builds it is the person who ships it to the customer.
  No handoffs between engineering and customer success.
- Reversible decisions: make them fast. Irreversible decisions: write a proposal.
- Document the why, not just the what.
```

### Roles (Nix — because they configure infrastructure)

```nix
# roles/engineering.nix
{
  description = "Product engineering";
  repos = [
    { name = "formabi-app"; url = "git@github.com:rlpt/formde.git"; }
    { name = "latice"; url = "git@github.com:rlpt/latice.git"; }
  ];
  packages = pkgs: with pkgs; [ elmPackages.elm nodejs_20 cargo rustc ];
  serverAccess = "none";
  context = [ "app" ];
}

# roles/ops.nix
{
  description = "Operations and deployment";
  repos = [
    { name = "cmdr"; url = "git@github.com:rlpt/shed.git"; }
  ];
  packages = pkgs: with pkgs; [ deploy-rs age ssh-to-age ];
  serverAccess = "wheel";
  secretAccess = [ "all" ];
  context = [ "ops" ];
}

# roles/sales.nix
{
  description = "Sales and presentations";
  repos = [
    { name = "deck"; url = "git@github.com:rlpt/deck.git"; }
  ];
  packages = pkgs: with pkgs; [ marp-cli ];
  serverAccess = "none";
  context = [ "sales" ];
}
```

Roles stay in nix because they produce nix outputs (packages, server access levels). But they read from the Dolt data layer — the roster table determines who has which role.

## Core Mechanism: Graceful Degradation

### builtins.pathExists (local side)

```nix
let
  sibling = name: ../. + "/${name}";
  has = name: builtins.pathExists (sibling name);
  activeModules = lib.filter (m: has m.repo) allModules;
in
  mkShell {
    buildInputs = basePackages ++ lib.concatMap (m: m.packages) activeModules;
  }
```

The flake never fails. Missing repos = fewer tools, not an error.

### Why Not Flake Inputs for Private Repos?

Flake inputs resolve at `nix flake lock` time. If you can't access a repo, the entire lock fails. Only nixpkgs and public deps go in inputs. Private repos are detected on disk.

## The Repo as a Prompt

The deepest idea: **the repo is a prompt.** When you give it to an LLM, the structured data and markdown don't just inform the LLM — they shape it into an instance of formabi's intelligence.

### What "becoming formabi" means

An LLM given this repo can:

| Capability | What it reads |
|------------|--------------|
| Answer "what is formabi?" | identity/mission.md |
| Write in formabi's voice | identity/voice.md |
| Know who works here and their roles | Dolt roster + person_roles tables |
| Understand the current company stage | state/stage.json |
| Know what matters right now | state/priorities.json |
| Know who the customers are | Dolt customers table |
| Explain why Elm was chosen over React | decisions/001-elm-frontend.md |
| Write code that fits the architecture | context/app.md + decisions/ |
| Draft a customer email in the right tone | identity/voice.md + Dolt customers |
| Make a decision consistent with precedent | decisions/index.json + decisions/*.md |
| Generate a pitch with current metrics | state/metrics.json + brand/brand.json |
| Onboard a new hire | Dolt roster + identity/processes.md + roles/ |

The LLM doesn't need to be told "we use Elm" every time. It reads the decision log and knows. It doesn't need to be told "be concise" every time. It reads voice.md and knows. The repo is the company's accumulated intelligence, and the LLM inherits it.

### Context assembly per role

When alice (engineering + ops) opens Claude Code, the system assembles:

```
identity/mission.md          ← everyone gets this
identity/voice.md            ← everyone gets this
identity/processes.md        ← everyone gets this
Dolt roster summary          ← everyone gets this (public info)
state/stage.json             ← everyone gets this
state/priorities.json        ← everyone gets this
brand/brand.json             ← everyone gets this
decisions/index.json         ← everyone gets this
context/app.md               ← because engineering role
context/ops.md               ← because ops role
Dolt customers summary       ← because ops role (needs instance awareness)
```

When bob (sales) opens Claude Code:

```
identity/mission.md          ← everyone gets this
identity/voice.md            ← everyone gets this
identity/processes.md        ← everyone gets this
Dolt roster summary          ← everyone gets this
state/stage.json             ← everyone gets this
state/priorities.json        ← everyone gets this
brand/brand.json             ← everyone gets this
decisions/index.json         ← everyone gets this
context/sales.md             ← because sales role
state/metrics.json           ← because sales role (needs numbers for pitches)
```

Same LLM, same repo, different slices. Alice's Claude is an engineering agent. Bob's Claude is a sales agent. Both are formabi.

### Dolt as memory

The LLM doesn't just see the current state. Dolt's built-in versioning gives it temporal awareness:

```bash
# What changed about the roster recently?
dolt log --tables roster

# Who was on the team 3 months ago?
dolt sql -q "SELECT name, email FROM roster AS OF 'HEAD~10' WHERE active = TRUE"

# Diff the customer list between two points
dolt diff HEAD~5 HEAD --tables customers

# When did acme-corp get provisioned?
dolt log --tables customers --oneline
```

Every entity change is a Dolt commit. Every config change is a git commit. The LLM can reason about *when* things changed and *who* changed them.

### The company bootstrapping itself

Day zero scenario: you have the root repo with identity/, brand/, and an empty Dolt database. You hand the repo to an LLM and say "help me hire the first engineer." The LLM reads mission.md, voice.md, processes.md, stage.json, priorities.json — and it can:

1. Draft a job posting in formabi's voice
2. Suggest what to look for based on the tech stack (decisions/)
3. INSERT the person into the roster table once hired
4. Know what repos to give them access to (roles/)
5. Generate their onboarding checklist from processes.md

The company literally uses itself to grow itself.

## Dolt: The Guild Ledger

### Why Dolt instead of custom tooling

The formabi product uses datoms — `{ e, a, v, op }` — for form data. But for the company itself, we need something simpler. The problem with a custom datom log:
- Need to build `formabi-transact` (validate, generate IDs, append)
- Need to build `formabi-derive` (replay log → JSON views)
- Custom file format that only custom tools can query
- LLMs need to learn the intent JSON format

Dolt gives us all the properties we want without custom tooling:

| What we need | Datom approach | Dolt approach |
|-------------|---------------|---------------|
| Structured entity data | Custom log file | SQL tables |
| Version control | Git tracks the log file | Built into Dolt (branch, merge, diff, log) |
| Time travel | Replay log to date | `AS OF` clause in SQL |
| Immutable history | Append-only log | Dolt commit log (immutable) |
| Query current state | Custom derive → JSON | SQL query directly |
| LLM interaction | Custom intent JSON → tool → datoms | Standard SQL INSERT/UPDATE |
| Diffing changes | `git diff` on log file | `dolt diff` with schema awareness |
| Branching for proposals | Not supported | `dolt checkout -b proposal`, merge when approved |
| ID generation | Custom ULID tool | Dolt handles it (or use UUID) |
| Audit trail | Log file + git log | `dolt log`, `dolt blame` |

### How it works

Dolt is a SQL database that versions every change like git. It runs on the server and guild members interact with it via the `dolt` CLI over SSH.

```bash
# The Dolt database lives on the server
/srv/formabi/ledger/          ← Dolt repo (the guild ledger)
├── .dolt/                    ← Dolt internals (like .git/)
├── roster                    ← table
├── person_roles              ← table
├── ssh_keys                  ← table
└── customers                 ← table
```

### Adding a guild member

```bash
# Someone with ops role runs:
dolt sql -q "
  INSERT INTO roster (id, name, email, github, region, started)
  VALUES (UUID(), 'Dave', 'dave@formabi.com', 'dave', 'us-west', '2025-06-01');
"

dolt sql -q "
  INSERT INTO person_roles (person_id, role)
  SELECT id, 'engineering' FROM roster WHERE email = 'dave@formabi.com';
"

dolt sql -q "
  INSERT INTO ssh_keys (person_id, key_type, public_key)
  SELECT id, 'ed25519', 'ssh-ed25519 AAAAC3Nza...'
  FROM roster WHERE email = 'dave@formabi.com';
"

# Commit the change to Dolt
dolt add .
dolt commit -m "add Dave, engineering role"

# Deploy server — NixOS reads from Dolt, converges
deploy server
```

Or branch for review:

```bash
# Propose a hire on a branch
dolt checkout -b hire-dave
# ... make the INSERTs above ...
dolt commit -m "add Dave, engineering role"

# Review the diff
dolt diff main hire-dave

# Merge when approved
dolt checkout main
dolt merge hire-dave
deploy server
```

### Removing a guild member

```bash
dolt sql -q "UPDATE roster SET active = FALSE WHERE email = 'dave@formabi.com'"
dolt commit -m "offboard Dave"
deploy server
# → NixOS removes user, SSH key gone, access revoked
```

Dave's data stays in history — `dolt log` shows when he joined and when he left. No data is deleted, just marked inactive. Time travel still works: `SELECT * FROM roster AS OF 'two months ago'`.

### What the LLM sees and does

The LLM works with standard SQL — no custom format to learn:

```bash
# "Who has ops access?"
dolt sql -q "SELECT r.name FROM roster r
             JOIN person_roles pr ON r.id = pr.person_id
             WHERE pr.role = 'ops' AND r.active = TRUE"

# "Hire Dave as an engineer"
dolt sql -q "INSERT INTO roster ..."
dolt sql -q "INSERT INTO person_roles ..."
dolt commit -m "add Dave, engineering role"

# "What changed since last month?"
dolt diff HEAD~5 HEAD --tables roster

# "Provision acme-corp"
dolt sql -q "INSERT INTO customers (id, name, domain, port, tier, status, provisioned)
             VALUES (UUID(), 'acme-corp', 'acme.formabi.app', 3101, 'pro', 'active', CURRENT_DATE)"
dolt commit -m "provision acme-corp workspace"
deploy server
```

No custom intent JSON. No custom transact tool. Standard SQL that any LLM already knows.

## The Server: The Guild Hall

The server is a single large dedicated machine where everyone works. It's the physical manifestation of the guild — shared workspace, shared tools, shared ledger.

```
server.formabi.com                      ← the guild hall (NixOS)
├── /home/mei/                          ← guild member home dirs
├── /home/alice/
├── /srv/formabi/ledger/                ← Dolt database (the guild ledger)
├── /srv/formabi/demo/                  ← customer instance
├── /srv/formabi/acme-corp/             ← customer instance
└── /srv/repos/                         ← bare clones of company repos
```

Two separate concerns on one box:
- **Guild workspace** = the company as a unix system (members, repos, tools, Dolt ledger)
- **Formabi instances** = the product serving customers (systemd services, postgres DBs, nginx vhosts)

They share a server for now. They could split to separate machines later. The nix configs are already separate modules.

### Layer 1: Guild Members as Unix Users

The Dolt roster is the source of truth. NixOS derives unix users from it. Classic unix tools — SSH keys, home dirs, groups, permissions — do the enforcement.

#### Adding a guild member

```bash
# 1. Someone with ops role adds to Dolt (from the server)
dolt sql -q "INSERT INTO roster ..."
dolt sql -q "INSERT INTO person_roles ..."
dolt sql -q "INSERT INTO ssh_keys ..."
dolt commit -m "add Mei Lin, engineering role"

# 2. Deploy
deploy server
```

What NixOS does when the config is applied:

```
creates user: mei
  uid:    deterministic from roster
  home:   /home/mei/
  shell:  /bin/bash (with role-appropriate profile)
  groups: [ formabi engineering ]

writes: /home/mei/.ssh/authorized_keys
  → ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... mei@formabi.com

writes: /home/mei/.claude-context.md
  → assembled from identity/ + context/app.md (because engineering role)

creates: /home/mei/.bashrc
  → PS1 showing role, formabi commands in PATH
  → whoami, halp, dolt (if role allows)

links: /home/mei/repos/formabi-app → /srv/repos/formabi-app
links: /home/mei/repos/latice → /srv/repos/latice
  → only repos matching engineering role

does NOT create: /home/mei/repos/cmdr (not her role)
does NOT create: /home/mei/repos/deck (not her role)
```

Mei can now SSH in:

```
mei@laptop:~$ ssh mei@server.formabi.com

Welcome to the Formabi guild hall
Member: Mei Lin | Role: engineering | Region: singapore

mei@server:~$ ls repos/
formabi-app/  latice/

mei@server:~$ ls /home/
alice/  mei/

mei@server:~$ ls /home/alice/
ls: cannot open directory '/home/alice/': Permission denied

mei@server:~$ whoami
Member:  Mei Lin
Roles:   engineering
Region:  singapore
Home:    /home/mei

mei@server:~$ halp
Available commands:
  whoami          Your identity and roles
  halp            This help
  dolt sql        Query the guild ledger (read-only for you)

Not available (requires ops role):
  dolt commit
  deploy
```

#### Removing a guild member

```bash
# 1. Ops role marks inactive
dolt sql -q "UPDATE roster SET active = FALSE WHERE email = 'mei@formabi.com'"
dolt commit -m "offboard Mei Lin"

# 2. Deploy
deploy server
```

What NixOS does:

```
user 'mei' no longer in active roster

  → archives /home/mei/ to /var/archive/members/mei-2025-09-15/
  → removes user 'mei' from /etc/passwd
  → removes mei from 'engineering' and 'formabi' groups
  → SSH authorized_keys gone (no user = no file)
  → /home/mei/ removed after archive
```

Mei tries to SSH:

```
mei@laptop:~$ ssh mei@server.formabi.com
mei@server.formabi.com: Permission denied (publickey).
```

Done. No manual steps. No "did we remember to revoke her access?" The Dolt roster says she's inactive. The NixOS config has no user. SSH rejects. Declarative convergence.

#### The home directory is the member's workspace

The local shell and the server home dir are the same concept at different locations:

```
Local (mei's laptop)                    Server
────────────────────                    ──────────────
~/formabi/                              /home/mei/
├── .claude-context.md                  ├── .claude-context.md
├── formabi-app/ (cloned)               ├── repos/formabi-app/ (linked)
├── latice/ (cloned)                    ├── repos/latice/ (linked)
└── (devenv for tools)                  └── (NixOS profile for tools)
```

Same person, same role, same context, same repos. Whether Mei is working locally or SSH'd into the server, she sees the same world. The only difference: locally she has `devenv`, on the server NixOS manages her environment declaratively.

#### Unix groups from roles

```nix
# Derived from Dolt roster + roles
users.groups = {
  formabi = {};        # everyone in the guild
  engineering = {};    # engineering role
  ops = {};            # ops role — can sudo, manage deploys
  sales = {};          # sales role
};

# Each user gets groups from their roles
users.users.mei = {
  isNormalUser = true;
  extraGroups = [ "formabi" "engineering" ];
  # ...
};

users.users.alice = {
  isNormalUser = true;
  extraGroups = [ "formabi" "engineering" "ops" "wheel" ];
  # ops role → wheel → sudo
};

users.users.james = {
  isNormalUser = true;
  extraGroups = [ "formabi" "sales" ];
  # no wheel → no sudo → can't touch server config
};
```

File permissions follow naturally:

```
/srv/repos/formabi-app/    owner: root  group: engineering  750
/srv/repos/latice/         owner: root  group: engineering  750
/srv/repos/deck/           owner: root  group: sales        750
/srv/repos/cmdr/           owner: root  group: ops          750
/srv/formabi/              owner: root  group: ops          750  ← customer instances
/var/log/formabi/          owner: root  group: ops          750  ← production logs
```

James (sales group) physically cannot read `/srv/repos/formabi-app/`. Not because a policy says so — because unix permissions say `750` and he's not in the `engineering` group. Same constraint as locally: if you can't see it, the LLM running as you can't see it either.

#### The full picture: Dolt → NixOS → unix

```
Dolt ledger                 Export                      NixOS config
(source of truth)    →     (dolt sql -r json)    →     (declarative)
                                                              │
INSERT roster: Mei         roster.json exported         users.users.mei = { ... }
INSERT role: eng           (for nix to read)            users.groups.engineering.members
INSERT ssh_key: "..."                                   /home/mei/.ssh/authorized_keys
                                                              │
                                                        deploy server
                                                              │
                                                        NixOS applies:
                                                          useradd mei
                                                          mkdir /home/mei
                                                          write authorized_keys
                                                          ln -s repos
                                                          write .claude-context.md
                                                          write .bashrc
```

```
UPDATE roster: active=FALSE roster.json exported         users.users.mei GONE
                           (Mei gone)                   groups updated
                                                        no authorized_keys
                                                              │
                                                        deploy server
                                                              │
                                                        NixOS applies:
                                                          archive /home/mei
                                                          userdel mei
                                                          rm authorized_keys
                                                          unlink repos
```

One pipeline. Dolt in, unix out. The guild manages its members the same way NixOS manages its packages — declaratively, reproducibly, with full rollback via Dolt + git.

### Layer 2: Secrets (agenix, scoped by role)

**Today (cmdr)**: `secrets.nix` has a hardcoded list of who can decrypt what.

**With root flake**: Derived from Dolt roster + roles:

```nix
# secrets/secrets.nix — who can decrypt what
let
  people = import ../people;
  roles = import ../roles;

  # Collect SSH keys for people with secret access
  keysForAccess = level:
    lib.concatMap (p: p.sshKeys)
      (lib.filter (p:
        builtins.any (r: builtins.elem level (roles.${r}).secretAccess or []) p.roles
      ) (lib.attrValues people));
in {
  "plausible-admin-password.age".publicKeys = keysForAccess "all";
  "formabi-default-password.age".publicKeys = keysForAccess "all";
}
```

Add a person with ops role → they can decrypt production secrets. Remove them → they can't. No manual secret re-encryption lists.

### Layer 3: Product Instances (customers as Dolt data)

**Today (cmdr)**: `formabi-instances.nix` declares `{ demo = { port = 3100; }; }`. The `deploy-formabi` script creates DB, env file, and deploys.

**With root flake**: Customer data lives in Dolt, exported to JSON for Nix to consume:

```bash
# Export customers for Nix
dolt sql -q "SELECT name, domain, port, tier, status, provisioned
             FROM customers WHERE status = 'active'" -r json > /tmp/customers.json
```

```nix
# server/instances.nix — reads exported customer data
let
  customers = builtins.fromJSON (builtins.readFile ./customers-export.json);
in
  # generates systemd services, nginx vhosts, postgres DBs per customer
```

New customer = INSERT into Dolt, export, deploy. The server converges to include them.

### Layer 4: The Server as the Guild Hall

The NixOS server configuration becomes a pure function of the root flake + Dolt data:

```nix
# flake.nix (server output)
nixosConfigurations.server = nixpkgs.lib.nixosSystem {
  modules = [
    ./server/configuration.nix
    ./server/hardware-configuration.nix
    ./server/shared/common.nix
    (import ./server/shared/users.nix { inherit people roles; })
    (import ./server/shared/formabi.nix { inherit customers; })
    (import ./server/shared/services.nix { inherit brand; })
    agenix.nixosModules.default
  ];
};
```

Everything on the server is derived from the root flake's data:
- **Users** ← Dolt roster
- **SSH access** ← roles (serverAccess)
- **Secrets** ← roles (secretAccess)
- **Product instances** ← Dolt customers
- **Nginx vhosts** ← customers + brand (domains, SSL)
- **Analytics** ← brand (plausible config)
- **Static sites** ← deck, zolanic packages

The server has no manual configuration. It is what the nix expression says it is.

### Layer 5: AI Agents as Scoped Processes

Each role already gets a CLAUDE.md fragment. Take it further: define AI agent contexts as first-class:

```nix
# roles/ops.nix
{
  # ...existing fields...
  agent = {
    name = "ops-agent";
    context = [ "ops" "server" "instances" ];
    capabilities = [ "read-logs" "check-health" "trigger-deploy" ];
    restrictions = [ "no-delete-instances" "no-modify-secrets" ];
  };
}
```

This produces a CLAUDE.md + tool configuration for an AI agent that:
- Can read server logs and instance health
- Can trigger a deploy (with approval)
- Cannot delete customer data or modify secrets
- Only sees ops-relevant context

The agent definition lives in git. Its permissions are auditable. If you change the agent's capabilities, that's a PR with a reviewer.

**Per-person agent context**: When alice runs Claude Code on the server, the CLAUDE.md is assembled from her specific roles. The AI literally becomes a different agent depending on who is asking.

### Layer 6: Company Knowledge as Nix Packages

The deck repo already builds a handbook as a nix package (`nix build .#handbook`). Extend this:

```nix
# The company's knowledge, built from source
packages.handbook = buildHandbook {
  inherit brand;
  people = import ./people;    # team page auto-generated
  roles = import ./roles;      # role descriptions included
  customers = import ./server/instances.nix;  # customer list for internal reference
};

packages.decks = buildDecks {
  inherit brand;
  # pitch decks with latest metrics
};
```

The handbook is not a static doc someone maintains. It's **derived from the same data** that configures the servers and shells. The team page is always accurate because it reads the Dolt roster. The architecture diagram is always current because it reads the module definitions.

### Layer 7: CI/CD Derived from Modules

Each module knows what it needs to build and test. CI pipelines can be generated:

```nix
# Derived: what to build on push to each repo
ciPipelines = lib.mapAttrs (name: mod: {
  repo = mod.repo;
  steps = [
    { name = "build"; command = mod.buildCommand; }
    { name = "test"; command = mod.testCommand; }
    { name = "deploy"; command = mod.deployCommand; condition = "branch == main"; }
  ];
}) activeModules;
```

When you add a new module, its CI pipeline exists automatically. No manually configuring GitHub Actions per-repo.

### Layer 8: Company Health as a Nix Evaluation

```bash
# scripts/health.sh — queries the guild's state
health() {
  echo "Members:   $(dolt sql -q 'SELECT COUNT(*) FROM roster WHERE active = TRUE' -r csv | tail -1)"
  echo "Roles:     $(ls roles/*.nix | grep -v default | wc -l) defined"
  echo "Modules:   $(ls modules/*.nix | wc -l) registered"
  echo "Customers: $(dolt sql -q 'SELECT COUNT(*) FROM customers WHERE status = \"active\"' -r csv | tail -1)"
  echo "Server:    $(ssh server uptime)"
  echo "Last deploy: $(git log --oneline -1 -- server/)"
}
```

The guild's vital signs are queryable from the shell. Not a dashboard — a function.

### Layer 9: Browser Access — Forgejo as the Glass Window

The CLI shell is powerful but not everyone lives in a terminal. Marketing, sales, new hires — they need to view and edit company content from a browser or phone. The source of truth stays in git and Dolt, but we add a browser layer on top.

#### The problem

The formabi system already serves static content well:
- `deck.zolanic.space` serves pitch decks (markdown → marp → HTML → nginx)
- Handbook builds from markdown via pandoc
- Everything is nix-built and nginx-served

But this is **read-only**. A sales person can view decks but can't fix a typo without SSH + git CLI + vim. We need browser-based editing that still commits to git.

#### The solution: Forgejo on the server

**Forgejo** — a lightweight, self-hosted git forge (community fork of Gitea). Runs as a single binary. NixOS has a module for it. It gives you:

- **Web UI for git** — browse repos, view markdown rendered, see commit history
- **In-browser editing** — click a file, edit, commit. Each edit is a real git commit.
- **Mobile-friendly** — responsive web UI, works on phone
- **Pull requests** — non-technical people can propose changes, someone reviews
- **API** — webhooks on push to trigger nix rebuilds
- **User management** — derives from Dolt roster (same people, same roles)

```
code.formabi.com                       ← web UI for the guild's repos
├── formabi/formabi (root repo)        ← edit identity/, state/, decisions/ in browser
├── formabi/deck (pitch decks)         ← marketing edits slides in browser
└── formabi/handbook                   ← anyone can fix a typo via PR
```

#### How it works

```
James (sales, phone)              Forgejo                    Git               Server
─────────────────────    →    ──────────────    →    ──────────────    →    ──────
                              browser editor
"fix typo in investor          edit file,               git commit           webhook
 pitch deck"                   commit message            appended            triggers
                              "fix: typo in slide 3"                        nix rebuild
                                                                            deck rebuilt
                                                                            nginx serves
                                                                            new version at
                                                                            deck.zolanic.space
```

The source of truth never changes — it's still git and Dolt. Forgejo is just a browser-shaped window into the guild. Every edit through Forgejo is a git commit with the person's identity. `git log` shows it the same as any CLI commit.

#### NixOS config

```nix
# server/shared/forgejo.nix
{ config, pkgs, lib, people, roles, brand, ... }:
{
  services.forgejo = {
    enable = true;
    settings = {
      server = {
        DOMAIN = "code.formabi.com";
        ROOT_URL = "https://code.formabi.com";
      };
      service.DISABLE_REGISTRATION = true;  # users from roster only
    };
  };

  # nginx vhost with ACME
  services.nginx.virtualHosts."code.formabi.com" = {
    enableACME = true;
    forceSSL = true;
    locations."/".proxyPass = "http://127.0.0.1:3000";
  };
}
```

Users are provisioned from the Dolt roster — same people, same roles, same permissions. A sales person sees the repos their role grants. An engineer sees engineering repos. The browser window respects the same boundaries as the CLI.

#### Webhook → rebuild pipeline

When someone edits a file through Forgejo:

1. Forgejo commits to the repo (a real git commit)
2. Webhook fires to a small rebuild service on the server
3. Service runs `nix build` for the affected package (deck, handbook, etc.)
4. Nginx serves the new build
5. Git records the change

For the deck repo, this means: James fixes a typo on his phone → 30 seconds later → `deck.zolanic.space` has the fix. No deploy command needed. The webhook + nix build pipeline handles it.

#### What Forgejo gives each role

| Role | What they see in Forgejo | What they can do |
|------|--------------------------|------------------|
| Everyone | Root repo (identity/, state/, decisions/) | Read, propose changes via PR |
| Sales | + deck repo | Edit pitch decks, handbook |
| Engineering | + formabi-app, latice repos | Full access, code review |
| Ops | + cmdr repo, server config | Edit server configs, review deploys |
| Design | + zolanic repo | Edit website |

#### What Forgejo does NOT replace

- **The CLI** — `dolt sql`, `deploy server`, `dolt log` stay CLI-only. These are power tools.
- **Dolt** — entity data stays in Dolt. Forgejo is for git-tracked files only.
- **The server config** — server changes still go through `deploy server` from a CLI with ops access.
- **Claude Code** — LLM interaction stays in the terminal. Forgejo is for humans with browsers.

Forgejo is a **glass window** — you can see and touch the same things, but through glass. The CLI has the full controls.

#### Other browser tools on the server

Forgejo handles editing. For read-only access, the existing pattern works:

| Content | Source | Build | Served at |
|---------|--------|-------|-----------|
| Pitch decks | deck/decks/*.md | marp (nix build) | deck.zolanic.space |
| Handbook | deck/handbook/*.md | pandoc (nix build) | handbook.formabi.com |
| Brand site | zolanic/ | astro (nix build) | zolanic.space |
| Analytics | plausible | NixOS service | analytics.zolanic.space |
| Secret sharing | privatebin | NixOS service | yo.zolanic.space |
| Code / editing | forgejo | NixOS service | code.formabi.com |

Everything is a NixOS service on the server, declared in nix, served by nginx with ACME SSL. Add a new service = add a nix module + nginx vhost, deploy.

## Onboarding: Two New Guild Members

Before either person starts, someone with ops access has already run:

```bash
dolt sql -q "
  INSERT INTO roster (id, name, email, github, region, started)
  VALUES
    (UUID(), 'Mei Lin', 'mei@formabi.com', 'meilin', 'singapore', '2025-06-02'),
    (UUID(), 'James', 'james@formabi.com', 'jamesw', 'uk', '2025-06-02');
"

dolt sql -q "
  INSERT INTO person_roles (person_id, role)
  SELECT id, 'engineering' FROM roster WHERE email = 'mei@formabi.com'
  UNION ALL
  SELECT id, 'sales' FROM roster WHERE email = 'james@formabi.com';
"

dolt sql -q "
  INSERT INTO ssh_keys (person_id, key_type, public_key)
  SELECT id, 'ed25519', 'ssh-ed25519 AAAAC3Nza... mei@formabi.com'
  FROM roster WHERE email = 'mei@formabi.com';
"

dolt commit -m "add Mei Lin (engineering, singapore) and James (sales, uk)"
deploy server
```

They exist in the guild before they've touched a keyboard.

---

### Mei Lin — Core Engineer, Singapore

Mei gets a one-line instruction from her manager: "Clone formabi, enter the shell, run `onboard`."

```
mei@laptop:~$ git clone git@github.com:formabi/formabi.git
mei@laptop:~$ cd formabi
mei@laptop:~/formabi$ nix develop

formabi shell — 0 of 5 modules active

  base: git, dolt, jq, halp, whoami, onboard

Run 'onboard' to get started.

mei@laptop:~/formabi$ onboard
```

The onboard script detects her git email, queries the Dolt roster, and starts a chat session with the LLM. The LLM has the full company context loaded.

```
─────────────────────────────────────────────
  formabi onboarding
─────────────────────────────────────────────

  Looking you up... found you in the roster.

  Welcome to Formabi, Mei Lin!

  You're a product engineer in the Singapore region.
  You joined on 2025-06-02. Here's what I know about your role.

  Formabi makes complex forms easy. We're a small team of product
  engineers — one per region, follow-the-sun. You own Asia-Pacific.
  The person who builds it is the person who ships it to the customer.

  Current priorities (from state/priorities.json):
    1. Ship form engine v1 — complete fill/submit flow
    2. Land 3 pilot customers
    3. Hire Singapore product engineer  ← that's you

  Let me get you set up.

  ─── repos ───────────────────────────────

  Your roles need these repos. I'll check which you have access to.

  formabi-app  ✗  not cloned
    → git clone git@github.com:rlpt/formde.git ../formabi-app

  latice       ✗  not cloned
    → git clone git@github.com:rlpt/latice.git ../latice

  Run those two clone commands, then come back here.

> (mei clones both repos)

  Checking... found both.

  formabi-app  ✓  ../formabi-app (main branch)
  latice       ✓  ../latice

  ─── architecture (quick version) ───────

  The product is an Elm 0.19.1 SPA + Rust Axum backend.

  Core concept: datoms. Atomic facts as {e, a, v, op}.
  Everything is Entity-Attribute-Value. Forms are defined as "plans,"
  filled as "fills." The form structure is a tree of sections,
  polyances (repeating groups), and fields.

  Key decision: we chose Elm because its type system catches bugs at
  compile time and we have no runtime exceptions in production.
  (See decisions/001-elm-frontend.md for the full reasoning.)

  Key decision: datalog-style EAV because forms have wildly varying
  schemas. Traditional relational models break on this.
  (See decisions/002-datalog-architecture.md)

  ─── dev environment ────────────────────

  Exit this shell and re-enter to pick up the new modules:

    exit
    nix develop

  You'll see the engineering tools load. Then:

    cd ../formabi-app
    dev               # starts backend + frontend via overmind

  The backend runs on :3060, frontend on :3010.
  Test credentials: alice@zolanic.space / password123

  ─── your first week ────────────────────

  Based on current priorities, I'd suggest:

  1. Get the app running locally (today)
  2. Read through src/Forms/Fill/Types.elm — the core data model
  3. Read decisions/ — understand why things are the way they are
  4. Pick up a task from the board related to "fill/submit flow"
  5. Ship something small by end of week

  ─── how we work ────────────────────────

  From identity/processes.md:

  - Async-first. Write things down, don't schedule calls.
  - Ship small, frequent changes. Branch → PR → review → merge.
  - You own APAC. When UK hands off at end of day, you pick up.
  - Document the why, not just the what.

  ─── people ─────────────────────────────

  Current team (from roster):

  Alice  — engineering, ops — UK region (your handoff partner)
  James  — sales — UK region (starting same day as you)

  Alice is your main collaborator. She built most of what exists.
  Overlap window: your morning is her afternoon.

  ───────────────────────────────────────

  That's it. Run 'halp' anytime to see available commands.
  Run 'whoami' to check your current state.

  Welcome aboard, Mei. Ship something.
```

Mei exits, re-enters the shell:

```
mei@laptop:~/formabi$ exit
mei@laptop:~/formabi$ nix develop

formabi shell — 2 of 5 modules active

  base:   git, dolt, jq, halp, whoami, onboard
  app:    elm, node, cargo, dev, test, build
  latice: cargo, buf, protobuf

mei@laptop:~/formabi$ whoami

Member:  Mei Lin
Roles:   engineering
Region:  singapore
Modules: 2/5 active

  app     ✓  ../formabi-app
  latice  ✓  ../latice
  cmdr    -  (not your role)
  deck    -  (not your role)
  zolanic -  (not your role)
```

She opens Claude Code. The CLAUDE.md has been assembled from identity/ + state/ + context/app.md. Claude knows the architecture, the priorities, the team, and the decisions. It doesn't know about deployment, sales decks, or the brand website — those aren't her modules.

```
mei@laptop:~/formabi$ claude

> What should I work on first?

  Based on state/priorities.json, the top priority is shipping the
  form engine v1 fill/submit flow. Looking at the current state of
  src/Forms/Fill/...
```

---

### James — Sales, UK

James gets the same one-line instruction.

```
james@laptop:~$ git clone git@github.com:formabi/formabi.git
james@laptop:~$ cd formabi
james@laptop:~/formabi$ nix develop

formabi shell — 0 of 5 modules active

  base: git, dolt, jq, halp, whoami, onboard

james@laptop:~/formabi$ onboard
```

```
─────────────────────────────────────────────
  formabi onboarding
─────────────────────────────────────────────

  Looking you up... found you in the roster.

  Welcome to Formabi, James!

  You're in sales, UK region. You joined on 2025-06-02.

  Formabi makes complex forms easy. We sell to organizations that
  have painful, multi-step form workflows — think compliance,
  onboarding, applications, audits. Our product turns those into
  something people actually enjoy using.

  You'll be partnering with Alice (engineering, UK) on deals.
  She runs the technical demos and scopes integrations.
  You find the customers, qualify opportunities, and close together.

  Current stage (from state/stage.json):
    Pre-seed. Focus: product-market fit.
    Team: 3 people. Runway: 18 months.

  Current priorities:
    1. Ship form engine v1
    2. Land 3 pilot customers  ← this is your mission
    3. Hire Singapore engineer  ← done (Mei, starting today with you)

  ─── repos ───────────────────────────────

  Your role needs:

  deck  ✗  not cloned
    → git clone git@github.com:rlpt/deck.git ../deck

  Run that clone command, then come back.

> (james clones deck)

  Checking... found it.

  deck  ✓  ../deck

  ─── what you have ──────────────────────

  The deck repo contains:

  Pitch decks (Marp markdown → HTML slides):
    decks/investor.md  — investor pitch: problem, solution, market, ask
    decks/product.md   — product deep-dive: features, workflows
    decks/company.md   — the team, org design, velocity

  Company handbook (Pandoc markdown → HTML):
    handbook/00-introduction.md
    handbook/01-how-we-work.md

  Brand theme with our colors (indigo/violet on dark).

  To preview decks locally:
    cd ../deck
    marp --server decks/

  Live decks are served at deck.zolanic.space

  ─── the product (what you're selling) ──

  Formabi is a form builder for the complex case. Most form tools
  handle simple contact forms. We handle multi-step workflows with:

  - Conditional logic (show/hide sections based on answers)
  - Repeating groups (add another dependent, add another address)
  - Entity relationships (this person references that organization)
  - Audit trails (every change is a datom — immutable, traceable)

  Target customers: regulated industries, HR, compliance, government.
  Anyone with forms that make people cry.

  ─── current customers ──────────────────

  From the guild ledger:

  demo  — demo.zolanic.space — free tier — active since 2025-01-01
    This is our demo instance. Use it for prospect demos.

  That's it so far. Landing 3 pilots is priority #2. That's you.

  ─── your first week ────────────────────

  1. Read the pitch decks (today) — understand the story we tell
  2. Visit demo.zolanic.space — click through the product
  3. Read identity/voice.md — how we communicate
  4. Read identity/mission.md — what we believe
  5. Talk to Alice about target customer profiles
  6. Start building a prospect list by end of week

  ─── how we work ────────────────────────

  - Async-first. Context-rich messages, not quick Slack pings.
  - You and Alice close deals together. You qualify, she demos.
  - When you land a customer, it becomes a Dolt entry:
      dolt sql -q "INSERT INTO customers ..."
      dolt commit -m "provision acme-corp"
    That provisions their workspace on the server. No tickets, no ops team.

  ─── people ─────────────────────────────

  Alice  — engineering, ops — UK (your deal partner)
  Mei Lin — engineering — Singapore (starting same day, ships product)

  ───────────────────────────────────────

  That's it. Run 'halp' for commands. Run 'whoami' to check state.

  Welcome aboard, James. Go find us some customers.
```

James re-enters the shell:

```
james@laptop:~/formabi$ exit
james@laptop:~/formabi$ nix develop

formabi shell — 1 of 5 modules active

  base: git, dolt, jq, halp, whoami, onboard
  deck: marp, build-deck, present

james@laptop:~/formabi$ whoami

Member:  James
Roles:   sales
Region:  uk
Modules: 1/5 active

  deck    ✓  ../deck
  app     -  (not your role)
  latice  -  (not your role)
  cmdr    -  (not your role)
  zolanic -  (not your role)
```

He opens Claude Code. The CLAUDE.md has identity/ + state/ + context/sales.md. Claude knows the pitch, the product positioning, the current metrics, the customers. It doesn't know the Elm architecture, the datom model internals, or the server configuration.

```
james@laptop:~/formabi$ claude

> I have a call with a compliance team at a mid-size bank tomorrow.
> Help me prep.

  Based on the product deck and our positioning, here's the angle
  for a compliance team at a bank...

  Their pain: regulatory forms are complex, change frequently, need
  audit trails, and current tools can't handle conditional logic
  across multi-step workflows...
```

---

### What just happened

Both guild members started from the same place: `git clone`, `nix develop`, `onboard`. The system:

1. **Identified them** from the Dolt roster (matched by git email)
2. **Scoped their experience** by role — different repos, different tools, different context
3. **Oriented them** to the guild — mission, stage, priorities, team, how we work
4. **Got them productive** — specific repos to clone, specific first-week tasks
5. **Shaped their AI** — Claude Code for each person is a different agent

Mei's Claude is an engineering agent that knows Elm, datoms, and the fill/submit flow.
James's Claude is a sales agent that knows the pitch, the demo, and the customer pipeline.

Neither can see the other's world. Neither LLM can exceed its user's permissions. Both are formabi.

| | Mei (engineering) | James (sales) |
|---|---|---|
| Repos | formabi-app, latice | deck |
| Tools | elm, cargo, node, dev, test | marp, build-deck, present |
| Claude context | architecture, datoms, code patterns | pitch, product positioning, customers |
| First task | Ship code for fill/submit flow | Build prospect list, prep first demo |
| Doesn't see | deploy scripts, pitch decks, brand site | source code, server config, Elm internals |
| Can't do | deploy (no ops role, no SSH key) | write to Dolt (no ops role), push to formabi-app (no GitHub access) |
| LLM bounded by | Mei's filesystem, SSH keys, git identity | James's filesystem, SSH keys, git identity |

## What This Looks Like Day-to-Day

### Hiring someone

```bash
# 1. Add to Dolt
dolt sql -q "INSERT INTO roster ..."
dolt sql -q "INSERT INTO person_roles ..."
dolt sql -q "INSERT INTO ssh_keys ..."
dolt commit -m "add dave, engineering role"

# 2. Deploy server (dave gets SSH access based on role)
deploy server

# 3. Dave clones root repo, runs onboard
# dave$ git clone ... && cd formabi && nix develop
# dave$ onboard
# → "Your roles: engineering. Clone formabi-app and latice."
```

### Offboarding someone

```bash
# 1. Mark inactive
dolt sql -q "UPDATE roster SET active = FALSE WHERE email = 'dave@formabi.com'"
dolt commit -m "offboard dave"

# 2. Deploy
deploy server
# → dave's unix user removed, SSH key gone, secret access revoked
```

### Adding a customer

```bash
# 1. Add to Dolt
dolt sql -q "INSERT INTO customers (id, name, domain, port, tier, status, provisioned)
             VALUES (UUID(), 'acme-corp', 'acme.formabi.app', 3101, 'pro', 'active', CURRENT_DATE)"
dolt commit -m "provision acme-corp workspace"

# 2. Deploy
deploy server
# → systemd service created, nginx vhost created, SSL provisioned, DB created
```

### Changing a role's permissions

```bash
# 1. Edit role
vim roles/engineering.nix
# Change serverAccess from "none" to "ssh" (read-only shell)

# 2. Commit, deploy
git commit -am "grant engineers read-only server access"
deploy server
# → all engineers now have SSH access (no sudo). Derived from their roster entries.
```

## Security Model

### The hard rule: LLM <= User

The LLM never has more permissions than the active user. This isn't enforced by telling the LLM to behave — it's enforced by the architecture. There is no mechanism for escalation because every layer is physically bounded by what the user has on disk.

| What the LLM tries to do | What actually constrains it |
|---------------------------|----------------------------|
| Read source code | Can only read files on disk. User hasn't cloned the repo? Files don't exist. LLM can't read what isn't there. |
| Write to Dolt | Dolt runs on the server. User must SSH in. No ops role = no SSH key = no connection. |
| Run `deploy server` | Requires SSH key on the server. Server users derived from Dolt roster + roles. No ops role = no SSH key = deploy fails. |
| Decrypt a secret | agenix requires the user's age key. No secretAccess in role = key not in the encryption list = decryption fails. |
| Push to a repo | Requires GitHub write access. User's GitHub account doesn't have access = push rejected. |
| See context for another role | CLAUDE.md assembled from modules on disk. No repo cloned = no context fragment included. |

The enforcement is **physical, not policy**. The LLM runs as a process in the user's shell. It has the user's filesystem, the user's SSH keys, the user's git config. It literally cannot reach what the user cannot reach. There is no API key that grants the LLM separate access. There is no service account. The LLM is the user.

### Sanctum — the innermost ring

The sanctum is the smallest, most privileged access zone: the people who have full access to application source code and the NixOS environment. Their identities and SSH keys are defined directly in the nix config. This is the hardest boundary — you're either in the sanctum or you're not.

Who belongs here: product engineers, and potentially a small number of infra people. Nobody else. This group should stay as small as possible. Every person in the sanctum can read all source, modify the NixOS configuration, and deploy. They are the people who can change what the guild *is*, not just what it *does*.

The sanctum is controlled by nix, not by policy. If your SSH key isn't in the config, you don't have access — there's no override, no admin panel, no escalation path. Adding someone to the sanctum is a nix change, committed to git, reviewed in a PR, deployed. Removing them is the same.

### Layer summary

| Layer | Mechanism | Boundary |
|-------|-----------|----------|
| Code access | GitHub repo permissions | Can't clone = can't see |
| Local tools | builtins.pathExists | No repo on disk = no tools |
| LLM permissions | Runs as user's process | LLM = user, always |
| Dolt access | Server-side, requires SSH | No ops role = no SSH = no writes |
| Server access | Derived from Dolt roster + roles | serverAccess field → SSH key or nothing |
| Secret access | agenix + derived from roles | secretAccess field → age key or nothing |
| AI context | Assembled from modules on disk | Only sees what's present |
| Instance data | Server-side, not in local shells | Customers isolated per-instance |
| Audit trail | Git + Dolt history | Every change is versioned under user's identity |

The root repo is safe for everyone to read. It contains structure, roles, and identity (public info). Actual secrets are agenix-encrypted — only decryptable by people whose roles grant access. The LLM's context, tools, and capabilities are exactly the user's context, tools, and capabilities — nothing more.

## What's In vs What's Out

### In the repo + Dolt (the guild's definition)

| What | Format | Where |
|------|--------|-------|
| Identity | markdown | identity/mission.md, voice.md, processes.md |
| People | Dolt SQL | roster, person_roles, ssh_keys tables |
| Customers | Dolt SQL | customers table |
| Company state | JSON | state/stage.json, priorities.json, metrics.json |
| Decisions | markdown + JSON index | decisions/ |
| Brand | JSON | brand/brand.json |
| Infrastructure | nix | flake.nix, roles/, modules/, server/ |
| Secrets (encrypted) | age files | only decryptable by role |
| AI context | markdown | context/ — per-role fragments assembled on shell entry |

### Out of the repo (stays external)

| What | Why | Where instead |
|------|-----|---------------|
| Conversations | Ephemeral, high-volume | Slack, email |
| Money | Regulated, needs real accounting | Xero/Stripe |
| Legal contracts | Need legal standing | Lawyers, DocuSign |
| Customer data | Per-instance, belongs to customers | PostgreSQL per-instance |
| Real-time metrics | Changes every second | Plausible, server monitoring |
| Passwords/tokens | Never in git, even encrypted | agenix for infra, 1Password for humans |

The line: **the repo + Dolt define the shape and brain of the guild. They don't hold customer data or move money.** State like metrics.json is a curated snapshot (updated periodically or by CI), not a live feed.

## Migration Path

### Phase 0: Identity + state (no code changes, pure data)
- Create root repo
- Write identity/mission.md, voice.md, processes.md from existing deck/handbook content
- Write brand/brand.json (already defined in deck/flake.nix)
- Write state/stage.json, priorities.json manually
- Write first decision records from existing architecture
- **Test**: hand the repo to an LLM and ask it to describe formabi. If it sounds right, the data is good.

### Phase 1: Dolt database + schema
- Set up Dolt on the server
- Create roster, person_roles, ssh_keys, customers tables
- Seed from current people + customer knowledge
- Prove: `dolt sql -q "SELECT * FROM roster"` shows current guild members
- Prove: `dolt log` shows clean versioned history
- Prove: `dolt diff` shows readable schema-aware diffs

### Phase 2: Nix shells (local only, no server changes)
- Add flake.nix that reads exported Dolt data + roles, composes devenv shells
- Add modules/ with pathExists detection for sibling repos
- Prove: `nix develop .#alice` gives the right tools
- cmdr/deploy/ stays as-is, untouched

### Phase 3: AI context assembly
- Add context/ fragments per role
- Shell entry assembles CLAUDE.md from identity/ + state/ + context/ based on active modules
- Prove: Claude Code behaves differently per role

### Phase 4: Server users derived from Dolt roster
- server/shared/users.nix reads exported Dolt roster data
- Deploy. Server users now come from the same Dolt tables as local shells.

### Phase 5: Server fully derived from root
- Migrate cmdr/deploy/ into root repo's server/
- Dolt customers table feeds systemd services + nginx vhosts
- secrets.nix derived from Dolt roster + roles
- deploy-rs in root flake
- cmdr becomes scripts-only (no config)

### Phase 6: The guild maintains itself
- Handbook auto-generated from identity/ + Dolt roster + brand/
- CI validates: every active roster member has SSH key, every customer has valid port/domain
- Onboard script queries Dolt + roles, guides new member
- Health script queries all layers
- LLM adds people/customers via `dolt sql`, never edits JSON directly

## Open Questions

- Should the root repo be `formabi/formabi` or `formabi/root` or just the org-level `.github` repo?
- Do worktree branches (app-blue, app-green, app-purple) get their own modules or share the app module?
- Should roles compose? (e.g., "lead" = engineering + ops + hiring)
- How to handle the transition period where cmdr/deploy/ and root/server/ coexist?
- Should devenv (used today) coexist with pure flake devShells or be replaced?
- Should decisions/ use a stricter schema (like ADR) or stay freeform?
- What's the minimum viable root repo? Just identity/ + Dolt + state/ without nix?
- How to connect Dolt to the nix build? Export JSON at build time, or read via a nix fetcher?
- Where does the Dolt database live? On the server only, or replicated locally?
- Should Dolt branches map to git branches for coordinated changes (e.g., hire-dave branch in both)?
- How to handle Dolt auth? Unix permissions on the server? Dolt's built-in user system?
- Should `dolt sql` be exposed as an MCP tool so Claude Code can query the ledger directly?
