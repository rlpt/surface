#!/usr/bin/env python3
"""CRM — customer contract management (toml)"""

import os
import subprocess
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/scripts"))
import datalib

SURFACE_ROOT = os.environ.get("SURFACE_ROOT", ".")
DOWNLOADS_DIR = os.path.join(SURFACE_ROOT, "downloads")


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


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
    crm = datalib.load("crm")
    customers = crm.get("customers", [])
    contracts = crm.get("contracts", [])
    contacts = crm.get("contacts", [])
    rows = []
    for cu in sorted(customers, key=lambda c: c.get("company", "")):
        cid = cu["id"]
        ct_count = sum(1 for ct in contracts if ct["customer_id"] == cid)
        co_count = sum(1 for co in contacts if co["customer_id"] == cid)
        rows.append({
            "id": cid,
            "company": cu.get("company", ""),
            "company_number": cu.get("company_number", ""),
            "contracts": ct_count,
            "contacts": co_count,
        })
    datalib.print_table(rows)


def cmd_customer(cust_id):
    if not cust_id:
        die("usage: crm customer <customer-id>")
    crm = datalib.load("crm")
    cu = next((c for c in crm.get("customers", []) if c["id"] == cust_id), None)
    if not cu:
        die(f"unknown customer: {cust_id}")
    print(f"# {cu['company']}\n")
    datalib.print_table([{
        "id": cu["id"],
        "company": cu.get("company", ""),
        "company_number": cu.get("company_number", ""),
        "address": cu.get("address", ""),
        "notes": cu.get("notes", ""),
    }])
    print("\n## Contacts")
    contacts = sorted(
        [co for co in crm.get("contacts", []) if co["customer_id"] == cust_id],
        key=lambda c: c.get("name", ""),
    )
    datalib.print_table(
        [{"id": co["id"], "name": co.get("name", ""), "email": co.get("email", ""),
          "role": co.get("role", "")} for co in contacts],
    )
    print("\n## Contracts")
    contracts = sorted(
        [ct for ct in crm.get("contracts", []) if ct["customer_id"] == cust_id],
        key=lambda c: c.get("effective_date", ""),
        reverse=True,
    )
    datalib.print_table(
        [{"id": ct["id"], "title": ct.get("title", ""), "status": ct.get("status", "draft"),
          "effective_date": ct.get("effective_date", ""), "term_months": ct.get("term_months", ""),
          "auto_renew": ct.get("auto_renew", False)} for ct in contracts],
    )


def cmd_contracts(filter_=""):
    rows = datalib.contract_summary()
    if filter_ == "active":
        rows = [r for r in rows if r["status"] == "active"]
        rows.sort(key=lambda r: r["company"])
        datalib.print_table(rows, columns=[
            "id", "company", "title", "effective_date", "term_months",
            "auto_renew", "mrr", "currency",
        ])
    elif filter_ == "draft":
        rows = [r for r in rows if r["status"] == "draft"]
        rows.sort(key=lambda r: r["company"])
        datalib.print_table(rows, columns=[
            "id", "company", "title", "line_count", "clause_count",
        ])
    else:
        rows.sort(key=lambda r: (r["status"], r["company"]))
        datalib.print_table(rows, columns=[
            "id", "company", "title", "status", "effective_date", "mrr", "currency",
        ])


