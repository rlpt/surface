#!/usr/bin/env python3
"""CRM — customer contract management (dolt)"""

import csv
import io
import os
import subprocess
import sys
from datetime import date

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
SURFACE_DB = os.environ.get("SURFACE_DB", os.path.join(SURFACE_ROOT, ".surface-db"))
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def check_db():
    if not os.path.isdir(os.path.join(SURFACE_DB, ".dolt")):
        die("database not initialised — run 'data init'")


def dsql(query):
    check_db()
    sys.stdout.flush()
    subprocess.run(["dolt", "sql", "-q", query], cwd=SURFACE_DB, check=True)


def dsql_csv(query):
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = r.stdout.strip().split("\n")
    return lines[1:] if len(lines) > 1 else []


def dsql_val(query):
    rows = dsql_csv(query)
    return rows[0] if rows else ""


def dsql_rows(query):
    check_db()
    r = subprocess.run(
        ["dolt", "sql", "-r", "csv", "-q", query],
        cwd=SURFACE_DB,
        capture_output=True,
        text=True,
        check=True,
    )
    reader = csv.DictReader(io.StringIO(r.stdout))
    return list(reader)


def dolt_commit(msg):
    subprocess.run(["dolt", "add", "."], cwd=SURFACE_DB, check=True)
    subprocess.run(
        ["dolt", "commit", "--allow-empty", "-m", msg],
        cwd=SURFACE_DB, check=True,
    )


def esc(s):
    return s.replace("'", "''")


# ── Standard clauses ────────────────────────────────────────────────────────

STANDARD_CLAUSES = [
    (
        "Definitions",
        'In this Agreement: "Provider" means the party providing the Services; '
        '"Customer" means the party receiving the Services; "Services" means the '
        'services described in the Commercial Terms; "Effective Date" means the '
        'date on which this Agreement comes into force; "Term" means the period '
        "specified in the Commercial Terms.",
    ),
    (
        "Services",
        "The Provider shall supply the Services to the Customer in accordance "
        "with the Commercial Terms and any applicable service levels. The Provider "
        "shall perform the Services with reasonable skill and care.",
    ),
    (
        "Fees and Payment",
        "The Customer shall pay the fees set out in the Commercial Terms. "
        "Invoices are due within the payment terms specified. Late payments shall "
        "bear interest at 3% per annum above the Bank of England base rate. "
        "All amounts are exclusive of VAT unless stated otherwise.",
    ),
    (
        "Term and Renewal",
        "This Agreement commences on the Effective Date and continues for the "
        "Term specified in the Commercial Terms. If auto-renewal is specified, "
        "the Agreement shall automatically renew for successive periods equal to "
        "the original Term unless either party gives written notice of "
        "non-renewal at least the number of days specified as the notice period "
        "before the end of the then-current Term.",
    ),
    (
        "Termination",
        "Either party may terminate this Agreement: (a) by giving written notice "
        "as specified in the notice period if the other party commits a material "
        "breach and fails to remedy it within 30 days of written notice; (b) "
        "immediately if the other party becomes insolvent, enters administration, "
        "or ceases to carry on business.",
    ),
    (
        "Intellectual Property",
        "All intellectual property rights in the Services and any deliverables "
        "shall remain vested in the Provider. The Customer is granted a "
        "non-exclusive, non-transferable licence to use the Services for its "
        "internal business purposes during the Term.",
    ),
    (
        "Confidentiality",
        "Each party shall keep confidential all information of a confidential "
        "nature obtained from the other party and shall not disclose it to any "
        "third party without prior written consent, except as required by law or "
        "to professional advisers. This obligation survives termination for a "
        "period of 3 years.",
    ),
    (
        "Data Protection",
        "Each party shall comply with its obligations under applicable data "
        "protection legislation including the UK GDPR and the Data Protection "
        "Act 2018. Where the Provider processes personal data on behalf of the "
        "Customer, the parties shall enter into a separate data processing "
        "agreement.",
    ),
    (
        "Limitation of Liability",
        "Neither party excludes or limits liability for death or personal injury "
        "caused by negligence, fraud, or any other liability that cannot be "
        "excluded by law. Subject to the foregoing, each party's total aggregate "
        "liability under this Agreement shall not exceed the total fees paid or "
        "payable in the 12-month period preceding the claim. Neither party shall "
        "be liable for indirect, consequential, or special losses.",
    ),
    (
        "Force Majeure",
        "Neither party shall be liable for any failure or delay in performing "
        "its obligations where such failure or delay results from circumstances "
        "beyond its reasonable control. If such circumstances continue for more "
        "than 90 days, either party may terminate this Agreement by written notice.",
    ),
    (
        "General",
        "This Agreement constitutes the entire agreement between the parties. "
        "No variation shall be effective unless in writing and signed by both "
        "parties. A waiver of any right under this Agreement is only effective "
        "if it is in writing. This Agreement may not be assigned without the "
        "prior written consent of the other party. Nothing in this Agreement "
        "creates a partnership or agency relationship between the parties.",
    ),
    (
        "Governing Law and Jurisdiction",
        "This Agreement and any dispute arising out of or in connection with it "
        "shall be governed by and construed in accordance with the law specified "
        "in the Commercial Terms. The parties submit to the exclusive jurisdiction "
        "of the courts specified in the Commercial Terms.",
    ),
]


