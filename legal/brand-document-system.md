# Document Brand System — Google Workspace Templates

How to set up Google Docs, Sheets, and Slides so every company document looks like it came from the same company. Do this once, use it forever.

---

## The problem

Without templates, every document looks different. Board minutes in Times New Roman, pitch decks in whatever Google's default is, financial models in Arial. Investors notice. It signals "this person doesn't pay attention to detail" — which is the opposite of what you want.

The fix is 30 minutes of setup. After that, every new document starts from a template that already has the right fonts, colours, headers, and layout.

---

## Formabi document palette

The product brand (indigo/purple on dark) does not work for documents. Documents are printed, projected, and read on white backgrounds. You need a **document adaptation** of the brand — same personality, different medium.

### Document colours

| Use | Colour | Hex | Where |
|-----|--------|-----|-------|
| **Primary** | Indigo | #4f46e5 | Headings, borders, emphasis. Slightly deeper than the product primary (#6366f1) for readability on white. |
| **Secondary** | Purple | #7c3aed | Subheadings, accents, links |
| **Dark text** | Near black | #1e1e2e | Body text. Not pure black — slightly warm, easier on the eyes. Echoes the logo text colour #1e2250. |
| **Muted text** | Grey | #6b7280 | Captions, footnotes, secondary information |
| **Background** | White | #ffffff | Page background. Do not use the dark brand background for documents. |
| **Light accent** | Pale indigo | #eef2ff | Table header backgrounds, callout boxes, highlighted sections |
| **Border** | Light grey | #e5e7eb | Table borders, dividers, section separators |
| **Success** | Green | #059669 | Status indicators, positive metrics |
| **Warning** | Amber | #d97706 | Cautions, items needing attention |
| **Error/urgent** | Red | #dc2626 | Critical items, overdue, negative metrics |

### Document fonts

| Use | Font | Weight | Size |
|-----|------|--------|------|
| **Document title** | Inter | Bold | 24pt |
| **Section heading (H1)** | Inter | Semi-bold | 18pt |
| **Subsection heading (H2)** | Inter | Semi-bold | 14pt |
| **Sub-subsection (H3)** | Inter | Medium | 12pt |
| **Body text** | Inter | Regular | 11pt |
| **Small text / captions** | Inter | Regular | 9pt |
| **Code / technical** | JetBrains Mono or Source Code Pro | Regular | 10pt |
| **Numbers / financial** | Inter | Regular (tabular figures) | 11pt |

**Why Inter**: free, available in Google Fonts (built into Google Docs), excellent readability at all sizes, professional without being generic, has tabular figures for aligned numbers in financial documents. It is the document equivalent of your product's font choices.

**If Inter is not available**: use Google Sans (default in Google Workspace) or Roboto. Both are clean and professional. Avoid: Times New Roman (dated), Calibri (screams Microsoft), Comic Sans (obviously).

---

## Google Docs setup

### Step 1: Create a master template document

Create a Google Doc called `_Formabi Template — Document`. This is your master template. Every new document starts as a copy of this.

**Page setup:**
- Page size: A4
- Margins: 2.5cm top, 2.5cm bottom, 2.5cm left, 2.5cm right
- Line spacing: 1.15 (slightly more than single, easier to read)
- Paragraph spacing: 6pt after each paragraph

**Set up custom styles:**

In Google Docs, go to **Format > Paragraph styles** and configure each heading level:

| Style | Font | Size | Weight | Colour | Spacing |
|-------|------|------|--------|--------|---------|
| Title | Inter | 24pt | Bold | #4f46e5 (indigo) | 24pt after |
| Subtitle | Inter | 14pt | Regular | #6b7280 (muted) | 12pt after |
| Heading 1 | Inter | 18pt | Semi-bold | #4f46e5 (indigo) | 18pt before, 6pt after |
| Heading 2 | Inter | 14pt | Semi-bold | #1e1e2e (dark) | 12pt before, 4pt after |
| Heading 3 | Inter | 12pt | Medium | #1e1e2e (dark) | 10pt before, 4pt after |
| Normal text | Inter | 11pt | Regular | #1e1e2e (dark) | 0pt before, 6pt after |

After configuring each style, click on the style name in the toolbar dropdown and select **"Update [style] to match"** to save it.

Then go to **Format > Paragraph styles > Options > Save as my default styles**. This makes every new document you create use these styles.

**Header:**

