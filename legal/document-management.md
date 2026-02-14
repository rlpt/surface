# Document Management — Company Documents in Google Drive

How to organise, version, and control access to company documents from day one. Get this right now and you never have to reorganise. Get it wrong and you spend a weekend before your first investment round frantically searching for your certificate of incorporation.

---

## The two systems

Formabi has two homes for documents:

| System | What lives there | Why |
|--------|-----------------|-----|
| **Git** (this repo) | Templates, guides, working drafts, anything that benefits from diff history and collaboration | Version control is built in. Every change is a commit with an author and a reason. LLMs and developers can read it. |
| **Google Drive** | Executed originals, PDFs, scans, third-party documents, anything that needs to be shared with non-technical people (solicitors, accountants, investors) | Solicitors and investors do not use git. They need folders they can click through. |

**The rule**: drafts and templates live in git. Executed, signed, final documents live in Google Drive. Some things live in both — the git version is the editable source, the Drive version is the signed PDF.

---

## Google Drive folder structure

```
Formabi/
│
├── 01 Corporate/
│   ├── Formation/
│   │   ├── Certificate of Incorporation.pdf
│   │   ├── Memorandum of Association.pdf
│   │   ├── Articles of Association (Model Articles).pdf
│   │   └── IN18 Application for Registration.pdf
│   │
│   ├── Articles/
│   │   ├── [CURRENT] Model Articles.pdf
│   │   └── [templates]/
│   │       └── Bespoke Articles v1 (draft).pdf
│   │
│   ├── Registers/
│   │   ├── Register of Members.pdf
│   │   ├── Register of Directors.pdf
│   │   ├── Register of PSCs.pdf
│   │   └── Register of Secretaries.pdf
│   │
│   ├── Companies House Filings/
│   │   ├── 2024/
│   │   │   └── Confirmation Statement CS01 - [DATE].pdf
│   │   ├── 2025/
│   │   └── 2026/
│   │
│   ├── Board Minutes/
│   │   ├── 2024/
│   │   ├── 2025/
│   │   └── 2026/
│   │       └── 001 - Service Agreement & IP Assignment - [DATE].pdf
│   │
│   └── Resolutions/
│       ├── Written Resolutions (Board)/
│       └── Written Resolutions (Shareholder)/
│
├── 02 Legal/
│   ├── IP/
│   │   ├── [CURRENT] IP Assignment Deed - [DATE].pdf
│   │   └── Open Source Schedule.pdf
│   │
│   ├── Employment/
│   │   ├── [CURRENT] Founder Service Agreement - [DATE].pdf
│   │   └── [templates]/
│   │       └── Employment Contract Template.pdf
│   │
│   ├── NDAs/
│   │   ├── [template] Mutual NDA.pdf
│   │   └── Signed/
│   │       └── NDA - [Counterparty Name] - [DATE].pdf
│   │
│   ├── Terms & Policies/
│   │   ├── [CURRENT] Privacy Policy - v1 - [DATE].pdf
│   │   ├── [CURRENT] Terms of Service - v1 - [DATE].pdf
│   │   ├── [CURRENT] Cookie Policy - v1 - [DATE].pdf
│   │   └── Archive/
│   │
│   ├── Data Protection/
│   │   ├── ICO Registration Certificate.pdf
│   │   ├── Record of Processing Activities (ROPA).xlsx
│   │   └── Data Protection Impact Assessments/
│   │
│   └── Insurance/
│       └── (D&O, PI, etc. when obtained)
│
├── 03 Finance/
│   ├── Accounts/
│   │   ├── Management Accounts/
│   │   │   ├── 2024/
│   │   │   │   ├── 2024-06 June.pdf
│   │   │   │   ├── 2024-07 July.pdf
│   │   │   │   └── ...
│   │   │   ├── 2025/
│   │   │   └── 2026/
│   │   │
│   │   └── Annual Accounts/
│   │       └── Year Ending [DATE] - Micro Entity Accounts.pdf
│   │
│   ├── Bank/
│   │   ├── Account Opening Confirmation.pdf
│   │   └── Statements/
│   │       ├── 2024/
│   │       ├── 2025/
│   │       └── 2026/
│   │
│   ├── Tax/
│   │   ├── Corporation Tax/
│   │   │   ├── CT Registration Confirmation.pdf
│   │   │   └── Returns/
│   │   │       └── CT600 - Year Ending [DATE].pdf
│   │   │
│   │   ├── PAYE/
│   │   │   └── (when payroll begins)
│   │   │
│   │   ├── VAT/
│   │   │   └── (when registered)
│   │   │
│   │   └── R&D Tax Relief/
│   │       └── (when claimed)
│   │
│   └── Projections/
│       ├── [CURRENT] Financial Model v1 - [DATE].xlsx
│       └── Archive/
│
├── 04 Fundraising/
│   ├── SEIS-EIS/
│   │   ├── SEIS1 Advance Assurance Application.pdf
│   │   ├── SEIS1 HMRC Response.pdf
│   │   ├── EIS1 Advance Assurance Application.pdf
│   │   ├── EIS1 HMRC Response.pdf
│   │   ├── SEIS2 Compliance Statements/
│   │   ├── EIS2 Compliance Statements/
│   │   ├── SEIS3 Certificates/
│   │   │   └── SEIS3 - [Investor Name] - [DATE].pdf
│   │   └── EIS3 Certificates/
│   │
│   ├── Pitch/
│   │   ├── [CURRENT] Pitch Deck v1 - [DATE].pdf
│   │   ├── [CURRENT] Business Plan v1 - [DATE].pdf
│   │   ├── [CURRENT] Executive Summary v1 - [DATE].pdf
│   │   └── Archive/
│   │
│   ├── Cap Table/
│   │   ├── [CURRENT] Cap Table - [DATE].xlsx
│   │   └── Archive/
│   │
│   └── Rounds/
│       └── (one subfolder per round when they happen)
│           └── Pre-Seed [DATE]/
│               ├── Term Sheet.pdf
│               ├── Subscription Agreement.pdf
│               ├── Shareholders Agreement.pdf
│               ├── Disclosure Letter.pdf
│               ├── Bespoke Articles (adopted).pdf
│               ├── Board Resolution - Allotment.pdf
│               ├── SH01 Return of Allotment.pdf
│               ├── Share Certificates/
│               │   └── Certificate [Investor Name] - [shares].pdf
│               ├── Deed of Adherence/
│               │   └── Deed - [Investor Name].pdf
│               └── Investor Correspondence/
│
├── 05 Product/
│   ├── Screenshots/
│   ├── Architecture/
│   └── Roadmap/
│
├── 06 Team/
│   ├── Richard Targett/
│   │   ├── CV.pdf
│   │   ├── Service Agreement.pdf → (link to 02 Legal/Employment/)
│   │   └── Share Certificate.pdf
│   │
│   └── (future team members get their own folder)
│
├── 07 Contracts/
│   ├── Customers/
│   ├── Suppliers/
│   │   └── [Supplier Name] - [Service] - [DATE].pdf
│   └── Advisors/
│
└── 08 Data Room/
    └── (see below — this is assembled from the other folders)
```

