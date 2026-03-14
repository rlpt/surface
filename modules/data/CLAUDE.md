# Data Module — LLM Context

Company data stored as YAML files in `data/` at the project root, versioned by git.

## Files

- `data/shares.yaml` — share classes, holders, events, pools, pool members
- `data/officers.yaml` — company officers (directors, secretary, PSC)
- `data/compliance.yaml` — statutory compliance deadlines
- `data/board.yaml` — meetings, attendees, minutes, resolutions

## Shared library

`modules/data/scripts/datalib.py` provides:

```python
import datalib
data = datalib.load("shares")       # returns dict of lists from YAML
datalib.save("shares", data)         # writes back to YAML
datalib.git_commit("message")        # git add data/ && git commit

# Linting (schema validation)
datalib.lint("shares", data)         # returns list of error strings

# Referential integrity
datalib.validate_refs("shares", data)  # returns list of error strings

# Computed views
datalib.holdings(share_data)         # current holdings per holder/class
datalib.cap_table(share_data)        # cap table with percentages
datalib.class_availability(share_data)  # issued vs authorised
datalib.vesting_schedule(share_data) # per-holder vesting status
datalib.compliance_upcoming(comp_data) # deadlines due within 90 days
datalib.changelog(domain, since)     # structured git log for a domain
datalib.print_table(rows)            # formatted CLI output
```

## Linting

Schema validation checks:
- Required fields present and non-empty
- Type correctness (str, int, float, bool)
- Enum values (event_type, account_type, status, frequency, role)

## Querying

```python
data = datalib.load("shares")
holders = data.get("holders", [])
events = data.get("share_events", [])
# Filter in Python
richard_events = [e for e in events if e["holder_id"] == "richard"]
```

## Version control

Data is versioned by git alongside code:

```bash
data diff                    # git diff data/
data log                     # git log data/
data changelog shares        # structured change history
```

## CLI

```bash
data status               # show YAML files and entry counts
data check                # run lint + referential integrity checks
data lint                 # run schema validation only
data edit                 # open data/ in $EDITOR
data log                  # git history for data/
data diff                 # uncommitted changes to data/
data changelog <domain>   # structured change history
```

## Reset

To reset to seed data: `git checkout -- data/`
