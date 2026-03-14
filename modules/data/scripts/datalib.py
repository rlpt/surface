"""datalib — shared YAML data layer for surface modules."""

import os
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta

import yaml

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
DATA_DIR = os.path.join(SURFACE_ROOT, "data")
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")
LETTERHEAD_TEMPLATE = os.path.join(SURFACE_ROOT, "modules", "brand", "letterhead.typ")
LOGO_PATH = os.path.join(SURFACE_ROOT, "modules", "brand", "logo.svg")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Load / save
# ---------------------------------------------------------------------------

def load(domain):
    """Load data from data/<domain>.yaml, returning a dict of lists."""
    path = os.path.join(DATA_DIR, f"{domain}.yaml")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    # Normalise: convert date objects to ISO strings for consistency
    result = {}
    for key, rows in data.items():
        if isinstance(rows, dict):
            result[key] = _normalise_row(rows)
            continue
        if not isinstance(rows, list):
            result[key] = rows
            continue
        result[key] = [_normalise_row(row) for row in rows]
    return result


def save(domain, data):
    """Write data dict to data/<domain>.yaml."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{domain}.yaml")
    # Prepare data for YAML output
    out = {}
    for key, rows in data.items():
        if isinstance(rows, list):
            out[key] = [_prepare_row(row) for row in rows]
        elif isinstance(rows, dict):
            out[key] = _prepare_row(rows)
        else:
            out[key] = rows
    with open(path, "w") as f:
        yaml.dump(out, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def git_commit(msg):
    """Stage data/ and git commit."""
    subprocess.run(["git", "add", "data/"], cwd=SURFACE_ROOT, check=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=SURFACE_ROOT, check=True)


# ---------------------------------------------------------------------------
# Type helpers
# ---------------------------------------------------------------------------

def _normalise_row(row):
    """Normalise a YAML-loaded row: convert date objects to ISO strings."""
    if not isinstance(row, dict):
        return row
    out = {}
    for k, v in row.items():
        if isinstance(v, date) and not isinstance(v, type(None)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def _prepare_row(row):
    """Prepare a row for YAML output: convert ISO date strings back to date objects."""
    if not isinstance(row, dict):
        return row
    out = {}
    for k, v in row.items():
        if isinstance(v, str) and _is_date_key(k):
            try:
                out[k] = date.fromisoformat(v)
            except ValueError:
                out[k] = v
        else:
            out[k] = v
    return out


_DATE_SUFFIXES = ("_date", "_start", "_at")
_DATE_NAMES = ("effective_date", "event_date", "meeting_date", "txn_date",
               "voted_date", "vesting_start", "appointed_date", "resigned_date",
               "filed_date", "due_date", "incorporation_date", "created_date",
               "delivered_date", "satisfied_date", "declaration_date", "payment_date")


def _is_date_key(key):
    """Heuristic: does this key name suggest a date value?"""
    return key in _DATE_NAMES or any(key.endswith(s) for s in _DATE_SUFFIXES)


# ---------------------------------------------------------------------------
# Schema definitions (for linting)
# ---------------------------------------------------------------------------

SCHEMAS = {
    "shares": {
        "share_classes": {
            "required": ["name", "nominal_value", "nominal_currency", "authorised"],
            "types": {"name": str, "nominal_value": (int, float), "nominal_currency": str, "authorised": int},
            "values": {},
        },
        "holders": {
            "required": ["id", "display_name"],
            "types": {"id": str, "display_name": str},
            "values": {},
        },
        "share_events": {
            "required": ["event_date", "event_type", "holder_id", "share_class", "quantity"],
            "types": {"event_date": str, "event_type": str, "holder_id": str,
                       "share_class": str, "quantity": int,
                       "vesting_start": str, "vesting_months": int, "cliff_months": int},
            "values": {"event_type": ["grant", "transfer-in", "transfer-out", "cancel"]},
        },
        "pools": {
            "required": ["name", "share_class", "budget"],
            "types": {"name": str, "share_class": str, "budget": int},
            "values": {},
        },
        "pool_members": {
            "required": ["pool_name", "holder_id"],
            "types": {"pool_name": str, "holder_id": str},
            "values": {},
        },
    },
    "officers": {
        "officers": {
            "required": ["id", "person_name", "role", "appointed_date"],
            "types": {"id": str, "person_name": str, "role": str, "appointed_date": str},
            "values": {"role": ["director", "secretary", "psc"]},
        },
    },
    "compliance": {
        "deadlines": {
            "required": ["id", "title", "due_date", "frequency", "category", "status"],
            "types": {"id": str, "title": str, "due_date": str, "frequency": str,
                       "category": str, "status": str},
            "values": {
                "frequency": ["annual", "quarterly", "monthly", "one-off"],
                "category": ["companies-house", "hmrc", "other"],
                "status": ["upcoming", "filed", "overdue"],
            },
        },
    },
    "charges": {
        "charges": {
            "required": ["id", "created_date", "description", "chargee", "amount", "status"],
            "types": {"id": str, "charge_code": str, "created_date": str,
                       "description": str, "chargee": str, "amount": int,
                       "currency": str, "status": str, "delivered_date": str,
                       "satisfied_date": str},
            "values": {"status": ["outstanding", "satisfied"]},
        },
    },
    "dividends": {
        "dividends": {
            "required": ["id", "declaration_date", "share_class", "amount_per_share", "status"],
            "types": {"id": str, "declaration_date": str, "payment_date": str,
                       "share_class": str, "amount_per_share": (int, float),
                       "currency": str, "tax_voucher_ref": str, "status": str,
                       "resolution_id": str},
            "values": {"status": ["declared", "paid", "cancelled"]},
        },
    },
    "company": {
        "company": {
            "required": ["name", "company_number", "jurisdiction", "company_type", "incorporation_date"],
            "types": {"name": str, "company_number": str, "jurisdiction": str,
                       "company_type": str, "incorporation_date": str,
                       "accounting_reference_date": str, "articles": str},
            "values": {
                "jurisdiction": ["england-wales", "scotland", "northern-ireland"],
                "company_type": ["private-limited", "public-limited", "llp", "unlimited"],
            },
        },
    },
    "board": {
        "board_meetings": {
            "required": ["id", "meeting_date", "title"],
            "types": {"id": str, "meeting_date": str, "title": str},
            "values": {"status": ["scheduled", "in-progress", "completed", "cancelled"]},
        },
        "board_attendees": {
            "required": ["meeting_id", "person_name"],
            "types": {"meeting_id": str, "person_name": str},
            "values": {"role": ["chair", "secretary", "director", "observer"]},
        },
        "board_minutes": {
            "required": ["meeting_id", "seq", "item_text"],
            "types": {"meeting_id": str, "seq": int, "item_text": str},
            "values": {},
        },
        "board_resolutions": {
            "required": ["id", "meeting_id", "resolution_text"],
            "types": {"id": str, "meeting_id": str, "resolution_text": str},
            "values": {"status": ["pending", "passed", "failed", "withdrawn"]},
        },
    },
}


# ---------------------------------------------------------------------------
# Linting
# ---------------------------------------------------------------------------

def lint(domain, data):
    """Validate data against schema. Returns list of error strings."""
    errors = []
    schema = SCHEMAS.get(domain, {})

    for table_name, table_schema in schema.items():
        rows = data.get(table_name, [])
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            continue
        required = table_schema.get("required", [])
        types = table_schema.get("types", {})
        values = table_schema.get("values", {})

        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                errors.append(f"{table_name}[{i}]: expected a mapping, got {type(row).__name__}")
                continue

            # Required fields
            for field in required:
                if field not in row or row[field] is None or row[field] == "":
                    errors.append(f"{table_name}[{i}]: missing required field '{field}'")

            # Type checks
            for field, expected_type in types.items():
                val = row.get(field)
                if val is None or val == "":
                    continue
                if not isinstance(val, expected_type):
                    errors.append(
                        f"{table_name}[{i}]: field '{field}' expected "
                        f"{_type_name(expected_type)}, got {type(val).__name__} ({val!r})"
                    )

            # Enum value checks
            for field, allowed in values.items():
                val = row.get(field)
                if val is not None and val != "" and val not in allowed:
                    errors.append(
                        f"{table_name}[{i}]: field '{field}' value '{val}' "
                        f"not in {allowed}"
                    )

    return errors


def _type_name(t):
    """Human-readable type name."""
    if isinstance(t, tuple):
        return "/".join(x.__name__ for x in t)
    return t.__name__


# ---------------------------------------------------------------------------
# Computed views
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




def vesting_schedule(share_data=None):
    """Compute vesting status per holder.

    Returns list of dicts: holder_id, share_class, total_granted, vested,
    unvested, cliff_date, fully_vested_date, next_vest_date, pct_vested
    """
    if share_data is None:
        share_data = load("shares")
    today = date.today()
    result = []
    for e in share_data.get("share_events", []):
        if e["event_type"] != "grant":
            continue
        vs = e.get("vesting_start")
        vm = e.get("vesting_months")
        cm = e.get("cliff_months", 0)
        qty = e["quantity"]
        hid = e["holder_id"]
        cls = e["share_class"]

        if not vs or not vm:
            # Fully vested immediately
            result.append({
                "holder_id": hid, "share_class": cls,
                "total_granted": qty, "vested": qty, "unvested": 0,
                "cliff_date": "", "fully_vested_date": "",
                "next_vest_date": "", "pct_vested": 100.0,
            })
            continue

        start = date.fromisoformat(str(vs))
        cliff_date = _add_months(start, cm) if cm else start
        fully_vested_date = _add_months(start, vm)
        months_elapsed = _months_between(start, today)

        if today < cliff_date:
            vested = 0
        elif today >= fully_vested_date:
            vested = qty
        else:
            vested = int(qty * months_elapsed / vm)

        unvested = qty - vested
        pct = round(vested * 100.0 / qty, 1) if qty > 0 else 0.0

        # Next vest date: next month boundary after today
        if vested < qty and today >= cliff_date:
            next_vest = _add_months(start, months_elapsed + 1)
        elif today < cliff_date:
            next_vest = cliff_date
        else:
            next_vest = None

        result.append({
            "holder_id": hid, "share_class": cls,
            "total_granted": qty, "vested": vested, "unvested": unvested,
            "cliff_date": cliff_date.isoformat(),
            "fully_vested_date": fully_vested_date.isoformat(),
            "next_vest_date": next_vest.isoformat() if next_vest else "",
            "pct_vested": pct,
        })
    return result


def compliance_upcoming(comp_data=None):
    """Deadlines due within 90 days.

    Returns list of dicts: id, title, due_date, frequency, category, status, days_left
    """
    if comp_data is None:
        comp_data = load("compliance")
    today = date.today()
    cutoff = today + timedelta(days=90)
    result = []
    for d in comp_data.get("deadlines", []):
        try:
            due = date.fromisoformat(str(d["due_date"]))
        except (ValueError, TypeError):
            continue
        if due <= cutoff and d.get("status") != "filed":
            result.append({
                "id": d["id"],
                "title": d["title"],
                "due_date": d["due_date"],
                "frequency": d["frequency"],
                "category": d["category"],
                "status": "overdue" if due < today else d.get("status", "upcoming"),
                "days_left": (due - today).days,
            })
    result.sort(key=lambda x: x["due_date"])
    return result


def changelog(domain, since=None):
    """Parse git log for data/<domain>.yaml, return structured list of changes."""
    cmd = ["git", "log", "--pretty=format:%H|%ai|%s", "--follow"]
    if since:
        cmd.append(f"--since={since}")
    cmd.extend(["--", f"data/{domain}.yaml"])
    try:
        out = subprocess.run(cmd, cwd=SURFACE_ROOT, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return []
    result = []
    for line in out.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) == 3:
            result.append({
                "commit": parts[0][:8],
                "date": parts[1].split(" ")[0],
                "message": parts[2],
            })
    return result


def _add_months(d, months):
    """Add months to a date."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, 28)
    return date(year, month, day)


