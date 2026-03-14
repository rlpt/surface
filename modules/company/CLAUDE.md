# Company Module — LLM Context

Company details register stored in `data/company.yaml`. Uses `datalib` for loading, saving, and schema validation.

## Data keys in company.yaml

- `company` — single dict (not a list) with company details:
  - `name` — registered company name
  - `company_number` — Companies House number
  - `jurisdiction` — england-wales, scotland, or northern-ireland
  - `company_type` — private-limited, public-limited, llp, unlimited
  - `incorporation_date` — date of incorporation
  - `registered_address` — nested dict: line_1, line_2, city, postcode, country
  - `sic_codes` — list of SIC code strings
  - `accounting_reference_date` — MM-DD format
  - `articles` — articles of association type

## Commands

Read:
- `company show` — display all company details
- `company check` — validate company data

Write:
- `company set <field> <value>` — update a top-level field
- `company set-address <line1> <city> <postcode> [country] [line2]` — update registered address
- `company add-sic <code>` — add a SIC code
- `company remove-sic <code>` — remove a SIC code

Output:
- `company pdf summary` — generate company summary PDF
