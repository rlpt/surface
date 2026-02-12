# Formabi as Code

The repo IS the company. The system is called **formabi**. It has three parts, like a ship:

- **hull** — the body. The NixOS server where the company runs. `deploy hull`.
- **bridge** — the command center. The shell where you query, transact, and steer. `bridge` to enter. Forgejo (`code.formabi.com`) is the glass bridge — same view, browser-shaped.
- **wake** — the trail. Datom log + git history. Immutable, append-only. You can't change your wake. `wake log`.

Read the repo and you become formabi — you know the mission, the people, the customers, the architecture, the current priorities, and how to make decisions consistent with how formabi operates. Enter the bridge and you can query state, transact changes, derive views, and deploy. Human or LLM — the interface is the same. The company is the program. The bridge is where you steer it.

Four formats, each for what it's best at:
- **Datoms** — immutable append-only log of entity facts `{ e, a, v, op, t }`. The source of truth for anything with identity (people, customers, instances). LLMs never generate IDs — they express intent as JSON, a tool converts to datoms.
- **JSON** — derived views of current state (roster.json, customers.json) + manually maintained narrative (stage.json, priorities.json). Machine-readable, queryable, LLM-native.
- **Markdown** — company knowledge (mission, processes, voice, decisions, context). Human-readable, LLM-native.
- **Nix** — infrastructure and composition (shells, servers, builds). Reads JSON, produces reproducible outputs.

Git ties them together. Every change is a commit. The wake — datom log + git history — is the company's memory. Append-only, replayable, time-travelable. You can't change your wake.

## Principles

1. **The LLM never has more permissions than the active user.** This is the hard rule. The LLM runs in the user's shell, with the user's repos, the user's role, the user's git identity. It cannot see repos the user hasn't cloned. It cannot transact changes the user's role doesn't allow. It cannot deploy if the user doesn't have ops access. The LLM is never a privilege escalation vector — it is always bounded by the human sitting at the keyboard.
2. **Hull, bridge, wake** — The company is a ship. The hull runs it (server). The bridge steers it (shell). The wake records it (datom log + git). Human or LLM — same bridge, same permissions.
3. **Separate repos are the security boundary** — GitHub permissions control who sees what. The root flake never references private repos as inputs.
4. **Works with any/all modules missing** — Zero repos cloned = base shell still works. It never fails, it just gives you less.
5. **One definition, two targets** — `people/alice.nix` produces her local shell AND her server access. Change it once, both sides update.
6. **Datoms for entities, JSON for views, markdown for knowledge, nix for infra** — Each format for what it's best at. LLMs write intent, tools write datoms, state is derived.
7. **Git is the audit log** — Every change to people, roles, servers, and instances is a commit with a reviewer.
8. **KISS** — Simple files. No custom tooling beyond shell scripts.

## The Big Idea

Today you already have two halves:

- **Local**: devenv shells per-repo, each configured independently
- **Server**: NixOS on hull (currently called formrunner), declared in cmdr/deploy/, deployed with deploy-rs

These halves don't know about each other. `users.nix` on the server has hardcoded SSH keys. `devenv.nix` in each repo has hardcoded tools. There's no shared definition of "who works here" or "what they can do."

The idea: a **root flake** that is the single source of truth for the company. It evaluates differently depending on the target:

```
formabi (root flake)
  │
  ├── nix develop .#alice     → local shell with her tools, repos, AI context
  ├── nix develop .#ops       → local shell for ops role (anyone)
  │
  ├── nixosConfigurations     → server configs that read the same people/roles
  │     └── hull        → SSH keys, unix users, services — all derived
  │
  └── packages                → built artifacts (app binary, deck html, etc.)
```

One `people/alice.nix` file produces:
- Her local devShell (tools for her roles)
- Her SSH authorized key on the server
- Her unix user on hull
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
│   ├── roster.json                   ← structured: [ { name, github, email, roles, sshKeys, region, started } ]
│   └── default.nix                   ← reads roster.json, exposes to nix
│
├── roles/                            ← WHAT each role can do
│   ├── engineering.nix               ← repos, tools, server access, AI context scope
│   ├── ops.nix
│   ├── sales.nix
│   ├── design.nix
│   └── default.nix                   ← role registry
│
├── state/                            ← WHERE the company is right now (JSON)
│   ├── stage.json                    ← { stage, runway_months, funding, focus }
│   ├── customers.json                ← [ { name, domain, tier, port, provisioned, status } ]
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
│   ├── hull/
│   │   ├── configuration.nix
│   │   └── hardware-configuration.nix
│   └── shared/
│       ├── common.nix
│       ├── users.nix                 ← derived from people/roster.json
│       └── services.nix              ← derived from state/customers.json
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
│   └── default.nix                   ← always-on: git, halp, whoami, onboard
│
└── scripts/
    ├── onboard.sh
    ├── whoami.sh
    └── halp.sh
```

### The Four Layers

```
┌──────────────────────────────────────────────────────────┐
│  KNOWLEDGE (markdown)                                    │
│  identity/mission.md, identity/voice.md,                 │
│  decisions/*.md, context/*.md                            │
│  → LLM reads this and becomes formabi                    │
├──────────────────────────────────────────────────────────┤
│  TRUTH (datoms)                            ┌───────────┐ │
│  log/company.datoms                        │ LLM says: │ │
│  append-only immutable fact log            │ intent as │ │
│  { e, a, v, op, timestamp }               │ plain JSON │ │
│  → source of truth for entities            │ ↓          │ │
│  → tool generates IDs + validates          │ tool      │ │
│  → replayable, time-travelable             │ converts  │ │
│                                            │ to datoms │ │
│          │ derive                          └───────────┘ │
│          ▼                                               │
│  VIEWS (derived json)                                    │
│  people/roster.json, state/customers.json                │
│  → read-only snapshots of current state                  │
│  → regenerable from log at any time                      │
│                                                          │
│  NARRATIVE (manual json)                                 │
│  state/stage.json, state/priorities.json                 │
│  brand/brand.json, decisions/index.json                  │
│  → high-level company state, maintained directly         │
├──────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE (nix)                                    │
│  flake.nix, roles/*.nix, modules/*.nix,                  │
│  server/**/*.nix, base/default.nix                       │
│  → reads JSON views, produces shells + servers           │
└──────────────────────────────────────────────────────────┘
         │
         │  git log
         ▼
    HISTORY (git)
    every datom append, every JSON change, every nix edit
    is a commit with an author and a reason