---

## Naming conventions

Consistent naming makes documents findable years later. Follow these rules:

### Files

```
[Type] - [Description] - [Version or Date].ext
```

Examples:
- `IP Assignment Deed - Richard Targett - 2026-02-14.pdf`
- `Service Agreement - Richard Targett - 2026-02-14.pdf`
- `NDA - Acme Ventures - 2026-03-15.pdf`
- `Board Minutes - 001 - IP Assignment & Service Agreement - 2026-02-14.pdf`
- `Financial Model v3 - 2026-06-01.xlsx`
- `Pitch Deck v2 - 2026-06-01.pdf`

### Dates

Always use **YYYY-MM-DD** format. It sorts chronologically in any file system.

- `2026-02-14` not `14/02/2026` or `Feb 14 2026`
- In folder names for monthly documents: `2026-02 February` (so they sort by date but are still readable)

### Versions

For documents that evolve (pitch deck, financial model, business plan):

- `v1`, `v2`, `v3` — major revisions
- Keep old versions in an `Archive/` subfolder within the same directory
- The current version is always in the main folder, prefixed with `[CURRENT]`

For documents that are executed once and never change (signed deeds, certificates):

- Use the date of execution instead of a version number
- These never go into Archive — they are permanent records

### The [CURRENT] prefix

The single most useful convention. Any folder with evolving documents uses `[CURRENT]` to mark the live version:

```
Articles/
├── [CURRENT] Model Articles.pdf           ← this is what's in force right now
└── [templates]/
    └── Bespoke Articles v1 (draft).pdf    ← this is a draft for future use
```

After adopting bespoke articles:

```
Articles/
├── [CURRENT] Bespoke Articles - Adopted 2026-09-15.pdf
└── Archive/
    └── Model Articles (replaced 2026-09-15).pdf
```

One glance tells you what is current. No ambiguity.

---

## Tracking changes over time

### Documents that are executed once

Signed deeds, certificates, formation documents — these never change. They are historical records. File them with their date and leave them.

```
IP/
└── [CURRENT] IP Assignment Deed - 2026-02-14.pdf
```

If a new IP assignment is needed later (e.g. a contractor assigns their IP):

```
IP/
├── [CURRENT] IP Assignment Deed - Richard Targett - 2026-02-14.pdf
└── [CURRENT] IP Assignment Deed - Jane Doe (contractor) - 2026-08-01.pdf
```