def _months_between(start, end):
    """Approximate months between two dates."""
    return (end.year - start.year) * 12 + end.month - start.month


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


# ---------------------------------------------------------------------------
# Branded PDF generation
# ---------------------------------------------------------------------------

def generate_branded_pdf(output_file, markdown):
    """Generate a PDF with Formabi letterhead via pandoc + typst template.

    Takes markdown content, converts to typst via pandoc, wraps in the
    letterhead template, and compiles to PDF.
    """
    import tempfile

    os.makedirs(DOWNLOADS_DIR, exist_ok=True)

    root = os.path.abspath(SURFACE_ROOT)
    logo = os.path.join(root, "modules", "brand", "logo.svg")
    template_abs = os.path.join(root, "modules", "brand", "letterhead.typ")

    # Paths relative to SURFACE_ROOT for typst
    template_rel = "modules/brand/letterhead.typ"
    logo_rel = "modules/brand/logo.svg"

    if not os.path.exists(template_abs):
        # Fallback: plain pandoc PDF without letterhead
        subprocess.run(
            [
                "pandoc",
                "--pdf-engine=typst",
                "-V", "mainfont=Source Sans 3",
                "-V", "margin-top=2cm",
                "-V", "margin-bottom=2cm",
                "-V", "margin-left=2cm",
                "-V", "margin-right=2cm",
                "-o", output_file,
            ],
            input=markdown,
            text=True,
            check=True,
        )
        print(output_file)
        _upload_to_drive(output_file)
        return

    # Step 1: Convert markdown to typst markup via pandoc
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "typst"],
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
    )
    typst_body = result.stdout

    # Post-process: pandoc emits #horizontalrule for markdown '---' but
    # typst has no built-in horizontalrule variable.  Replace with a line.
    typst_body = typst_body.replace(
        "#horizontalrule",
        "#line(length: 100%, stroke: 0.5pt + luma(180))",
    )

    # Post-process: make tables span full page width with equal fractional columns.
    # Pandoc emits "columns: N," — replace with fractional widths.
    import re
    def _fix_table_columns(m):
        n = int(m.group(1))
        fracs = ", ".join(["1fr"] * n)
        return f"columns: ({fracs})"
    typst_body = re.sub(r"\bcolumns: (\d+),\n", lambda m: _fix_table_columns(m) + ",\n", typst_body)

    # Step 2: Build a typst document that imports the template
    # Logo path relative to the template file (both in modules/brand/)
    logo_line = '  logo-path: "logo.svg",' if os.path.exists(logo) else ""
    typst_doc = f"""\
#import "{template_rel}": letterhead

#show: letterhead.with(
{logo_line}
)

{typst_body}
"""

    # Step 3: Write to temp file in SURFACE_ROOT and compile with --root
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".typ", dir=root, delete=False
    ) as tmp:
        tmp.write(typst_doc)
        tmp_path = tmp.name

    try:
        subprocess.run(
            ["typst", "compile", "--root", root, tmp_path, output_file],
            cwd=root,
            check=True,
        )
    finally:
        os.unlink(tmp_path)

    print(output_file)
    _upload_to_drive(output_file)


# ---------------------------------------------------------------------------
# Google Drive upload (via rclone)
# ---------------------------------------------------------------------------

def _upload_to_drive(file_path):
    """Upload a file to Google Drive via rclone. Silent no-op if GDRIVE_REMOTE not set.

    Requires:
      GDRIVE_REMOTE — rclone remote and path (e.g. "gdrive:formabi/documents")

    Rclone must be configured with a Google Drive remote (run: rclone config).
    """
    remote = os.environ.get("GDRIVE_REMOTE")
    if not remote:
        return

    try:
        filename = os.path.basename(file_path)
        result = subprocess.run(
            ["rclone", "copyto", file_path, f"{remote}/{filename}"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  -> uploaded to Drive")
        else:
            print(f"  -> Drive upload failed: {result.stderr.strip()}", file=sys.stderr)
    except FileNotFoundError:
        print(f"  -> Drive upload skipped (rclone not found)", file=sys.stderr)