# ── Read commands ───────────────────────────────────────────────────────────


def cmd_customers():
    dsql(
        "SELECT id, company, company_number, "
        "(SELECT COUNT(*) FROM contracts ct WHERE ct.customer_id = cu.id) AS contracts, "
        "(SELECT COUNT(*) FROM contacts co WHERE co.customer_id = cu.id) AS contacts "
        "FROM customers cu ORDER BY company;"
    )


def cmd_customer(cust_id):
    if not cust_id:
        die("usage: crm customer <customer-id>")
    company = dsql_val(f"SELECT company FROM customers WHERE id = '{esc(cust_id)}';")
    if not company:
        die(f"unknown customer: {cust_id}")
    print(f"# {company}\n")
    dsql(
        f"SELECT id, company, company_number, address, notes "
        f"FROM customers WHERE id = '{esc(cust_id)}';"
    )
    print("\n## Contacts")
    dsql(
        f"SELECT id, name, email, role FROM contacts "
        f"WHERE customer_id = '{esc(cust_id)}' ORDER BY name;"
    )
    print("\n## Contracts")
    dsql(
        f"SELECT id, title, status, effective_date, term_months, auto_renew "
        f"FROM contracts WHERE customer_id = '{esc(cust_id)}' ORDER BY effective_date DESC;"
    )


def cmd_contracts(filter_=""):
    if filter_ == "active":
        dsql(
            "SELECT id, company, title, effective_date, term_months, auto_renew, "
            "ROUND(mrr, 2) AS mrr, currency "
            "FROM contract_summary WHERE status = 'active' ORDER BY company;"
        )
    elif filter_ == "draft":
        dsql(
            "SELECT id, company, title, line_count, clause_count "
            "FROM contract_summary WHERE status = 'draft' ORDER BY company;"
        )
    else:
        dsql(
            "SELECT id, company, title, status, effective_date, "
            "ROUND(mrr, 2) AS mrr, currency "
            "FROM contract_summary ORDER BY status, company;"
        )


def cmd_contract(contract_id):
    if not contract_id:
        die("usage: crm contract <contract-id>")
    title = dsql_val(
        f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';"
    )
    if not title:
        die(f"unknown contract: {contract_id}")
    print(f"# {title}\n")
    dsql(
        f"SELECT ct.id, cu.company, ct.title, ct.status, ct.effective_date, "
        f"ct.term_months, ct.auto_renew, ct.payment_terms, ct.currency, "
        f"ct.governing_law, ct.jurisdiction, ct.notice_period_days, ct.notes "
        f"FROM contracts ct JOIN customers cu ON cu.id = ct.customer_id "
        f"WHERE ct.id = '{esc(contract_id)}';"
    )
    print("\n## Lines")
    dsql(
        f"SELECT seq, description, quantity, unit_price, frequency "
        f"FROM contract_lines WHERE contract_id = '{esc(contract_id)}' ORDER BY seq;"
    )
    total_mrr = dsql_val(
        f"SELECT ROUND(COALESCE(SUM(CASE frequency "
        f"WHEN 'monthly' THEN quantity * unit_price "
        f"WHEN 'quarterly' THEN quantity * unit_price / 3 "
        f"WHEN 'annual' THEN quantity * unit_price / 12 "
        f"ELSE 0 END), 0), 2) FROM contract_lines "
        f"WHERE contract_id = '{esc(contract_id)}';"
    )
    print(f"\nMRR: £{total_mrr}")
    print("\n## Clauses")
    dsql(
        f"SELECT seq, heading FROM contract_clauses "
        f"WHERE contract_id = '{esc(contract_id)}' ORDER BY seq;"
    )


def cmd_renewals():
    count = dsql_val("SELECT COUNT(*) FROM renewals_due;")
    if count == "0":
        print("No renewals due in the next 90 days.")
        return
    dsql("SELECT * FROM renewals_due;")


