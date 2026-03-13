# Data Module — LLM Context

Company data stored as TOML files in `data/` at the project root, versioned by git.

## Files

- `data/accounts.toml` — chart of accounts, transactions, postings
- `data/shares.toml` — share classes, holders, events, pools, pool members
- `data/crm.toml` — customers, contacts, contracts, lines, clauses
- `data/board.toml` — meetings, attendees, minutes, resolutions

## Shared library

`modules/data/scripts/datalib.py` provides:

```python
import datalib
data = datalib.load("shares")       # returns dict of lists from TOML
datalib.save("shares", data)         # writes back to TOML
datalib.git_commit("message")        # git add data/ && git commit

# Computed views
datalib.holdings(share_data)         # current holdings per holder/class
datalib.cap_table(share_data)        # cap table with percentages
datalib.class_availability(share_data)  # issued vs authorised
datalib.account_balances(acct_data)  # aggregated balances
datalib.contract_summary(crm_data)   # contracts with MRR
datalib.renewals_due(crm_data)       # active contracts expiring in 90 days
datalib.print_table(rows)            # formatted CLI output
```

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
```

## CLI

```bash
data status               # show TOML files and entry counts
data check                # run all module validation checks
data edit                 # open data/ in $EDITOR
data log                  # git history for data/
data diff                 # uncommitted changes to data/
```

## Reset

To reset to seed data: `git checkout -- data/`