Both are current. Both are permanent. Neither replaces the other.

### Documents that are replaced

Articles of association, service agreements, policies — these get superseded. The old version moves to Archive with a note of when and why it was replaced.

```
Articles/
├── [CURRENT] Bespoke Articles - Adopted 2026-09-15.pdf
└── Archive/
    └── Model Articles (superseded 2026-09-15 - replaced on Pre-Seed round).pdf
```

```
Employment/
├── [CURRENT] Service Agreement - Richard Targett - Amended 2026-09-15.pdf
└── Archive/
    └── Service Agreement - Richard Targett - Original 2026-02-14 (superseded 2026-09-15).pdf
```

The archive tells the story: what was in force, when it changed, why. An investor's solicitor doing due diligence can trace the full history.

### Documents that evolve continuously

Financial model, pitch deck, cap table — these change frequently. Use version numbers and archive aggressively.

```
Cap Table/
├── [CURRENT] Cap Table v4 - 2026-09-15.xlsx
└── Archive/
    ├── Cap Table v1 - 2026-02-14.xlsx
    ├── Cap Table v2 - 2026-06-01.xlsx
    └── Cap Table v3 - 2026-08-20.xlsx
```

**Keep every version.** Investors sometimes ask "what did the cap table look like before the option pool was created?" You want to be able to answer immediately.

### Monthly documents

Management accounts, bank statements — these accumulate. Organise by year and month.

```
Management Accounts/
├── 2026/
│   ├── 2026-01 January.pdf
│   ├── 2026-02 February.pdf
│   ├── 2026-03 March.pdf
│   └── ...
└── 2025/
    └── ...
```

The `YYYY-MM Month` format sorts correctly and is readable.

---

## Access control

Google Drive's sharing model maps well to a startup's needs.

### Pre-investment (just you)

Everything is in your personal Google Drive or a Formabi shared drive. You have full access. Nobody else needs access yet.

**Recommendation**: create a Google Workspace account for Formabi (formabi.com domain) even if it is just you. Cost is ~£5/month. Benefits:

- Documents are owned by the company, not your personal account
- If you add team members later, permissions are clean
- Looks professional to investors (richard@formabi.com not richard.targett@gmail.com)
- If you ever leave or are removed, the company retains access to its own documents

### Post-investment

| Folder | Who gets access | Access level |
|--------|----------------|-------------|
| 01 Corporate | Directors, solicitor, accountant | View (solicitor gets edit on their documents) |
| 02 Legal | Directors, solicitor | View |
| 03 Finance | Directors, accountant | View (accountant gets edit on accounts) |
| 04 Fundraising | Directors | Edit |
| 04 Fundraising/SEIS-EIS | Directors, accountant | Edit |
| 04 Fundraising/Rounds | Directors, solicitor, investor (their round only) | View |
| 05 Product | Directors, team leads | View |
| 06 Team | Directors, HR (when you have one) | View |
| 07 Contracts | Directors | View |
| 08 Data Room | Read-only link for investors during due diligence | View (time-limited) |

**Never give edit access to the whole drive.** Share specific folders with specific people at the minimum access level they need.

### The data room

The data room (folder 08) is not a separate collection of documents. It is a curated view assembled from the other folders. Two approaches:

**Option A — Shortcuts (recommended for Google Drive)**

Create shortcuts in `08 Data Room/` that point to documents in their canonical locations. The document lives in one place (e.g. `02 Legal/IP/IP Assignment Deed.pdf`) and the data room contains a shortcut to it. When the original is updated, the data room automatically reflects the change.

```
08 Data Room/
├── 1 Corporate/
│   ├── → Certificate of Incorporation.pdf (shortcut)
│   ├── → Articles of Association.pdf (shortcut)
│   ├── → Register of Members.pdf (shortcut)
│   └── ...
├── 2 Financial/
│   ├── → Financial Model.xlsx (shortcut)
│   ├── → Management Accounts/ (shortcut to folder)
│   └── ...
└── ...
```

**Option B — Copies (for external sharing)**

When you share the data room with an investor, create a separate copy of the folder with copies of documents (not shortcuts, since shortcuts do not work across Google accounts). This is more work but gives you control — you choose exactly what the investor sees and the shared folder is a snapshot that does not update.

**Best practice**: use shortcuts internally, then when an investor requests data room access, create a copy of the folder structure with actual files and share that. Revoke access after the round closes.

---

## What lives in git vs Google Drive

