---
marp: true
theme: formabi
paginate: true
---

<!-- _class: lead -->

# Formabi

## Product Overview

The Pluggable AI Workspace — plug in any UI and it becomes Formabi.

---

# What is Formabi?

A **form platform** purpose-built for organizations that have outgrown simple form builders but can't justify custom development.

**Core insight:** Most "complex" forms follow patterns that can be modeled declaratively — conditional visibility, entity references, validation chains.

Formabi gives you the power of a custom solution with the speed of a drag-and-drop builder.

---

# The Form Complexity Spectrum

```
Simple                                                    Complex
|-------|-----------|------------|------------|-----------|
Survey   Contact     Application   Inspection   Regulatory
Form     Form        Form          Report       Filing

         Typeform ------>
         JotForm -------->
                          Formabi -------------------------------->
                                                Custom Dev ------->
```

Formabi covers the **80% of use cases** where existing tools fail but custom dev is overkill.

---

# Key Capabilities

## Display Rules (Conditional Logic)

Show or hide fields based on prior answers — nested to any depth.

- If `equipment_type = "crane"` → show crane inspection fields
- If `crane_age > 10` → require additional safety attestation
- If `safety_attestation = "fail"` → block submission, notify supervisor

**Not just show/hide** — display rules can trigger validation, set defaults, and control navigation.

---

# Key Capabilities

## Entity Relationships

Forms don't exist in isolation — they reference shared organizational data.

- A safety inspection references **equipment entities** from the asset registry
- A crew manifest references **personnel entities** from HR
- A geological survey references **site entities** from the operations database

Formabi models these as **first-class relationships**, not just dropdown lookups.

---

# The Admin Experience

Form plan design is **declarative and visual**:

1. **Create entities** — define the data objects (Equipment, Personnel, Site)
2. **Add attributes** — text, number, date, select, file, entity-reference
3. **Set display rules** — if/then conditions for visibility and validation
4. **Assign workspaces** — who can access which form plans

All changes are **live** — no build step, no deployment. Update a form plan and users see changes immediately.

---

# The User Experience

Form filling is **guided and forgiving**:

- **Auto-save** — every keystroke persisted, never lose work
- **Progress indicators** — know what's done and what's left
- **Validation feedback** — real-time, contextual error messages
- **Collaboration** — multiple users fill the same form simultaneously
- **Offline-ready** — architecture supports eventual consistency

---

# Auditability & Time Travel

Every plan and every fill is built on an **immutable data engine** — nothing is ever deleted, only superseded.

### Ask any question about your data

- **Who** changed it? — every edit tagged with the user who made it
- **What** changed? — diff any two moments to see exactly which fields were added, removed, or modified
- **When** did it change? — full timestamped history, from first draft to final submission

### Roll back with confidence

- **Rewind a fill** — restore a submission to any previous state without losing the audit trail
- **Rewind a plan** — revert a form design to an earlier version; downstream fills stay consistent
- **Tamper-evident** — immutable transaction log, no silent edits

This matters for **compliance** (who approved this?), **disputes** (what was the original answer?), **investigations** (what did the form look like when it was submitted?), and **analytics** (how do answers change over time?).

---

# Multi-Workspace Architecture

Formabi is built for organizations with **multiple teams and contexts**:

- **Workspace isolation** — data and form plans are scoped per workspace
- **Role-based access** — admins, operators, and viewers per workspace
- **Cross-workspace entities** — shared reference data across the org
- **Centralized management** — super-admins oversee all workspaces

---

# Internationalization

Built for global operations from day one:

- **English, Spanish, Arabic, Hebrew** supported
- **Right-to-left (RTL)** layout fully supported
- **Per-workspace language** — each team uses their preferred language
- **Translatable form content** — field labels, help text, validation messages

---

# Integration & API

**API-first architecture** with full OpenAPI specification:

- Programmatic form plan creation
- Bulk data submission
- Webhook notifications on form events
- Export to CSV, JSON, or downstream systems

Auto-generated client libraries from the OpenAPI spec.

---

# Use Case: Regulatory Compliance Audit

1. **Compliance officer** creates an audit form plan:
   - Regulation selection (entity reference)
   - Conditional sections by regulation type
   - Evidence capture with document upload
   - Sign-off with digital signature

2. **Auditor** fills the form during review:
   - Selects regulation → sees relevant compliance criteria
   - Records findings → each with severity and remediation steps
   - Signs off → form locked, full history preserved for time-travel review

3. **Compliance manager** reviews submissions:
   - Dashboard of completed audits
   - Filter by regulation, risk level, date
   - Export for regulatory reporting

---

# Use Case: Clinical Trial Data Collection

1. **Study coordinator** designs the case report form (CRF):
   - Patient demographics
   - Visit schedule with conditional assessments
   - Adverse event reporting
   - 21 CFR Part 11 audit trail — full time-travel history of every change

2. **Site staff** enters data per visit:
   - Only see assessments relevant to this visit type
   - Validation prevents out-of-range values
   - Queries and corrections tracked with reason codes

---

<!-- _class: lead -->

# Formabi

## Complex Forms Made Easy

Ready to see a demo?
