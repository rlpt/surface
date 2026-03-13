"""datalib — shared TOML data layer for surface modules."""

import os
import subprocess
import sys
import tomllib
from collections import defaultdict
from datetime import date, timedelta

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
DATA_DIR = os.path.join(SURFACE_ROOT, "data")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load(domain):
    """Load a TOML data file, returning a dict of lists."""
    path = os.path.join(DATA_DIR, f"{domain}.toml")
    if not os.path.exists(path):
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def save(domain, data):
    """Write data dict back to TOML."""
    path = os.path.join(DATA_DIR, f"{domain}.toml")
    with open(path, "w") as f:
        f.write(dump_toml(data))


def git_commit(msg):
    """Stage data/ and git commit."""
    subprocess.run(["git", "add", "data/"], cwd=SURFACE_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=SURFACE_ROOT, check=True)


# ---------------------------------------------------------------------------
# TOML writer (no external dependency)
# ---------------------------------------------------------------------------

def dump_toml(data):
    """Dump a dict of lists-of-dicts as TOML array-of-tables."""
    lines = []
    for key, value in data.items():
        if isinstance(value, list):
            for item in value:
                lines.append(f"[[{key}]]")
                for k, v in item.items():
                    lines.append(f"{k} = {_toml_val(v)}")
                lines.append("")
        elif isinstance(value, dict):
            lines.append(f"[{key}]")
            for k, v in value.items():
                lines.append(f"{k} = {_toml_val(v)}")
            lines.append("")
    return "\n".join(lines) + "\n" if lines else ""


def _toml_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return str(v)
    if isinstance(v, str):
        escaped = v.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return f'"{v}"'


# ---------------------------------------------------------------------------
# Computed views (replicate SQL views in Python)
# ---------------------------------------------------------------------------

def holdings(share_data=None):
    """Compute current holdings per holder/class.

    Returns list of dicts: [{"holder_id", "share_class", "shares_held"}, ...]
    """
    if share_data is None:
        share_data = load("shares")
    events = share_data.get("share_events", [])
    totals = defaultdict(int)
    for e in events:
        key = (e["holder_id"], e["share_class"])
        if e["event_type"] in ("grant", "transfer-in"):
            totals[key] += e["quantity"]
        else:
            totals[key] -= e["quantity"]
    return [
        {"holder_id": hid, "share_class": cls, "shares_held": held}
        for (hid, cls), held in sorted(totals.items())
        if held > 0
    ]


def cap_table(share_data=None):
    """Compute cap table with percentages.

    Returns list of dicts: [{"holder", "holder_id", "class", "held", "pct"}, ...]
    """
    if share_data is None:
        share_data = load("shares")
    h = holdings(share_data)
    total = sum(r["shares_held"] for r in h)
    if total == 0:
        return []
    holders_map = {
        r["id"]: r["display_name"] for r in share_data.get("holders", [])
    }
    result = []
    for r in h:
        result.append({
            "holder": holders_map.get(r["holder_id"], r["holder_id"]),
            "holder_id": r["holder_id"],
            "class": r["share_class"],
            "held": r["shares_held"],
            "pct": round(r["shares_held"] * 100.0 / total, 1),
        })
    result.sort(key=lambda x: x["holder"])
    return result


def class_availability(share_data=None):
    """Compute issued vs authorised per class.

    Returns list of dicts: [{"class", "authorised", "issued", "available"}, ...]
    """
    if share_data is None:
        share_data = load("shares")
    h = holdings(share_data)
    issued_map = defaultdict(int)
    for r in h:
        issued_map[r["share_class"]] += r["shares_held"]
    result = []
    for sc in share_data.get("share_classes", []):
        issued = issued_map.get(sc["name"], 0)
        result.append({
            "class": sc["name"],
            "authorised": sc["authorised"],
            "issued": issued,
            "available": sc["authorised"] - issued,
        })
    return result


def account_balances(acct_data=None):
    """Compute account balances from postings.

    Returns list of dicts: [{"account_path", "account_type", "balance", "currency"}, ...]
    """
    if acct_data is None:
        acct_data = load("accounts")
    accounts_map = {
        a["path"]: a["account_type"] for a in acct_data.get("accounts", [])
    }
    balances = defaultdict(lambda: defaultdict(float))
    for p in acct_data.get("postings", []):
        key = p["account_path"]
        currency = p.get("currency", "GBP")
        balances[key][currency] += p["amount"]
    result = []
    for path in sorted(balances.keys()):
        for currency, balance in balances[path].items():
            result.append({
                "account_path": path,
                "account_type": accounts_map.get(path, "unknown"),
                "balance": round(balance, 2),
                "currency": currency,
            })
    result.sort(key=lambda x: (x["account_type"], x["account_path"]))
    return result


