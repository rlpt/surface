// Formabi letterhead template — used by datalib.generate_branded_pdf()
// All PDF output (shares, board, officers, compliance) uses this template.

#let brand-primary = rgb("#6366f1")
#let brand-accent = rgb("#a78bfa")
#let brand-dark = rgb("#1e2250")

#let company-name = "Formabi Ltd"
#let company-address = "66 Paul Street, London, EC2A 4NA"
#let company-strapline = "Complex Forms Made Easy"

#let letterhead(
  logo-path: none,
  body,
) = {
  set page(
    paper: "a4",
    margin: (top: 2.4cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
    header: context {
      if counter(page).get().first() == 1 {
        box(height: 1.8cm, {
          grid(
            columns: (auto, 1fr),
            align: (left + horizon, right + horizon),
            gutter: 1em,
            {
              if logo-path != none {
                image(logo-path, height: 1.5cm)
              } else {
                text(size: 18pt, weight: "bold", fill: brand-primary)[Formabi]
              }
            },
            {
              set text(size: 7.5pt, fill: luma(120))
              [*#company-name* #h(0.3em) | #h(0.3em) #company-address #h(0.3em) | #h(0.3em) formabi.com]
            },
          )
        })
        v(-10pt)
        line(length: 100%, stroke: 0.4pt + brand-primary)
      } else {
        grid(
          columns: (1fr, auto),
          align: (left + horizon, right + horizon),
          text(size: 9pt, weight: "bold", fill: brand-primary)[Formabi],
          text(size: 8pt, fill: luma(150))[Page #counter(page).display()],
        )
        line(length: 100%, stroke: 0.3pt + luma(200))
      }
    },
    footer: context {
      line(length: 100%, stroke: 0.3pt + luma(200))
      v(4pt)
      grid(
        columns: (1fr, auto),
        align: (left + horizon, right + horizon),
        text(size: 7pt, fill: luma(150))[#company-name — #company-strapline],
        text(size: 7pt, fill: luma(150))[Page #counter(page).display() of #counter(page).final().first()],
      )
    },
  )

  // Typography
  set text(font: "Helvetica", size: 10pt, fill: luma(30))
  set par(justify: true, leading: 0.65em)

  // Headings
  set heading(numbering: none)
  show heading.where(level: 1): it => {
    v(0.5em)
    text(size: 16pt, weight: "bold", fill: brand-dark)[#it.body]
    v(0.3em)
  }
  show heading.where(level: 2): it => {
    v(0.4em)
    text(size: 12pt, weight: "bold", fill: brand-primary)[#it.body]
    v(0.2em)
  }
  show heading.where(level: 3): it => {
    v(0.3em)
    text(size: 10pt, weight: "bold", fill: brand-dark)[#it.body]
    v(0.15em)
  }

  // Tables
  set table(stroke: 0.5pt + luma(200), inset: 5pt)
  show table: set text(size: 8pt)
  show table.cell: it => {
    // Allow optional line-breaking after hyphens in table cells (dates, IDs, etc.)
    show regex("-"): m => [-\u{200B}]
    it
  }
  show table.cell.where(y: 0): set text(weight: "bold", fill: brand-dark, size: 8pt)

  body
}