def cmd_find(term):
    if not term:
        die("usage: crm find <term>")
    e = esc(term)
    dsql(
        f"SELECT cu.id, cu.company, "
        f"(SELECT COUNT(*) FROM contracts ct WHERE ct.customer_id = cu.id) AS contracts "
        f"FROM customers cu "
        f"WHERE cu.company LIKE '%{e}%' OR cu.id LIKE '%{e}%' "
        f"ORDER BY cu.company;"
    )


# ── Write commands ──────────────────────────────────────────────────────────


def cmd_add_customer(args):
    if len(args) < 2:
        die('usage: crm add <customer-id> "Company Name" [company-number]')
    cust_id = args[0]
    company = args[1]
    co_num = args[2] if len(args) > 2 else ""
    dsql(
        f"INSERT INTO customers (id, company, company_number) "
        f"VALUES ('{esc(cust_id)}', '{esc(company)}', '{esc(co_num)}');"
    )
    dolt_commit(f"crm: add customer {company} ({cust_id})")
    print(f"Added customer: {company} ({cust_id})")


def cmd_add_contact(args):
    if len(args) < 3:
        die('usage: crm contact <customer-id> "Name" "email" [role]')
    cust_id, name, email = args[0], args[1], args[2]
    role = args[3] if len(args) > 3 else ""
    contact_id = f"{cust_id}-{name.lower().split()[0]}"
    dsql(
        f"INSERT INTO contacts (id, customer_id, name, email, role) "
        f"VALUES ('{esc(contact_id)}', '{esc(cust_id)}', '{esc(name)}', "
        f"'{esc(email)}', '{esc(role)}');"
    )
    dolt_commit(f"crm: add contact {name} at {cust_id}")
    print(f"Added contact: {name} ({contact_id})")


def cmd_new_contract(args):
    if len(args) < 2:
        die('usage: crm new <customer-id> "Contract Title"')
    cust_id = args[0]
    title = args[1]
    company = dsql_val(f"SELECT company FROM customers WHERE id = '{esc(cust_id)}';")
    if not company:
        die(f"unknown customer: {cust_id}")
    # generate id: ct-<customer>-<seq>
    count = dsql_val(
        f"SELECT COUNT(*) FROM contracts WHERE customer_id = '{esc(cust_id)}';"
    )
    seq = int(count) + 1
    contract_id = f"ct-{cust_id}-{seq}"
    dsql(
        f"INSERT INTO contracts (id, customer_id, title) "
        f"VALUES ('{esc(contract_id)}', '{esc(cust_id)}', '{esc(title)}');"
    )
    dolt_commit(f"crm: draft contract {contract_id} — {title}")
    print(f"Created draft contract: {contract_id}")