```

### People (JSON — the universal format)

```json
// people/roster.json
[
  {
    "id": "alice",
    "name": "Alice",
    "github": "alice",
    "email": "alice@formabi.com",
    "roles": ["engineering", "ops"],
    "region": "uk",
    "started": "2024-06-01",
    "sshKeys": ["ssh-ed25519 AAAAC3Nza... alice@formabi.com"]
  },
  {
    "id": "bob",
    "name": "Bob",
    "github": "bob",
    "email": "bob@formabi.com",
    "roles": ["engineering"],
    "region": "singapore",
    "started": "2025-01-15",
    "sshKeys": ["ssh-ed25519 AAAAC3Nza... bob@formabi.com"]
  }
]
```

Why JSON not nix:
- Any LLM can read it directly — no nix knowledge needed
- `jq` queries from shell scripts: `jq '.[] | select(.roles[] == "ops")' roster.json`
- Nix imports it with `builtins.fromJSON (builtins.readFile ./roster.json)`
- Diffable in git — hiring/offboarding shows as clear JSON diffs
- Other tools (CI, handbook generator, billing) consume it without nix

One roster entry feeds:

| Consumer | What it produces |
|----------|-----------------|
| Nix (local) | devShell with engineering + ops tools, repos, AI context |
| Nix (server) | Unix user with SSH key, wheel group (because ops role) |
| Nix (secrets) | agenix access scoped to role |
| LLM | "Alice is an engineer and ops lead in the UK region" |
| Handbook | Team page with name, role, region |
| jq/scripts | Queryable from any shell: `jq '.[] | .name' roster.json` |

### Company State (JSON — current snapshot)

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
// state/customers.json
[
  {
    "name": "demo",
    "domain": "demo.zolanic.space",
    "port": 3100,
    "tier": "free",
    "status": "active",
    "provisioned": "2025-01-01"
  },
  {
    "name": "acme-corp",
    "domain": "acme.formabi.app",
    "port": 3101,
    "tier": "pro",
    "status": "active",
    "provisioned": "2025-03-15"
  }
]
```

```json
// state/priorities.json
[
  "Ship form engine v1 — complete fill/submit flow",
  "Land 3 pilot customers",
  "Hire Singapore product engineer"
]
```

This state data feeds everything:
- **Nix server config** reads customers.json to generate systemd services + nginx vhosts
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

