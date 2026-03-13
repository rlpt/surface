# Data Module — LLM Context

Version-controlled database using Dolt. The database is auto-initialised on shell entry and lives at `$SURFACE_DB` (`.surface-db/` in the project root, gitignored).

## Schema

Tables: `accounts`, `transactions`, `postings`, `share_classes`, `holders`, `share_events`, `pools`, `pool_members`

Views: `holdings`, `cap_table`, `account_balances`, `class_availability`

Schema definition: `modules/data/schema.sql`
Seed data: `modules/data/seed.sql`

## Querying

```bash
data sql "SELECT * FROM holders;"           # run a query
data sql                                     # interactive SQL shell
```

Or from scripts:
```bash
(cd "$SURFACE_DB" && dolt sql -q "SELECT ...")      # table output
(cd "$SURFACE_DB" && dolt sql -r csv -q "SELECT ...")  # CSV output
```

## Version control (dolt)

Every data change can be committed independently of git:

```bash
data sql "INSERT INTO holders (id, display_name) VALUES ('alice', 'Alice Smith');"
data diff                    # see what changed
data commit -m "add alice"   # commit in dolt
data log                     # view dolt history
```

Branching works like git:
```bash
data branch experiment       # create branch
data checkout experiment     # switch to it
data sql "..."               # make changes
data commit -m "try thing"
data checkout main           # switch back
```

## Workflow: modifying data

1. Run the appropriate INSERT/UPDATE/DELETE via `data sql`
2. Run the relevant check command (`accounts check`, `shares check`)
3. Commit with `data commit -m "description"`

## Remotes

The production data lives on formrunner, served via Dolt's remotesapi at `http://formrunner:50051/surface-db`. The `data` command auto-configures the `origin` remote on first sync.

```bash
# Push local data to formrunner (after committing)
data sync

# Pull from formrunner to local
data sync pull
```

Override the remote URL with `SURFACE_DOLT_REMOTE`. CI clones from `http://localhost:50051/surface-db` (same machine). Falls back to seed data if the remote is unavailable.

## Reset

If the database gets corrupted or you want to start fresh:
```bash
data reset    # drops and recreates from schema.sql + seed.sql
```