Insert a header (Insert > Headers & footers > Header):
- Left-aligned: Formabi logo (small, ~1.5cm height) or just the text "FORMABI" in Inter Bold, 9pt, #4f46e5
- Right-aligned: leave blank (or add document type: "BOARD MINUTES" / "AGREEMENT" / etc.)
- Add a thin line below the header: insert a horizontal line or use a bottom border on the header paragraph (#e5e7eb, 0.5pt)
- Check "Different first page" — the first page can have a larger header or no header, your choice

**Footer:**

- Left-aligned: "Formabi Ltd — Confidential" in Inter, 8pt, #6b7280
- Right-aligned: page number ("Page X of Y") in Inter, 8pt, #6b7280
- Thin line above the footer (#e5e7eb)

**Table style:**

When you insert a table, apply this formatting consistently:
- Header row: background #eef2ff (pale indigo), text Inter Semi-bold 10pt #1e1e2e
- Body rows: background white, text Inter Regular 10pt #1e1e2e
- Alternating rows: background #f9fafb (very light grey) — optional but helps readability
- Borders: #e5e7eb, 0.5pt
- Cell padding: 4pt all sides

### Step 2: Save as template

Once the master document looks right:

1. Go to **docs.google.com/templates**
2. Or: from Google Drive, right-click the template > **"Use as template"** (this option appears in some Workspace editions)
3. Or: simpler — put the template in a shared folder called `_Templates` and always start new documents by making a copy ("File > Make a copy")

**Naming the templates folder:**

```
Formabi/
└── _Templates/
    ├── _Formabi Template — Document.gdoc
    ├── _Formabi Template — Board Minutes.gdoc
    ├── _Formabi Template — Agreement.gdoc
    ├── _Formabi Template — Spreadsheet.gsheet
    └── _Formabi Template — Presentation.gslides
```

The underscore prefix keeps the templates folder sorted to the top of any directory listing.

### Step 3: Create document-type templates

Start with three templates. Make each one as a copy of the master, then customise:

#### Board Minutes template

```
Header: FORMABI LTD — BOARD MINUTES

───────────────────────────────────────

MINUTES OF A MEETING OF THE BOARD OF DIRECTORS

FORMABI LTD

Company Number: [NUMBER]

Date:           [DATE]
Time:           [TIME]
Place:          [LOCATION]
Present:        [NAMES AND ROLES]
In attendance:  [NAMES]

───────────────────────────────────────

1. [AGENDA ITEM]

   [Discussion and resolution text]

   IT WAS RESOLVED that [resolution].

2. [AGENDA ITEM]

   ...

───────────────────────────────────────

There being no further business, the meeting was closed.

Signed as a correct record:

Chair: ____________________     Date: ____________________
```

#### Agreement template

```
Header: FORMABI LTD — [AGREEMENT TYPE]

───────────────────────────────────────

[TITLE OF AGREEMENT]

THIS AGREEMENT is made on [DATE]

BETWEEN:

(1)  FORMABI LTD ... (the "Company")

(2)  [COUNTERPARTY] ... (the "[DEFINED TERM]")

───────────────────────────────────────

BACKGROUND

(A)  [Context]

AGREED TERMS

1.   DEFINITIONS
     ...

2.   [CLAUSE]
     ...

───────────────────────────────────────

SIGNED by [PARTY 1]:

Signature: ____________________
Name:      ____________________
Date:      ____________________

SIGNED by [PARTY 2]:

Signature: ____________________
Name:      ____________________
Date:      ____________________
```

#### Letter template

```
[Formabi logo - top left]

Formabi Ltd
[Registered address]
Company No: [NUMBER]

[Date]

[Recipient name]
[Recipient address]

Dear [Name],

[Subject line in bold]

[Body text]

Yours sincerely,


____________________
Richard Targett
Chief Executive Officer
Formabi Ltd
```

---

## Google Sheets setup

### Template spreadsheet

Create `_Formabi Template — Spreadsheet` with these defaults:

**Font**: Inter, 10pt, #1e1e2e

**Header row (row 1):**
- Background: #eef2ff (pale indigo)
- Font: Inter Semi-bold 10pt, #1e1e2e
- Bottom border: #4f46e5, 2px
- Freeze row 1

**Column A (labels):**
- Font: Inter Medium 10pt
- Right-aligned if numbers follow, left-aligned if text follows

**Number formatting:**
- Currency: £#,##0 or £#,##0.00
- Percentages: 0.0%
- Dates: DD MMM YYYY (e.g. 14 Feb 2026)
- Accounting negatives: (£1,234) in red, not -£1,234

**Conditional formatting presets:**
- Positive numbers: #059669 (green)
- Negative numbers: #dc2626 (red)
- Headers: #eef2ff background
- Total rows: bold, top border #4f46e5

**Tab naming:**
- Use descriptive names: "P&L", "Balance Sheet", "Assumptions", "Cap Table"
- Tab colour: #4f46e5 for primary tabs, #e5e7eb for supporting tabs

**Tab for cap table:**

Pre-format a cap table tab with columns:
| Shareholder | Shares | Class | Price Paid | % | Vesting | Notes |

**Tab for management accounts:**

Pre-format with standard P&L structure:
| | Month 1 | Month 2 | ... | YTD |
| Revenue | | | | |
| Cost of Sales | | | | |
| Gross Profit | | | | |
| Operating Expenses | | | | |
| EBITDA | | | | |

---

## Google Slides setup

### Presentation template

Create `_Formabi Template — Presentation` for pitch decks and internal presentations.

**Slide size:** Widescreen 16:9

**Theme colours (Edit > Theme):**

Set the 10 theme colour slots:
1. #ffffff (white — background)
2. #1e1e2e (near black — body text)
3. #4f46e5 (indigo — primary)
4. #7c3aed (purple — secondary)
5. #eef2ff (pale indigo — light backgrounds)
6. #6b7280 (grey — muted text)
7. #059669 (green — positive)
8. #dc2626 (red — negative)
9. #d97706 (amber — caution)
10. #e5e7eb (border grey)

**Master slides to create:**

| Master slide | Layout | Use |
|-------------|--------|-----|
| **Title** | Logo centred, large title below, strapline, dark indigo background (#1e1e2e) with white text | First slide only |
| **Section** | Large heading centred, pale indigo background (#eef2ff) | Section dividers |
| **Content** | Heading top-left, body text area, logo watermark bottom-right (10% opacity) | Most slides |
| **Two column** | Heading top, two equal columns | Comparisons, before/after |
| **Image + text** | Image left (50%), text right (50%) | Product screenshots, demos |
| **Quote** | Large quotation mark, centred text, attribution below | Customer quotes, testimonials |
| **Data** | Heading top, large chart/table area | Metrics, financials |
| **Closing** | Logo centred, contact details, "Thank you" or CTA | Last slide |

**Slide header:**
- Every slide (except title and closing) has a thin #4f46e5 line across the top (2px)
- Slide number bottom-right in Inter 9pt #6b7280

**Fonts in slides:**
- Slide title: Inter Bold, 32pt, #1e1e2e
- Subtitle: Inter Regular, 20pt, #6b7280
- Body: Inter Regular, 18pt, #1e1e2e
- Bullet points: Inter Regular, 16pt, #1e1e2e
- Captions: Inter Regular, 12pt, #6b7280

---

## Putting it all together

### The templates folder

```
Formabi (Google Drive)/
└── _Templates/
    ├── _Formabi Template — Document.gdoc
    ├── _Formabi Template — Board Minutes.gdoc
    ├── _Formabi Template — Agreement.gdoc
    ├── _Formabi Template — Letter.gdoc
    ├── _Formabi Template — Spreadsheet.gsheet
    └── _Formabi Template — Presentation.gslides
```

### Workflow

1. Need a new document? Go to `_Templates/`
2. Right-click the appropriate template > **Make a copy**
3. Rename the copy and move it to the correct folder
4. Start writing — fonts, colours, headers, and layout are already set

### Rules

- **Never edit the templates directly.** Always make a copy. If you want to improve a template, make the change in the template file and save it — but never use the template file as a working document.
- **Every external-facing document uses a template.** Board minutes, agreements, pitch decks, letters, financial models. No exceptions.
- **Internal notes and scratch docs can be plain.** Not everything needs to be branded. Quick notes, internal checklists, brainstorm docs — use Google's default. Save the branding effort for documents that leave the building.
- **PDF exports for signing.** When a document needs to be signed (agreements, deeds), export as PDF from Google Docs. The formatting carries over cleanly. Sign the PDF, not the Google Doc.

### What this signals to investors

When an investor receives your pitch deck, board minutes, financial model, and legal documents, and they all use the same fonts, the same colours, the same layout conventions — it signals:

- Attention to detail
- Organisational discipline
- A founder who thinks about how things look and feel (relevant for a product company)
- Professionalism beyond what is typical for a pre-seed company

It takes 30 minutes to set up. It pays dividends for years.