Roles stay in nix because they produce nix outputs (packages, server access levels). But they read from the JSON data layer — `roster.json` determines who has which role.

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
| Know who works here and their roles | people/roster.json |
| Understand the current company stage | state/stage.json |
| Know what matters right now | state/priorities.json |
| Know who the customers are | state/customers.json |
| Explain why Elm was chosen over React | decisions/001-elm-frontend.md |
| Write code that fits the architecture | context/app.md + decisions/ |
| Draft a customer email in the right tone | identity/voice.md + state/customers.json |
| Make a decision consistent with precedent | decisions/index.json + decisions/*.md |
| Generate a pitch with current metrics | state/metrics.json + brand/brand.json |
| Onboard a new hire | people/roster.json + identity/processes.md + roles/ |

The LLM doesn't need to be told "we use Elm" every time. It reads the decision log and knows. It doesn't need to be told "be concise" every time. It reads voice.md and knows. The repo is the company's accumulated intelligence, and the LLM inherits it.

### Context assembly per role

When alice (engineering + ops) opens Claude Code on her bridge, the system assembles:

```
identity/mission.md          ← everyone gets this
identity/voice.md            ← everyone gets this
identity/processes.md        ← everyone gets this
people/roster.json           ← everyone gets this (public info)
state/stage.json             ← everyone gets this
state/priorities.json        ← everyone gets this
brand/brand.json             ← everyone gets this
decisions/index.json         ← everyone gets this
context/app.md               ← because engineering role
context/ops.md               ← because ops role
state/customers.json         ← because ops role (needs instance awareness)
```

When bob (sales) opens Claude Code:

```
identity/mission.md          ← everyone gets this
identity/voice.md            ← everyone gets this
identity/processes.md        ← everyone gets this
people/roster.json           ← everyone gets this
state/stage.json             ← everyone gets this
state/priorities.json        ← everyone gets this
brand/brand.json             ← everyone gets this
decisions/index.json         ← everyone gets this
context/sales.md             ← because sales role
state/metrics.json           ← because sales role (needs numbers for pitches)
```

Same LLM, same repo, different slices. Alice's Claude is an engineering agent. Bob's Claude is a sales agent. Both are formabi.

### The wake as memory

The LLM doesn't just see the current state. The wake — datom log + git history — gives it temporal awareness:

```bash
# What changed about priorities this quarter?
git log --oneline -- state/priorities.json

# When was the last customer provisioned?
git log --oneline -1 -- state/customers.json

# Who approved the decision to use datalog?
git log --oneline -- decisions/002-datalog-architecture.md

# How has the team grown?
git log --oneline -- people/roster.json
```

Every company decision is a commit. Every entity change is a datom. The LLM can reason about *when* things changed and *who* changed them. The wake is the company's memory — and you can't change it, only add to it.

### The company bootstrapping itself

Day zero scenario: you have the root repo with identity/, brand/, and an empty roster. You hand the repo to an LLM and say "help me hire the first engineer." The LLM reads mission.md, voice.md, processes.md, stage.json, priorities.json — and it can:

1. Draft a job posting in formabi's voice
2. Suggest what to look for based on the tech stack (decisions/)
3. Generate the person entry for roster.json once hired
4. Know what repos to give them access to (roles/)
5. Generate their onboarding checklist from processes.md

The company literally uses itself to grow itself.

## The Bridge is a REPL for the Company

The repo is a prompt (read). The bridge is a REPL (read, eval, print, loop). Together they form the complete interface to the company entity.

A programming language REPL has: state you can inspect, functions you can call, side effects that change the world, and a print loop that shows you what happened. The bridge has the same thing:

| REPL concept | The bridge |
|-------------|---------------|
| **Read** | LLM/human reads state: `jq '.[] \| .name' roster.json`, reads mission.md, reads decisions/ |
| **Eval** | `formabi-transact '{"action": "add-person", ...}'` — validates, appends datoms, derives state |
| **Print** | Derived JSON views update, `whoami` shows current state, `halp` shows available commands |
| **Loop** | Git commit captures the transaction. Next read sees the new state. The cycle continues. |

### Everything is a transaction against the company

```bash
# Query the company
jq '.[] | select(.roles[] == "engineering")' people/roster.json
jq '.focus' state/stage.json
git log --oneline -- log/company.datoms

# Mutate the company
formabi-transact '{"action": "add-person", "name": "Dave", "roles": ["engineering"]}'
formabi-transact '{"action": "add-customer", "name": "acme", "tier": "pro"}'
formabi-transact '{"action": "add-role", "person": "dave@formabi.com", "role": "ops"}'

# The company updates
formabi-derive          # replay log → update JSON views
deploy hull       # push state to server — the company's body converges

# The LLM in the shell does the same thing
# "Hire Dave as an engineer" → Claude builds intent JSON → calls formabi-transact
# "Provision acme-corp"      → Claude builds intent JSON → calls formabi-transact
# "Who has ops access?"      → Claude reads roster.json → answers
# "Why do we use Elm?"       → Claude reads decisions/001 → explains
```

### The LLM as bridge crew

In a traditional REPL, a programmer types expressions. On the bridge, the LLM types expressions — but they're company operations, not code. The LLM is the most natural bridge operator because:

- It reads the full state on every session (context assembly from identity/ + state/ + context/)
- It expresses intent as structured JSON (the language of `formabi-transact`)
- It never generates IDs (the tool handles that)
- It reasons about consequences before acting (reads decisions/ for precedent)
- It commits with explanatory messages (git as audit log)

A human on the bridge does the same things, just more manually. The bridge doesn't care who's at the helm — human or LLM. Both read state, both transact, both see results. The company is the ship. The bridge is where you steer it.

Critically: the LLM runs as the user's process. It has the user's filesystem, SSH keys, git identity, and nothing else. It cannot escalate. James's Claude cannot run `deploy hull` because James doesn't have ops access — not because we told Claude not to, but because SSH will reject the connection. The constraint is physical, not policy.

### Deploy as eval

The bridge is where you compose changes. `deploy hull` is where you eval them against the real world. The hull converges to what the repo says — new users get SSH access, new customers get instances, removed people lose access. Deploy is the moment the company's definition becomes the company's reality. The wake records that it happened.

```
bridge (command)                        hull (body)
────────────────                        ────────────
transact → datoms → derive → JSON  ──deploy──→  NixOS converges
    │                                            users created/removed
    │                                            services started/stopped
    ▼                                            nginx reconfigured
wake (trail)                                     secrets re-encrypted
append-only datom log + git commit
```

The gap between "what the repo says" and "what the server is" should always be zero after a deploy. If it's not zero, something drifted. The next deploy fixes it. The repo is always right.

## The Datom Layer: LLM Intent → Immutable Log → Derived State

### The problem with LLMs editing JSON directly

If an LLM edits roster.json to add a person, it might:
- Invent a plausible-looking but invalid ULID
- Accidentally duplicate an ID from elsewhere in the file
- Produce a valid edit but with no traceable atomic history
- Make multiple changes in one edit that can't be individually reverted

The JSON files are human-readable views. They shouldn't be the source of truth.

### The solution: datoms all the way down

The formabi product already uses datoms — `{ e, a, v, op }` — for form data. The same model works for the company itself. The LLM expresses intent as plain JSON. A tool converts that to datoms with proper content-addressed IDs. The datom log is append-only and immutable. Current state is derived by replaying the log.

```
LLM intent (JSON)          Tool layer              Datom log (append-only)
─────────────────    →    ──────────────    →    ─────────────────────────
                          generates IDs,
"add person Dave,         validates,              { e: "01HX7K...", a: "person/name",   v: "Dave",              op: true }
 engineering role,        appends datoms          { e: "01HX7K...", a: "person/email",  v: "dave@formabi.com",  op: true }
 dave@formabi.com"                                { e: "01HX7K...", a: "person/role",   v: "engineering",       op: true }
                                                  { e: "01HX7K...", a: "person/region", v: "us-west",           op: true }


Datom log              Derive tool              Current state (JSON views)
──────────────    →    ──────────────    →    ──────────────────────────────
                       replays log,
append-only            produces current          roster.json
immutable facts        state as JSON             customers.json
                                                 priorities.json
                                                 (these are READ-ONLY views)
```

### What the LLM sees and does

The LLM works with **intent commands** — plain JSON that describes what should change, without IDs:

```json
// "Hire Dave as an engineer in US West"
{
  "action": "add-person",
  "name": "Dave",
  "email": "dave@formabi.com",
  "roles": ["engineering"],
  "region": "us-west",
  "started": "2025-06-01"
}
```

```json
// "Provision a new customer workspace"
{
  "action": "add-customer",
  "name": "acme-corp",
  "domain": "acme.formabi.app",
  "tier": "pro"
}
```

```json
// "Dave is now also doing ops"
{
  "action": "add-role",
  "person": "dave@formabi.com",
  "role": "ops"
}
```

```json
// "Remove Dave from the company"
{
  "action": "retract-person",
  "person": "dave@formabi.com"
}
```

The LLM never generates entity IDs, never touches the datom log directly, and never edits the derived JSON files. It expresses what should happen. The tool makes it so.

### What the tool does

A `formabi-transact` tool (shell command in the devShell):

1. **Validates** the intent against the current derived state (is the email unique? does the role exist? is the port available?)
2. **Generates** a ULID for new entities
3. **Converts** intent to datoms
4. **Appends** datoms to the log file
5. **Re-derives** the JSON views (roster.json, customers.json, etc.)
6. **Commits** both the log and the derived views to git

```bash
# LLM or human runs:
formabi-transact '{"action": "add-person", "name": "Dave", ...}'

# Tool does:
#   1. validates: email not already in roster
#   2. generates: entity ID 01HX7K...
#   3. appends to log/company.datoms:
#        01HX7K... person/name    "Dave"              + 2025-06-01T00:00:00Z
#        01HX7K... person/email   "dave@formabi.com"  + 2025-06-01T00:00:00Z
#        01HX7K... person/role    "engineering"        + 2025-06-01T00:00:00Z
#        01HX7K... person/region  "us-west"            + 2025-06-01T00:00:00Z
#   4. re-derives: people/roster.json, state/customers.json
#   5. commits: "add person: Dave (engineering, us-west)"
```

### The log file

```
# log/company.datoms
# entity              attribute           value                    op  timestamp
01HX7K2A3B4C5D6E7F   person/name         "Alice"                  +   2024-06-01T00:00:00Z
01HX7K2A3B4C5D6E7F   person/email        "alice@formabi.com"      +   2024-06-01T00:00:00Z
01HX7K2A3B4C5D6E7F   person/role         "engineering"            +   2024-06-01T00:00:00Z
01HX7K2A3B4C5D6E7F   person/role         "ops"                    +   2024-06-01T00:00:00Z
01HX7K2A3B4C5D6E7F   person/region       "uk"                     +   2024-06-01T00:00:00Z
01HX7K2A3B4C5D6E7F   person/ssh-key      "ssh-ed25519 AAAA..."    +   2024-06-01T00:00:00Z
01HY9M4D5E6F7G8H9J   customer/name       "demo"                   +   2025-01-01T00:00:00Z
01HY9M4D5E6F7G8H9J   customer/domain     "demo.zolanic.space"     +   2025-01-01T00:00:00Z
01HY9M4D5E6F7G8H9J   customer/port       "3100"                   +   2025-01-01T00:00:00Z
01HY9M4D5E6F7G8H9J   customer/tier       "free"                   +   2025-01-01T00:00:00Z
01HZ3P7Q8R9S0T1U2V   person/name         "Dave"                   +   2025-06-01T00:00:00Z
01HZ3P7Q8R9S0T1U2V   person/email        "dave@formabi.com"       +   2025-06-01T00:00:00Z
01HZ3P7Q8R9S0T1U2V   person/role         "engineering"            +   2025-06-01T00:00:00Z
# Dave leaves — retract all his facts
01HZ3P7Q8R9S0T1U2V   person/name         "Dave"                   -   2025-09-15T00:00:00Z
01HZ3P7Q8R9S0T1U2V   person/email        "dave@formabi.com"       -   2025-09-15T00:00:00Z
01HZ3P7Q8R9S0T1U2V   person/role         "engineering"            -   2025-09-15T00:00:00Z
```

Properties of this log:
- **Append-only** — you never edit a line, you add retractions (`-`)
- **Content-addressed** — entity IDs are ULIDs generated by the tool
- **Time-ordered** — every fact has a timestamp
- **Git-friendly** — appending lines produces clean diffs
- **Replayable** — derive current state by replaying from the top, applying `+` and `-`
- **Time-travelable** — "who worked here on 2025-03-01?" = replay up to that timestamp

### Derived JSON views

The derive tool replays the log and produces read-only JSON:

```bash
formabi-derive   # replays log/company.datoms → people/roster.json, state/customers.json, etc.
```

These JSON files are checked into git alongside the log. They're convenience views — you could delete them and regenerate from the log. But having them means:
- LLMs can read current state without replaying anything
- Nix can `builtins.fromJSON` without custom tooling
- `jq` queries work on derived files
- Git diffs on the JSON show the human-readable effect of datom changes

### Why this matters

| Property | Benefit |
|----------|---------|
| LLM never generates IDs | No hallucinated ULIDs, no collisions |
| Append-only log | Every change is traceable — who, when, what |
| Retractions not deletions | "Dave left" is a fact in the log, not a missing line |
| Derived JSON is read-only | LLM reads JSON for state, writes intent for changes |
| Same model as the product | formabi-app uses datoms for forms, the company uses datoms for itself |
| Git commit per transaction | `git log -- log/company.datoms` = complete company history |
| Time travel | "What did the customer list look like last quarter?" = replay to date |

### Directory update

```
formabi/
├── log/
│   └── company.datoms            ← immutable append-only datom log (source of truth)
├── people/
│   └── roster.json               ← DERIVED from log (read-only view)
├── state/
│   ├── customers.json            ← DERIVED from log (read-only view)
│   ├── stage.json                ← manually maintained (company-level, not entity-level)
│   ├── priorities.json           ← manually maintained (ordered list)
│   └── metrics.json              ← manually maintained or CI-updated
├── ...
```

Not everything goes through datoms. `stage.json` and `priorities.json` are high-level company narrative — maintained as plain JSON by humans/LLMs directly. The datom layer is for **entity data** with identity: people, customers, instances — things that have IDs, lifecycle, and relationships.

## How Far Can This Go?

### The Trinity: Hull, Bridge, Wake

The company has three parts. Nautical names — every ship has all three.

```
       bridge
       (mind)
     the shell
    command here
       /    \
      /      \
   hull ── wake
  (body)   (trail)
  server   history
  runs     remembers
```

**hull** — the vessel. The physical body of the ship. The NixOS server where the company runs, employees SSH in, customer instances serve traffic. What formabi IS, as a running system. `deploy hull`. `ssh hull.formabi.com`.

**bridge** — the command center. Where the captain stands, sees everything, gives orders. The formabi shell — locally via `nix develop`, on the server via SSH. The REPL. Where humans and LLMs query, transact, and steer the company. `bridge` to enter.

**wake** — the trail left behind the ship. You can't change your wake — it's already in the water. The datom log, git history, decision records. Append-only, immutable, the trace of every course the company has ever taken. `wake log`. `wake diff 2025-01 2025-06`. `wake replay --at 2025-03-01`.

They're interdependent:
- **bridge** reads from **wake** (the shell shows current state derived from history)
- **bridge** writes to **wake** (every transaction appends datoms, every commit adds to git)
- **hull** is derived from **wake** (deploy reads the log-derived state and converges the server)
- **bridge** commands **hull** (`deploy hull` pushes the current truth onto the body)

#### As CLI

```bash
bridge                              # enter the formabi shell
bridge --as mei                     # enter as specific person (for context assembly)

deploy hull                         # push current state to the server

wake log                            # show datom history
wake log --entity mei@formabi.com   # show all facts about Mei over time
wake diff 2025-01 2025-06           # what changed: who joined, customers added, decisions made
wake replay --at 2025-03-01         # derive state as of a specific date
wake query "person/role = ops"      # find all entities with ops role
```

#### On the server

```
hull.formabi.com                        ← the company (NixOS)
├── /home/mei/                          ← employee home dirs
├── /home/alice/
├── /srv/formabi/demo/                  ← customer instance
├── /srv/formabi/acme-corp/             ← customer instance
└── /srv/repos/                         ← bare clones of company repos
```

Two separate concerns on one box:
- **hull** = the company as a unix system (employees, repos, tools, company state)
- **formabi instances** = the product serving customers (systemd services, postgres DBs, nginx vhosts)

They share a server for now. They could split to separate machines later. The nix configs are already separate modules.

### Layer 1: Employees as Unix Users

The datom log is the source of truth. NixOS derives unix users from it. Classic unix tools — SSH keys, home dirs, groups, permissions — do the enforcement.

#### Adding an employee

```bash
# 1. Someone with ops role transacts (from their local shell)
formabi-transact '{
  "action": "add-person",
  "name": "Mei Lin",
  "email": "mei@formabi.com",
  "github": "meilin",
  "roles": ["engineering"],
  "region": "singapore",
  "started": "2025-06-02",
  "sshKeys": ["ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... mei@formabi.com"]
}'

# 2. Datoms appended, roster.json derived, committed
# 3. Deploy
deploy hull
```

What NixOS does on `hull` when the config is applied:

```
creates user: mei
  uid:    deterministic from roster position
  home:   /home/mei/
  shell:  /bin/bash (with role-appropriate profile)
  groups: [ formabi engineering ]

writes: /home/mei/.ssh/authorized_keys
  → ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... mei@formabi.com

writes: /home/mei/.claude-context.md
  → assembled from identity/ + context/app.md (because engineering role)

creates: /home/mei/.bashrc
  → PS1 showing role, formabi commands in PATH
  → whoami, halp, formabi-transact (if role allows)

links: /home/mei/repos/formabi-app → /srv/repos/formabi-app
links: /home/mei/repos/latice → /srv/repos/latice
  → only repos matching engineering role

does NOT create: /home/mei/repos/cmdr (not her role)
does NOT create: /home/mei/repos/deck (not her role)
```

Mei can now SSH in:

```
mei@laptop:~$ ssh mei@hull.formabi.com

Welcome to hull — Formabi company server
Person: Mei Lin | Role: engineering | Region: singapore

mei@hull:~$ ls repos/
formabi-app/  latice/

mei@hull:~$ ls /home/
alice/  mei/

mei@hull:~$ ls /home/alice/
ls: cannot open directory '/home/alice/': Permission denied

mei@hull:~$ whoami
Person:  Mei Lin
Roles:   engineering
Region:  singapore
Server:  hull.formabi.com
Home:    /home/mei

mei@hull:~$ halp
Available commands:
  whoami          Your identity and roles
  halp            This help
  formabi-derive  Replay datom log → update views (read-only for you)

Not available (requires ops role):
  formabi-transact
  deploy
```

#### Removing an employee

```bash
# 1. Ops role retracts
formabi-transact '{"action": "retract-person", "person": "mei@formabi.com"}'

# 2. Datom log gets retraction lines, roster.json re-derived (Mei gone), committed
# 3. Deploy
deploy hull
```

What NixOS does:

```
user 'mei' no longer in config

  → archives /home/mei/ to /var/archive/employees/mei-2025-09-15/
  → removes user 'mei' from /etc/passwd
  → removes mei from 'engineering' and 'formabi' groups
  → SSH authorized_keys gone (no user = no file)
  → /home/mei/ removed after archive
```

Mei tries to SSH:

```
mei@laptop:~$ ssh mei@hull.formabi.com
mei@hull.formabi.com: Permission denied (publickey).
```

Done. No manual steps. No "did we remember to revoke her access?" The datom log says she's retracted. The derived roster has no Mei. The NixOS config has no user. SSH rejects. It's the same declarative convergence as everything else.

#### The home directory is the employee's bridge — on the hull

The local shell and the server home dir are the same concept at different locations:

```
Local (mei's laptop)                    Server (hull)
────────────────────                    ──────────────
~/formabi/                              /home/mei/
├── .claude-context.md                  ├── .claude-context.md
├── formabi-app/ (cloned)               ├── repos/formabi-app/ (linked)
├── latice/ (cloned)                    ├── repos/latice/ (linked)
└── (nix develop for tools)             └── (NixOS profile for tools)
```

Same person, same role, same context, same repos. Whether Mei is working locally or SSH'd into hull, she sees the same world. The only difference: locally she has `nix develop`, on the server NixOS manages her environment declaratively.

#### Unix groups from roles

```nix
# Derived from roster.json + roles
users.groups = {
  formabi = {};        # everyone in the company
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

#### The full picture: datom → roster → NixOS → unix

```
datom log                   formabi-derive              NixOS config
(source of truth)    →     (replay + derive)     →     (declarative)
                                                              │
+ mei person/name "Mei"    roster.json updated          users.users.mei = { ... }
+ mei person/role "eng"    (Mei appears)                users.groups.engineering.members
+ mei person/ssh-key "..."                              /home/mei/.ssh/authorized_keys
                                                              │
                                                        deploy hull
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
- mei person/name "Mei"    roster.json updated          users.users.mei GONE
- mei person/role "eng"    (Mei gone)                   groups updated
- mei person/ssh-key "..."                              no authorized_keys
                                                              │
                                                        deploy hull
                                                              │
                                                        NixOS applies:
                                                          archive /home/mei
                                                          userdel mei
                                                          rm authorized_keys
                                                          unlink repos
```

One pipeline. Datom in, unix out. The company manages its employees the same way NixOS manages its packages — declaratively, reproducibly, with full rollback via git.

### Layer 2: Secrets (agenix, scoped by role)

**Today (cmdr)**: `secrets.nix` has a hardcoded list of who can decrypt what.

**With root flake**: Derived from people + roles:

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

### Layer 3: Product Instances (customers as data)

**Today (cmdr)**: `formabi-instances.nix` declares `{ demo = { port = 3100; }; }`. The `deploy-formabi` script creates DB, env file, and deploys.

**With root flake**: Same pattern, but richer. Each instance is a nix attrset:

```nix
# server/instances.nix
{
  demo = {
    port = 3100;
    domain = "demo.zolanic.space";
    tier = "free";
  };
  acme-corp = {
    port = 3101;
    domain = "acme.formabi.app";
    tier = "pro";
    provisioned = "2025-01-15";
  };
}
```

This feeds:
- **systemd services** (one per instance, same as today)
- **nginx vhosts** (domain + SSL per instance)
- **PostgreSQL databases** (one per instance)
- **Monitoring** (alerts scoped to tier/SLA)
- **Billing data** (tier → what to invoice, exported as JSON for accounting)

New customer = add an attrset, deploy. The server converges to include them.

### Layer 4: The Server as the Company's Body

The NixOS server configuration becomes a pure function of the root flake:

```nix
# flake.nix (server output)
nixosConfigurations.hull = nixpkgs.lib.nixosSystem {
  modules = [
    ./server/hull/configuration.nix
    ./server/hull/hardware-configuration.nix
    ./server/shared/common.nix
    (import ./server/shared/users.nix { inherit people roles; })
    (import ./server/shared/formabi.nix { inherit instances; })
    (import ./server/shared/services.nix { inherit brand; })
    agenix.nixosModules.default
  ];
};
```

Everything on the server is derived from the root flake's data:
- **Users** ← people/*.nix
- **SSH access** ← roles (serverAccess)
- **Secrets** ← roles (secretAccess)
- **Product instances** ← server/instances.nix
- **Nginx vhosts** ← instances + brand (domains, SSL)
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

**Per-person agent context**: When alice runs Claude Code on her bridge, the CLAUDE.md is assembled from her specific roles. The AI literally becomes a different agent depending on who is asking.

### Layer 6: Company Knowledge as Nix Packages

The deck repo already builds a handbook as a nix package (`nix build .#handbook`). Extend this:

```nix
# The company's knowledge, built from source
packages.handbook = buildHandbook {
  inherit brand;
  people = import ./people;    # team page auto-generated
  roles = import ./roles;      # role descriptions included
  instances = import ./server/instances.nix;  # customer list for internal reference
};

packages.decks = buildDecks {
  inherit brand;
  # pitch decks with latest metrics
};
```

The handbook is not a static doc someone maintains. It's **derived from the same data** that configures the servers and shells. The team page is always accurate because it reads `people/*.nix`. The architecture diagram is always current because it reads the module definitions.

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

```nix
# scripts/health.sh — queries the company's state
health() {
  echo "People:    $(ls people/*.nix | wc -l) active"
  echo "Roles:     $(ls roles/*.nix | grep -v default | wc -l) defined"
  echo "Modules:   $(ls modules/*.nix | wc -l) registered"
  echo "Instances: $(nix eval .#instances --json | jq length) customer workspaces"
  echo "Server:    $(ssh hull uptime)"
  echo "Last deploy: $(git log --oneline -1 -- server/)"
}
```

The company's vital signs are queryable from the bridge. Not a dashboard — a function.

### Layer 9: Browser Access — Forgejo as the Glass Bridge

The bridge (CLI shell) is powerful but not everyone lives in a terminal. Marketing, sales, new hires — they need to view and edit company content from a browser or phone. The source of truth stays in git (the wake), but we add a glass layer on top.

#### The problem

The formabi system already serves static content well:
- `deck.zolanic.space` serves pitch decks (markdown → marp → HTML → nginx)
- Handbook builds from markdown via pandoc
- Everything is nix-built and nginx-served

But this is **read-only**. A sales person can view decks but can't fix a typo without SSH + git CLI + vim. We need browser-based editing that still commits to git.

#### The solution: Forgejo on hull

**Forgejo** — a lightweight, self-hosted git forge (community fork of Gitea). Runs as a single binary. NixOS has a module for it. It gives you:

- **Web UI for git** — browse repos, view markdown rendered, see commit history
- **In-browser editing** — click a file, edit, commit. Each edit is a real git commit in the wake.
- **Mobile-friendly** — responsive web UI, works on phone
- **Pull requests** — non-technical people can propose changes, someone reviews
- **API** — webhooks on push to trigger nix rebuilds
- **User management** — derives from roster.json (same people, same roles)

```
forgejo.formabi.com                     ← web UI for the company's repos
├── formabi/formabi (root repo)         ← edit identity/, state/, decisions/ in browser
├── formabi/deck (pitch decks)          ← marketing edits slides in browser
└── formabi/handbook                    ← anyone can fix a typo via PR
```

#### How it works

```
James (sales, phone)              Forgejo                    Wake              Hull
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

The source of truth never changes — it's still git, still the wake. Forgejo is just a browser-shaped bridge. Every edit through Forgejo is a git commit with the person's identity. `wake log` shows it the same as any CLI commit.

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

Users are provisioned from roster.json — same people, same roles, same permissions. A sales person sees the repos their role grants. An engineer sees engineering repos. The glass bridge respects the same boundaries as the CLI bridge.

#### Webhook → rebuild pipeline

When someone edits a file through Forgejo:

1. Forgejo commits to the repo (a real git commit)
2. Webhook fires to a small rebuild service on hull
3. Service runs `nix build` for the affected package (deck, handbook, etc.)
4. Nginx serves the new build
5. The wake records the change (it's a git commit)

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

- **The bridge (CLI)** — `formabi-transact`, `deploy hull`, `wake query` stay CLI-only. These are power tools for people on the bridge.
- **The wake** — Forgejo writes to git, which IS the wake. It doesn't have its own history.
- **The hull config** — server changes still go through `deploy hull` from a CLI with ops access.
- **Claude Code** — LLM interaction stays in the terminal bridge. Forgejo is for humans with browsers.

Forgejo is the **glass bridge** — you can see and touch the same things, but through a window. The real bridge (CLI) has the full controls.

#### Other browser tools on hull

Forgejo handles editing. For read-only access, the existing pattern works:

| Content | Source | Build | Served at |
|---------|--------|-------|-----------|
| Pitch decks | deck/decks/*.md | marp (nix build) | deck.zolanic.space |
| Handbook | deck/handbook/*.md | pandoc (nix build) | handbook.formabi.com |
| Brand site | zolanic/ | astro (nix build) | zolanic.space |
| Analytics | plausible | NixOS service | analytics.zolanic.space |
| Secret sharing | privatebin | NixOS service | yo.zolanic.space |
| Code / editing | forgejo | NixOS service | code.formabi.com |

Everything is a NixOS service on hull, declared in nix, served by nginx with ACME SSL. Add a new service = add a nix module + nginx vhost, deploy.

## Onboarding: Two New Employees

Before either person starts, someone with ops access has already run:

```bash
formabi-transact '{
  "action": "add-person",
  "name": "Mei Lin",
  "email": "mei@formabi.com",
  "github": "meilin",
  "roles": ["engineering"],
  "region": "singapore",
  "started": "2025-06-02",
  "sshKeys": ["ssh-ed25519 AAAAC3Nza... mei@formabi.com"]
}'

formabi-transact '{
  "action": "add-person",
  "name": "James",
  "email": "james@formabi.com",
  "github": "jamesw",
  "roles": ["sales"],
  "region": "uk",
  "started": "2025-06-02"
}'
```

Datoms appended, roster.json derived, committed, deployed. They exist in the company before they've touched a keyboard.

---

### Mei Lin — Core Engineer, Singapore

Mei gets a one-line instruction from her manager: "Clone formabi, enter the shell, run `onboard`."

```
mei@laptop:~$ git clone git@github.com:formabi/formabi.git
mei@laptop:~$ cd formabi
mei@laptop:~/formabi$ nix develop

formabi shell — 0 of 5 modules active

  base: git, jq, halp, whoami, onboard

Run 'onboard' to get started.

mei@laptop:~/formabi$ onboard
```

The onboard script detects her git email, matches it to the roster, and starts a chat session with the LLM. The LLM has the full company context loaded.

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

  Your role means you'll be building the product, running customer
  integrations, and working with regional sales in your timezone.

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

  base:   git, jq, halp, whoami, onboard
  app:    elm, node, cargo, dev, test, build
  latice: cargo, buf, protobuf

mei@laptop:~/formabi$ whoami

Person:  Mei Lin
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

  base: git, jq, halp, whoami, onboard

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

  From state/customers.json:

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
  - When you land a customer, it becomes a datom:
      formabi-transact '{"action": "add-customer", "name": "...", "tier": "pro"}'
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

  base: git, jq, halp, whoami, onboard
  deck: marp, build-deck, present

james@laptop:~/formabi$ whoami

Person:  James
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

Both employees started from the same place: `git clone`, `bridge`, `onboard`. The system:

1. **Identified them** from roster.json (matched by git email)
2. **Scoped their experience** by role — different repos, different tools, different context
3. **Oriented them** to the company — mission, stage, priorities, team, how we work
4. **Got them productive** — specific repos to clone, specific first-week tasks
5. **Shaped their AI** — Claude Code on each person's bridge is a different agent

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
| Can't do | deploy (no ops role, no SSH key) | transact customers (no ops role), push to formabi-app (no GitHub access) |
| LLM bounded by | Mei's filesystem, SSH keys, git identity | James's filesystem, SSH keys, git identity |

## What This Looks Like Day-to-Day

### Hiring someone

```bash
# 1. Create person file
vim people/dave.nix
# { name = "Dave"; github = "dave"; roles = [ "engineering" ]; sshKeys = [ "ssh-ed25519 ..." ]; }

# 2. PR, review, merge
git add people/dave.nix && git commit -m "add dave, engineering role"
git push  # PR → review → merge

# 3. Deploy server (dave gets SSH if his role warrants it)
deploy hull

# 4. Dave clones root repo, runs onboard
# dave$ git clone ... && cd formabi && nix develop
# dave$ onboard
# → "Your roles: engineering. Clone formabi-app and latice."
```

### Offboarding someone

```bash
# 1. Remove person file
git rm people/dave.nix
git commit -m "offboard dave"
git push  # PR → review → merge

# 2. Deploy
deploy hull
# → dave's unix user removed, SSH key gone, secret access revoked
```

### Adding a customer

```bash
# 1. Add instance
vim server/instances.nix
# acme = { port = 3101; domain = "acme.formabi.app"; tier = "pro"; };

# 2. Commit, deploy
git commit -am "provision acme-corp workspace"
deploy hull
# → systemd service created, nginx vhost created, SSL provisioned, DB created
```

### Changing a role's permissions

```bash
# 1. Edit role
vim roles/engineering.nix
# Change serverAccess from "none" to "ssh" (read-only shell)

# 2. Commit, deploy
git commit -am "grant engineers read-only server access"
deploy hull
# → all engineers now have SSH access (no sudo). Derived from their person files.
```

## Security Model

### The hard rule: LLM <= User

The LLM never has more permissions than the active user. This isn't enforced by telling the LLM to behave — it's enforced by the architecture. There is no mechanism for escalation because every layer is physically bounded by what the user has on disk.

| What the LLM tries to do | What actually constrains it |
|---------------------------|----------------------------|
| Read source code | Can only read files on disk. User hasn't cloned the repo? Files don't exist. LLM can't read what isn't there. |
| Run `formabi-transact` | Tool validates against roster.json. User's git email must match a person with a role that permits the action. No role = transaction rejected. |
| Run `deploy hull` | Requires SSH key on the server. Server users derived from roster.json + roles. No ops role = no SSH key = deploy fails. |
| Decrypt a secret | agenix requires the user's age key. No secretAccess in role = key not in the encryption list = decryption fails. |
| Push to a repo | Requires GitHub write access. User's GitHub account doesn't have access = push rejected. |
| See context for another role | CLAUDE.md assembled from modules on disk. No repo cloned = no context fragment included. |

The enforcement is **physical, not policy**. The LLM runs as a process in the user's shell. It has the user's filesystem, the user's SSH keys, the user's git config. It literally cannot reach what the user cannot reach. There is no API key that grants the LLM separate access. There is no service account. The LLM is the user.

### Layer summary

| Layer | Mechanism | Boundary |
|-------|-----------|----------|
| Code access | GitHub repo permissions | Can't clone = can't see |
| Local tools | builtins.pathExists | No repo on disk = no tools |
| LLM permissions | Runs as user's process | LLM = user, always |
| Transact access | formabi-transact validates git email + role | No matching role = rejected |
| Server access | Derived from people + roles | serverAccess field → SSH key or nothing |
| Secret access | agenix + derived from roles | secretAccess field → age key or nothing |
| AI context | Assembled from modules on disk | Only sees what's present |
| Instance data | Server-side, not in local shells | Customers isolated per-instance |
| Audit trail | Git history on root repo | Every change is a reviewed commit under user's identity |

The root repo is safe for everyone to read. It contains structure, people (public info + SSH pubkeys), and roles. Actual secrets are agenix-encrypted — only decryptable by people whose roles grant access. The LLM's context, tools, and capabilities are exactly the user's context, tools, and capabilities — nothing more.

## What's In vs What's Out

### In the repo (the company's definition)

| What | Format | Example |
|------|--------|---------|
| Identity | markdown | mission.md, voice.md, processes.md |
| People | JSON | roster.json — who, what role, when started |
| State | JSON | stage.json, customers.json, priorities.json |
| Decisions | markdown + JSON index | why we chose Elm, why datalog, why nix |
| Brand | JSON | colors, fonts, name, strapline |
| Infrastructure | nix | shells, server configs, builds |
| Secrets (encrypted) | age files | only decryptable by role |
| AI context | markdown | per-role fragments assembled on shell entry |

### Out of the repo (stays external)

| What | Why | Where instead |
|------|-----|---------------|
| Conversations | Ephemeral, high-volume | Slack, email |
| Money | Regulated, needs real accounting | Xero/Stripe |
| Legal contracts | Need legal standing | Lawyers, DocuSign |
| Customer data | Per-instance, belongs to customers | PostgreSQL per-instance |
| Real-time metrics | Changes every second | Plausible, server monitoring |
| Passwords/tokens | Never in git, even encrypted | agenix for infra, 1Password for humans |

The line: **the repo defines the shape and brain of the company. It doesn't hold customer data or move money.** State like metrics.json is a curated snapshot (updated periodically or by CI), not a live feed.

## Migration Path

### Phase 0: Identity + state (no code changes, pure data)
- Create root repo
- Write identity/mission.md, voice.md, processes.md from existing deck/handbook content
- Write brand/brand.json (already defined in deck/flake.nix)
- Write state/stage.json, priorities.json manually
- Write first decision records from existing architecture
- **Test**: hand the repo to an LLM and ask it to describe formabi. If it sounds right, the data is good.

### Phase 1: Datom log + derive tooling
- Create log/company.datoms with initial facts (seed from current people + customer knowledge)
- Build `formabi-transact` tool (validates intent JSON, generates ULIDs, appends datoms)
- Build `formabi-derive` tool (replays log, produces roster.json + customers.json)
- Prove: LLM can run `formabi-transact` to add a person, derived JSON updates correctly
- Prove: `git log -- log/company.datoms` shows clean append-only history

### Phase 2: Nix shells (local only, no server changes)
- Add flake.nix that reads derived roster.json + roles, composes devShells
- Add modules/ with pathExists detection for sibling repos
- Prove: `nix develop .#alice` gives the right tools
- cmdr/deploy/ stays as-is, untouched

### Phase 3: AI context assembly
- Add context/ fragments per role
- Shell entry assembles CLAUDE.md from identity/ + state/ + context/ based on active modules
- Prove: Claude Code on the bridge behaves differently per role

### Phase 4: Server users derived from roster.json
- server/shared/users.nix reads people/roster.json (which is derived from datom log)
- Deploy. Server users now come from the same datom log as local shells.

### Phase 5: Server fully derived from root
- Migrate cmdr/deploy/ into root repo's server/
- customers.json (derived from datoms) feeds systemd services + nginx vhosts
- secrets.nix derived from roster.json + roles
- deploy-rs in root flake
- cmdr becomes scripts-only (no config)

### Phase 6: The company maintains itself
- Handbook auto-generated from identity/ + people/ + brand/
- CI validates: every person in derived roster has SSH key, every customer has valid port/domain
- Onboard script reads derived state + roles, guides new hire
- Health script queries all layers
- LLM adds people/customers via `formabi-transact`, never edits JSON directly

## Open Questions

- Should the root repo be `formabi/formabi` or `formabi/root` or just the org-level `.github` repo?
- Do worktree branches (app-blue, app-green, app-purple) get their own modules or share the app module?
- Should roles compose? (e.g., "lead" = engineering + ops + hiring)
- How to handle the transition period where cmdr/deploy/ and root/server/ coexist?
- Should devenv (used today) coexist with pure flake devShells or be replaced?
- Should decisions/ use a stricter schema (like ADR) or stay freeform?
- What's the minimum viable root repo? Just identity/ + log/ + state/ without nix?
- What language for `formabi-transact` / `formabi-derive`? Shell script + jq? Rust CLI? Nix derivation?
- Should the datom log format match the product's datom format exactly, or be a simplified version?
- How to handle SSH keys in the datom log? They're large — store as datoms or keep as a separate file referenced by entity ID?
- Should `formabi-transact` be an MCP tool so Claude Code can call it directly?