def cmd_contract(contract_id):
    if not contract_id:
        die("usage: crm contract <contract-id>")
    crm = datalib.load("crm")
    ct = next((c for c in crm.get("contracts", []) if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    cu = next((c for c in crm.get("customers", []) if c["id"] == ct["customer_id"]), None)
    company = cu["company"] if cu else ct["customer_id"]

    print(f"# {ct['title']}\n")
    datalib.print_table([{
        "id": ct["id"],
        "company": company,
        "title": ct.get("title", ""),
        "status": ct.get("status", "draft"),
        "effective_date": ct.get("effective_date", ""),
        "term_months": ct.get("term_months", ""),
        "auto_renew": ct.get("auto_renew", False),
        "payment_terms": ct.get("payment_terms", ""),
        "currency": ct.get("currency", "GBP"),
        "governing_law": ct.get("governing_law", ""),
        "jurisdiction": ct.get("jurisdiction", ""),
        "notice_period_days": ct.get("notice_period_days", ""),
        "notes": ct.get("notes", ""),
    }])

    print("\n## Lines")
    lines = sorted(
        [ln for ln in crm.get("contract_lines", []) if ln["contract_id"] == contract_id],
        key=lambda l: l.get("seq", 0),
    )
    datalib.print_table(
        [{"seq": ln["seq"], "description": ln.get("description", ""),
          "quantity": ln.get("quantity", 1), "unit_price": ln["unit_price"],
          "frequency": ln.get("frequency", "monthly")} for ln in lines],
    )

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
    print(f"\nMRR: \u00a3{mrr:.2f}")

    print("\n## Clauses")
    clauses = sorted(
        [cl for cl in crm.get("contract_clauses", []) if cl["contract_id"] == contract_id],
        key=lambda c: c.get("seq", 0),
    )
    datalib.print_table(
        [{"seq": cl["seq"], "heading": cl.get("heading", "")} for cl in clauses],
    )


def cmd_renewals():
    rows = datalib.renewals_due()
    if not rows:
        print("No renewals due in the next 90 days.")
        return
    datalib.print_table(rows)


def cmd_find(term):
    if not term:
        die("usage: crm find <term>")
    crm = datalib.load("crm")
    customers = crm.get("customers", [])
    contracts = crm.get("contracts", [])
    t = term.lower()
    rows = []
    for cu in sorted(customers, key=lambda c: c.get("company", "")):
        if t in cu.get("company", "").lower() or t in cu["id"].lower():
            cid = cu["id"]
            ct_count = sum(1 for ct in contracts if ct["customer_id"] == cid)
            rows.append({
                "id": cid,
                "company": cu.get("company", ""),
                "contracts": ct_count,
            })
    datalib.print_table(rows)


# ── Write commands ──────────────────────────────────────────────────────────


def cmd_add_customer(args):
    if len(args) < 2:
        die('usage: crm add <customer-id> "Company Name" [company-number]')
    cust_id = args[0]
    company = args[1]
    co_num = args[2] if len(args) > 2 else ""
    crm = datalib.load("crm")
    customers = crm.get("customers", [])
    customers.append({
        "id": cust_id,
        "company": company,
        "company_number": co_num,
        "address": "",
        "notes": "",
        "created_at": date.today().isoformat(),
    })
    crm["customers"] = customers
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: add customer {company} ({cust_id})")
    print(f"Added customer: {company} ({cust_id})")


def cmd_add_contact(args):
    if len(args) < 3:
        die('usage: crm contact <customer-id> "Name" "email" [role]')
    cust_id, name, email = args[0], args[1], args[2]
    role = args[3] if len(args) > 3 else ""
    contact_id = f"{cust_id}-{name.lower().split()[0]}"
    crm = datalib.load("crm")
    contacts = crm.get("contacts", [])
    contacts.append({
        "id": contact_id,
        "customer_id": cust_id,
        "name": name,
        "email": email,
        "role": role,
    })
    crm["contacts"] = contacts
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: add contact {name} at {cust_id}")
    print(f"Added contact: {name} ({contact_id})")


def cmd_new_contract(args):
    if len(args) < 2:
        die('usage: crm new <customer-id> "Contract Title"')
    cust_id = args[0]
    title = args[1]
    crm = datalib.load("crm")
    cu = next((c for c in crm.get("customers", []) if c["id"] == cust_id), None)
    if not cu:
        die(f"unknown customer: {cust_id}")
    contracts = crm.get("contracts", [])
    seq = sum(1 for ct in contracts if ct["customer_id"] == cust_id) + 1
    contract_id = f"ct-{cust_id}-{seq}"
    contracts.append({
        "id": contract_id,
        "customer_id": cust_id,
        "title": title,
        "status": "draft",
    })
    crm["contracts"] = contracts
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: draft contract {contract_id} — {title}")
    print(f"Created draft contract: {contract_id}")


def cmd_line(args):
    if len(args) < 4:
        die('usage: crm line <contract-id> <seq> "description" <unit-price> [frequency]')
    contract_id, seq_s, desc, price_s = args[0], args[1], args[2], args[3]
    freq = args[4] if len(args) > 4 else "monthly"
    crm = datalib.load("crm")
    ct = next((c for c in crm.get("contracts", []) if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    lines = crm.get("contract_lines", [])
    lines.append({
        "contract_id": contract_id,
        "seq": int(seq_s),
        "description": desc,
        "quantity": 1,
        "unit_price": float(price_s),
        "frequency": freq,
    })
    crm["contract_lines"] = lines
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: line {seq_s} on {contract_id} — {desc}")
    print(f"Added line {seq_s}: {desc} @ \u00a3{price_s}/{freq}")


def cmd_clause(args):
    if len(args) < 4:
        die('usage: crm clause <contract-id> <seq> "Heading" "body text"')
    contract_id, seq_s, heading, body = args[0], args[1], args[2], args[3]
    crm = datalib.load("crm")
    ct = next((c for c in crm.get("contracts", []) if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    clauses = crm.get("contract_clauses", [])
    clauses.append({
        "contract_id": contract_id,
        "seq": int(seq_s),
        "heading": heading,
        "body": body,
    })
    crm["contract_clauses"] = clauses
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: clause {seq_s} on {contract_id} — {heading}")
    print(f"Added clause {seq_s}: {heading}")


def cmd_standard_clauses(contract_id):
    if not contract_id:
        die("usage: crm standard-clauses <contract-id>")
    crm = datalib.load("crm")
    ct = next((c for c in crm.get("contracts", []) if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    clauses = crm.get("contract_clauses", [])
    existing = sum(1 for cl in clauses if cl["contract_id"] == contract_id)
    start_seq = existing + 1
    for i, (heading, body) in enumerate(STANDARD_CLAUSES):
        seq = start_seq + i
        clauses.append({
            "contract_id": contract_id,
            "seq": seq,
            "heading": heading,
            "body": body,
        })
    crm["contract_clauses"] = clauses
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: standard clauses on {contract_id}")
    print(f"Added {len(STANDARD_CLAUSES)} standard clauses (seq {start_seq}\u2013{start_seq + len(STANDARD_CLAUSES) - 1})")


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
    crm = datalib.load("crm")
    contracts = crm.get("contracts", [])
    ct = next((c for c in contracts if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    if col in ("term_months", "notice_period_days"):
        ct[col] = int(value)
    elif col == "auto_renew":
        ct[col] = value.lower() in ("true", "yes", "1")
    else:
        ct[col] = value
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: set {field}={value} on {contract_id}")
    print(f"Set {field} = {value} on {contract_id}")


def cmd_activate(contract_id):
    if not contract_id:
        die("usage: crm activate <contract-id>")
    crm = datalib.load("crm")
    contracts = crm.get("contracts", [])
    ct = next((c for c in contracts if c["id"] == contract_id), None)
    if not ct:
        die(f"unknown contract: {contract_id}")
    ct["status"] = "active"
    datalib.save("crm", crm)
    datalib.git_commit(f"crm: activate {contract_id}")
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
    crm = datalib.load("crm")
    ct = next((c for c in crm.get("contracts", []) if c["id"] == contract_id), None)
    if not ct:
        return None
    cu = next((c for c in crm.get("customers", []) if c["id"] == ct["customer_id"]), None)
    if not cu:
        return None

    c = {
        "id": ct["id"],
        "company": cu.get("company", ""),
        "company_number": cu.get("company_number", ""),
        "address": cu.get("address", ""),
        "title": ct.get("title", ""),
        "status": ct.get("status", "draft"),
        "effective_date": ct.get("effective_date", ""),
        "term_months": ct.get("term_months", ""),
        "auto_renew": ct.get("auto_renew", False),
        "payment_terms": ct.get("payment_terms", ""),
        "currency": ct.get("currency", "GBP"),
        "governing_law": ct.get("governing_law", ""),
        "jurisdiction": ct.get("jurisdiction", ""),
        "notice_period_days": ct.get("notice_period_days", ""),
    }

    lines = sorted(
        [ln for ln in crm.get("contract_lines", []) if ln["contract_id"] == contract_id],
        key=lambda l: l.get("seq", 0),
    )
    clauses = sorted(
        [cl for cl in crm.get("contract_clauses", []) if cl["contract_id"] == contract_id],
        key=lambda cl: cl.get("seq", 0),
    )

    md = []

    # Title
    md.append(f"# {c['title']}\n")
    md.append(f"**Agreement Reference:** {c['id']}\n")

    status_label = c['status'].upper()
    if status_label == "DRAFT":
        md.append("**\u26a0 DRAFT \u2014 NOT YET EXECUTED**\n")

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
    auto = "Yes" if c.get("auto_renew") in (True, "true", "True", "1") else "No"
    md.append(f"| Auto-Renewal | {auto} |")
    md.append(f"| Payment Terms | {c.get('payment_terms') or 'net-30'} |")
    md.append(f"| Currency | {c.get('currency') or 'GBP'} |")
    if c.get("notice_period_days"):
        md.append(f"| Notice Period | {c['notice_period_days']} days |")
    md.append(f"| Governing Law | {c.get('governing_law') or 'England and Wales'} |")
    md.append(f"| Jurisdiction | {c.get('jurisdiction') or 'Courts of England and Wales'} |")
    md.append("")

    # Service Lines
    if lines:
        md.append("## Services and Fees\n")
        md.append("| # | Description | Qty | Unit Price | Frequency |")
        md.append("|---|-------------|-----|------------|-----------|")
        total_annual = 0
        for ln in lines:
            qty = float(ln.get("quantity", 1))
            price = float(ln["unit_price"])
            freq = ln.get("frequency", "monthly")
            md.append(
                f"| {ln['seq']} | {ln.get('description', '')} | {qty:g} "
                f"| \u00a3{price:,.2f} | {freq} |"
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
        md.append(f"**Total annual value: \u00a3{total_annual:,.2f}**\n")

    # Clauses
    if clauses:
        for cl in clauses:
            md.append(f"## {cl['seq']}. {cl.get('heading', '')}\n")
            md.append(f"{cl.get('body', '')}\n")

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