def cmd_line(args):
    if len(args) < 4:
        die('usage: crm line <contract-id> <seq> "description" <unit-price> [frequency]')
    contract_id, seq_s, desc, price_s = args[0], args[1], args[2], args[3]
    freq = args[4] if len(args) > 4 else "monthly"
    title = dsql_val(f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';")
    if not title:
        die(f"unknown contract: {contract_id}")
    dsql(
        f"INSERT INTO contract_lines (contract_id, seq, description, unit_price, frequency) "
        f"VALUES ('{esc(contract_id)}', {seq_s}, '{esc(desc)}', {price_s}, '{esc(freq)}');"
    )
    dolt_commit(f"crm: line {seq_s} on {contract_id} — {desc}")
    print(f"Added line {seq_s}: {desc} @ £{price_s}/{freq}")


def cmd_clause(args):
    if len(args) < 4:
        die('usage: crm clause <contract-id> <seq> "Heading" "body text"')
    contract_id, seq_s, heading, body = args[0], args[1], args[2], args[3]
    title = dsql_val(f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';")
    if not title:
        die(f"unknown contract: {contract_id}")
    dsql(
        f"INSERT INTO contract_clauses (contract_id, seq, heading, body) "
        f"VALUES ('{esc(contract_id)}', {seq_s}, '{esc(heading)}', '{esc(body)}');"
    )
    dolt_commit(f"crm: clause {seq_s} on {contract_id} — {heading}")
    print(f"Added clause {seq_s}: {heading}")


def cmd_standard_clauses(contract_id):
    if not contract_id:
        die("usage: crm standard-clauses <contract-id>")
    title = dsql_val(f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';")
    if not title:
        die(f"unknown contract: {contract_id}")
    existing = dsql_val(
        f"SELECT COUNT(*) FROM contract_clauses WHERE contract_id = '{esc(contract_id)}';"
    )
    start_seq = int(existing) + 1
    for i, (heading, body) in enumerate(STANDARD_CLAUSES):
        seq = start_seq + i
        dsql(
            f"INSERT INTO contract_clauses (contract_id, seq, heading, body) "
            f"VALUES ('{esc(contract_id)}', {seq}, '{esc(heading)}', '{esc(body)}');"
        )
    dolt_commit(f"crm: standard clauses on {contract_id}")
    print(f"Added {len(STANDARD_CLAUSES)} standard clauses (seq {start_seq}–{start_seq + len(STANDARD_CLAUSES) - 1})")


def cmd_set(args):
    if len(args) < 3:
        die("usage: crm set <contract-id> <field> <value>")
    contract_id, field, value = args[0], args[1], args[2]
    allowed = {
        "effective-date": "effective_date",
        "term": "term_months",
        "auto-renew": "auto_renew",
        "payment-terms": "payment_terms",
        "currency": "currency",
        "governing-law": "governing_law",
        "jurisdiction": "jurisdiction",
        "notice-period": "notice_period_days",
        "status": "status",
        "notes": "notes",
    }
    col = allowed.get(field)
    if not col:
        die(f"unknown field: {field}\nAllowed: {', '.join(sorted(allowed.keys()))}")
    title = dsql_val(f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';")
    if not title:
        die(f"unknown contract: {contract_id}")
    if col in ("term_months", "notice_period_days"):
        dsql(f"UPDATE contracts SET {col} = {value} WHERE id = '{esc(contract_id)}';")
    elif col == "auto_renew":
        bval = "TRUE" if value.lower() in ("true", "yes", "1") else "FALSE"
        dsql(f"UPDATE contracts SET {col} = {bval} WHERE id = '{esc(contract_id)}';")
    else:
        dsql(f"UPDATE contracts SET {col} = '{esc(value)}' WHERE id = '{esc(contract_id)}';")
    dolt_commit(f"crm: set {field}={value} on {contract_id}")
    print(f"Set {field} = {value} on {contract_id}")


def cmd_activate(contract_id):
    if not contract_id:
        die("usage: crm activate <contract-id>")
    title = dsql_val(f"SELECT title FROM contracts WHERE id = '{esc(contract_id)}';")
    if not title:
        die(f"unknown contract: {contract_id}")
    dsql(f"UPDATE contracts SET status = 'active' WHERE id = '{esc(contract_id)}';")
    dolt_commit(f"crm: activate {contract_id}")
    print(f"Contract {contract_id} is now active")


# ── PDF generation ──────────────────────────────────────────────────────────


def generate_pdf(output_file, markdown):
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    subprocess.run(
        [
            "pandoc",
            "--pdf-engine=typst",
            "-V", "mainfont=Helvetica",
            "-V", "margin-top=2.5cm",
            "-V", "margin-bottom=2.5cm",
            "-V", "margin-left=3cm",
            "-V", "margin-right=3cm",
            "-o", output_file,
        ],
        input=markdown,
        text=True,
        check=True,
    )
    print(output_file)


def contract_markdown(contract_id):
    """Build full contract document as markdown."""
    rows = dsql_rows(
        f"SELECT ct.id, cu.company, cu.company_number, cu.address, "
        f"ct.title, ct.status, ct.effective_date, ct.term_months, "
        f"ct.auto_renew, ct.payment_terms, ct.currency, "
        f"ct.governing_law, ct.jurisdiction, ct.notice_period_days "
        f"FROM contracts ct JOIN customers cu ON cu.id = ct.customer_id "
        f"WHERE ct.id = '{esc(contract_id)}'"
    )
    if not rows:
        return None
    c = rows[0]

    lines = dsql_rows(
        f"SELECT seq, description, quantity, unit_price, frequency "
        f"FROM contract_lines WHERE contract_id = '{esc(contract_id)}' ORDER BY seq"
    )
    clauses = dsql_rows(
        f"SELECT seq, heading, body FROM contract_clauses "
        f"WHERE contract_id = '{esc(contract_id)}' ORDER BY seq"
    )

    md = []

    # Title
    md.append(f"# {c['title']}\n")
    md.append(f"**Agreement Reference:** {c['id']}\n")

    status_label = c['status'].upper()
    if status_label == "DRAFT":
        md.append("**⚠ DRAFT — NOT YET EXECUTED**\n")

    md.append("---\n")

    # Parties
    md.append("## Parties\n")
    md.append(f"1. **Provider:** Formabi Ltd\n")
    customer_line = f"2. **Customer:** {c['company']}"
    if c.get("company_number"):
        customer_line += f" (Company No. {c['company_number']})"
    md.append(customer_line + "\n")
    if c.get("address"):
        md.append(f"   Registered address: {c['address']}\n")
    md.append("")

    # Commercial Terms
    md.append("## Commercial Terms\n")
    md.append("| Term | Value |")
    md.append("|------|-------|")
    if c.get("effective_date"):
        md.append(f"| Effective Date | {c['effective_date']} |")
    if c.get("term_months"):
        md.append(f"| Term | {c['term_months']} months |")
    auto = "Yes" if c.get("auto_renew") in ("1", "true", "True", True) else "No"
    md.append(f"| Auto-Renewal | {auto} |")
    md.append(f"| Payment Terms | {c.get('payment_terms', 'net-30')} |")
    md.append(f"| Currency | {c.get('currency', 'GBP')} |")
    if c.get("notice_period_days"):
        md.append(f"| Notice Period | {c['notice_period_days']} days |")
    md.append(f"| Governing Law | {c.get('governing_law', 'England and Wales')} |")
    md.append(f"| Jurisdiction | {c.get('jurisdiction', 'Courts of England and Wales')} |")
    md.append("")

    # Service Lines
    if lines:
        md.append("## Services and Fees\n")
        md.append("| # | Description | Qty | Unit Price | Frequency |")
        md.append("|---|-------------|-----|------------|-----------|")
        total_annual = 0
        for ln in lines:
            qty = float(ln["quantity"])
            price = float(ln["unit_price"])
            freq = ln["frequency"]
            md.append(
                f"| {ln['seq']} | {ln['description']} | {qty:g} "
                f"| £{price:,.2f} | {freq} |"
            )
            if freq == "monthly":
                total_annual += qty * price * 12
            elif freq == "quarterly":
                total_annual += qty * price * 4
            elif freq == "annual":
                total_annual += qty * price
            elif freq == "one-off":
                total_annual += qty * price  # show as-is

        md.append("")
        md.append(f"**Total annual value: £{total_annual:,.2f}**\n")

    # Clauses
    if clauses:
        for cl in clauses:
            md.append(f"## {cl['seq']}. {cl['heading']}\n")
            md.append(f"{cl['body']}\n")

    # Signature blocks
    md.append("---\n")
    md.append("## Execution\n")
    md.append("This Agreement is executed by the duly authorised representatives "
              "of each party on the date set out below.\n")

    md.append("**For and on behalf of Formabi Ltd:**\n")
    md.append("Name: ___________________________\n")
    md.append("Title: ___________________________\n")
    md.append("Date: ___________________________\n")
    md.append("Signature: ___________________________\n")
    md.append("")

    md.append(f"**For and on behalf of {c['company']}:**\n")
    md.append("Name: ___________________________\n")
    md.append("Title: ___________________________\n")
    md.append("Date: ___________________________\n")
    md.append("Signature: ___________________________\n")

    return "\n".join(md)


def cmd_pdf(contract_id):
    if not contract_id:
        die("usage: crm pdf <contract-id>")
    md = contract_markdown(contract_id)
    if md is None:
        die(f"unknown contract: {contract_id}")
    today = date.today().isoformat()
    output = os.path.join(DOWNLOADS_DIR, f"{contract_id}-{today}.pdf")
    generate_pdf(output, md)


# ── Help & routing ──────────────────────────────────────────────────────────


def cmd_help():
    with open(
        os.path.join(SURFACE_ROOT, "modules/crm/scripts/help.txt")
    ) as f:
        print(f.read(), end="")


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "help"

    match cmd:
        # read
        case "customers":
            cmd_customers()
        case "customer":
            cmd_customer(args[1] if len(args) > 1 else "")
        case "contracts":
            cmd_contracts(args[1] if len(args) > 1 else "")
        case "contract":
            cmd_contract(args[1] if len(args) > 1 else "")
        case "renewals":
            cmd_renewals()
        case "find":
            cmd_find(args[1] if len(args) > 1 else "")
        # write
        case "add":
            cmd_add_customer(args[1:])
        case "contact":
            cmd_add_contact(args[1:])
        case "new":
            cmd_new_contract(args[1:])
        case "line":
            cmd_line(args[1:])
        case "clause":
            cmd_clause(args[1:])
        case "standard-clauses":
            cmd_standard_clauses(args[1] if len(args) > 1 else "")
        case "set":
            cmd_set(args[1:])
        case "activate":
            cmd_activate(args[1] if len(args) > 1 else "")
        # output
        case "pdf":
            cmd_pdf(args[1] if len(args) > 1 else "")
        case _:
            cmd_help()


if __name__ == "__main__":
    main()