| Document | Git (this repo) | Google Drive |
|----------|-----------------|--------------|
| Article templates and guides | `legal/articles-of-association.md` | — |
| Signed articles (PDF) | — | `01 Corporate/Articles/` |
| IP Assignment template | `legal/ip-assignment.md` | — |
| Signed IP Assignment (PDF) | — | `02 Legal/IP/` |
| Service agreement template | `legal/founder-service-agreement.md` | — |
| Signed service agreement (PDF) | — | `02 Legal/Employment/` |
| Board minute templates | `legal/board-minutes/` | — |
| Signed board minutes (PDF) | — | `01 Corporate/Board Minutes/` |
| SEIS/EIS guide | `legal/seis-eis-guide.md` | — |
| SEIS/EIS certificates (PDF) | — | `04 Fundraising/SEIS-EIS/` |
| Investor readiness checklist | `legal/investor-readiness.md` | — |
| Financial model (working spreadsheet) | — | `03 Finance/Projections/` |
| Cap table (working spreadsheet) | — | `04 Fundraising/Cap Table/` |
| Pitch deck | — | `04 Fundraising/Pitch/` |
| Business plan | — | `04 Fundraising/Pitch/` |

**The principle**: markdown templates and guides are code — they belong in git where they benefit from version control, diff history, and LLM access. Executed legal documents, financial spreadsheets, and PDFs are business records — they belong in Google Drive where non-technical people can access them.

---

## The execution workflow

When you execute a document (e.g. the IP Assignment Deed):

1. **Draft** in git (you already have the template in `legal/ip-assignment.md`)
2. **Export** to PDF or Word for review (if sending to a solicitor)
3. **Print**, sign, have witnessed (for deeds) or just sign (for agreements)
4. **Scan** the signed document to PDF
5. **Upload** the signed PDF to the correct Google Drive folder
6. **Name** it following the naming convention: `IP Assignment Deed - Richard Targett - 2026-02-14.pdf`
7. **Update** the git template if any changes were made during review (so the template stays current for future use)

For documents that do not require wet signatures (board minutes, written resolutions), sign digitally and save the PDF directly.

---

## Google Drive settings to configure now

1. **Create a shared drive** called "Formabi" (requires Google Workspace). Shared drives are owned by the organisation, not an individual. If you leave, the drive stays.

2. **Turn on version history** (on by default in Google Drive). Every edit to a Google Doc/Sheet is tracked. For uploaded PDFs, each upload of a new version creates a version history entry.

3. **Set default access to "Restricted"**. New files should only be accessible to you until you explicitly share them.

4. **Organise folders first, then add documents.** Create the full folder structure from the tree above before you start uploading. Moving files later breaks shared links.

5. **Use Google Docs/Sheets for working documents** (financial model, cap table, ROPA). Use PDF only for executed/final documents. Google's native formats have better version history, commenting, and collaboration.

---

## Minimum viable setup (do today)

You do not need the full structure on day one. Start with this:

```
Formabi/
├── 01 Corporate/
│   ├── Formation/
│   │   └── Certificate of Incorporation.pdf
│   ├── Board Minutes/
│   │   └── 2026/
│   └── Registers/
│
├── 02 Legal/
│   ├── IP/
│   ├── Employment/
│   └── Data Protection/
│
├── 03 Finance/
│   ├── Bank/
│   │   └── Statements/
│   └── Accounts/
│       └── Management Accounts/
│
└── 04 Fundraising/
    ├── SEIS-EIS/
    ├── Cap Table/
    └── Pitch/
```

Create these folders now. Upload your certificate of incorporation. As you execute the IP Assignment Deed and Service Agreement this week, scan and upload them. The structure grows organically from there.

---

## Common mistakes

1. **Dumping everything in one folder.** Three years later you have 200 files and cannot find anything. The folder structure is the index.

2. **Not scanning signed documents.** The paper original matters, but if your house floods, the paper is gone. Scan everything to Drive the same day you sign it. The scan is the backup.

3. **Using personal accounts.** If documents live in your personal Google account and you lose access to it, the company loses its records. Use a company Google Workspace account.

4. **Not archiving superseded versions.** When articles change, the old version disappears into a renamed file or gets deleted. Always move the old version to Archive with a note of when and why it was replaced. The history is valuable.

5. **Giving blanket edit access.** Your accountant needs to edit the annual accounts, not your entire finance folder. Share at the most specific level possible.

6. **Forgetting to revoke data room access.** After a fundraise, revoke the investor's access to the data room folder. They have their own copies of the documents they signed. They do not need ongoing access to your full due diligence pack.

7. **Not keeping the git templates in sync.** If a solicitor modifies your articles template during a funding round, update the git version too. The git repo should always reflect the latest template, even if the signed version lives in Drive.

8. **Storing secrets in Google Drive.** Passwords, API keys, encryption keys — these do not belong in Drive. Use a password manager (1Password, Bitwarden) for credentials and agenix for infrastructure secrets.