def contract_summary(crm_data=None):
    """Compute contract summary with MRR.

    Returns list of dicts with: id, company, title, status, effective_date,
    term_months, auto_renew, currency, mrr, line_count, clause_count
    """
    if crm_data is None:
        crm_data = load("crm")
    customers_map = {
        c["id"]: c["company"] for c in crm_data.get("customers", [])
    }
    lines_by_contract = defaultdict(list)
    for ln in crm_data.get("contract_lines", []):
        lines_by_contract[ln["contract_id"]].append(ln)
    clauses_by_contract = defaultdict(list)
    for cl in crm_data.get("contract_clauses", []):
        clauses_by_contract[cl["contract_id"]].append(cl)

    result = []
    for ct in crm_data.get("contracts", []):
        lines = lines_by_contract.get(ct["id"], [])
        clauses = clauses_by_contract.get(ct["id"], [])
        mrr = 0.0
        for ln in lines:
            qty = float(ln.get("quantity", 1))
            price = float(ln["unit_price"])
            freq = ln.get("frequency", "monthly")
            if freq == "monthly":
                mrr += qty * price
            elif freq == "quarterly":
                mrr += qty * price / 3
            elif freq == "annual":
                mrr += qty * price / 12
        result.append({
            "id": ct["id"],
            "company": customers_map.get(ct["customer_id"], ct["customer_id"]),
            "title": ct["title"],
            "status": ct.get("status", "draft"),
            "effective_date": ct.get("effective_date", ""),
            "term_months": ct.get("term_months", ""),
            "auto_renew": ct.get("auto_renew", False),
            "currency": ct.get("currency", "GBP"),
            "mrr": round(mrr, 2),
            "line_count": len(lines),
            "clause_count": len(clauses),
        })
    return result


def renewals_due(crm_data=None):
    """Compute active contracts expiring within 90 days.

    Returns list of dicts: id, company, title, status, auto_renew, expiry_date, days_left
    """
    if crm_data is None:
        crm_data = load("crm")
    customers_map = {
        c["id"]: c["company"] for c in crm_data.get("customers", [])
    }
    today = date.today()
    cutoff = today + timedelta(days=90)
    result = []
    for ct in crm_data.get("contracts", []):
        if ct.get("status") != "active":
            continue
        term = ct.get("term_months")
        eff = ct.get("effective_date")
        if not term or not eff:
            continue
        try:
            eff_date = date.fromisoformat(str(eff))
            term_months = int(term)
        except (ValueError, TypeError):
            continue
        # Approximate month addition
        expiry_year = eff_date.year + (eff_date.month + term_months - 1) // 12
        expiry_month = (eff_date.month + term_months - 1) % 12 + 1
        expiry_day = min(eff_date.day, 28)
        expiry = date(expiry_year, expiry_month, expiry_day)
        if expiry <= cutoff:
            result.append({
                "id": ct["id"],
                "company": customers_map.get(ct["customer_id"], ct["customer_id"]),
                "title": ct["title"],
                "status": ct["status"],
                "auto_renew": ct.get("auto_renew", False),
                "expiry_date": expiry.isoformat(),
                "days_left": (expiry - today).days,
            })
    result.sort(key=lambda x: x["expiry_date"])
    return result


# ---------------------------------------------------------------------------
# Referential integrity
# ---------------------------------------------------------------------------

def validate_refs(domain, data):
    """Check referential integrity for a domain. Returns list of error strings."""
    errors = []

    def _check(items, field, valid_set, label):
        for item in items:
            val = item.get(field)
            if val is not None and val not in valid_set:
                errors.append(f"{label}: {field} '{val}' not found")

    if domain == "shares":
        holder_ids = {h["id"] for h in data.get("holders", [])}
        class_names = {c["name"] for c in data.get("share_classes", [])}
        pool_names = {p["name"] for p in data.get("pools", [])}
        _check(data.get("share_events", []), "holder_id", holder_ids, "share_events")
        _check(data.get("share_events", []), "share_class", class_names, "share_events")
        _check(data.get("pools", []), "share_class", class_names, "pools")
        _check(data.get("pool_members", []), "holder_id", holder_ids, "pool_members")
        _check(data.get("pool_members", []), "pool_name", pool_names, "pool_members")

    elif domain == "accounts":
        account_paths = {a["path"] for a in data.get("accounts", [])}
        txn_ids = {t["id"] for t in data.get("transactions", [])}
        _check(data.get("postings", []), "account_path", account_paths, "postings")
        _check(data.get("postings", []), "txn_id", txn_ids, "postings")

    elif domain == "crm":
        customer_ids = {c["id"] for c in data.get("customers", [])}
        contract_ids = {c["id"] for c in data.get("contracts", [])}
        _check(data.get("contacts", []), "customer_id", customer_ids, "contacts")
        _check(data.get("contracts", []), "customer_id", customer_ids, "contracts")
        _check(data.get("contract_lines", []), "contract_id", contract_ids, "contract_lines")
        _check(data.get("contract_clauses", []), "contract_id", contract_ids, "contract_clauses")

    elif domain == "board":
        meeting_ids = {m["id"] for m in data.get("board_meetings", [])}
        _check(data.get("board_attendees", []), "meeting_id", meeting_ids, "board_attendees")
        _check(data.get("board_minutes", []), "meeting_id", meeting_ids, "board_minutes")
        _check(data.get("board_resolutions", []), "meeting_id", meeting_ids, "board_resolutions")

    return errors


# ---------------------------------------------------------------------------
# Table formatting (for CLI output)
# ---------------------------------------------------------------------------

def print_table(rows, columns=None):
    """Print a list of dicts as a formatted table."""
    if not rows:
        print("No data.")
        return
    if columns is None:
        columns = list(rows[0].keys())
    widths = {col: len(col) for col in columns}
    for row in rows:
        for col in columns:
            widths[col] = max(widths[col], len(str(row.get(col, ""))))
    header = "  ".join(col.ljust(widths[col]) for col in columns)
    print(header)
    print("  ".join("-" * widths[col] for col in columns))
    for row in rows:
        line = "  ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        print(line)
