# FP Assistant — current design

Version 0.3.0. Local implementation; work-tenant acceptance and full-FP evaluation remain outstanding. Maintained scripts and this design describe current behaviour. Superseded designs and local implementation notes are not part of the distributed source.

## Purpose and writing

Help an investment officer improve and complete an FP that explains the company, its recent performance and the financing decision. The officer retains the recommendation, material risk placement, conditions and submission decisions.

Use the existing draft as the base, the separate template for requirements, original evidence for claims, and approved examples for style. Preserve useful writing and fill supported gaps. The usual observation → material risk → mitigants → residual exposure/conclusion reasoning can span paragraphs; descriptive sections should follow their topic naturally. Do not manufacture risks or conclude acceptability without support. Explain material financial movements, their drivers, cash conversion and implications for repayment.

Clarity draws selectively on ASD-STE100: concrete wording, consistent terms and readable reasoning. Evidence meaning and mandatory wording take priority; approved examples determine the institution's voice. FP Lead drafts within that voice and the style reviewer checks clarity, preserved meaning and whole-section flow. This adaptation has no dictionary restriction, sentence-length threshold, compliance score or additional skill. The existing preflight notes hold the house-style profile. [ASD's official overview](https://www.asd-ste100.org/about_STE.html) describes the full standard, including its controlled vocabulary and provision for specialist terms; this workflow does not claim compliance with it.

Eight skills divide company synthesis, annual-report reading, financial performance, repayment/structure, correspondence intake, drafting, substantive challenge and presentation. FP Lead owns the paper and adopted Deal Strategy. Deal Analyst maintains substantive synthesis. Deal Updates proposes changes from emails, interviews and comments, distinguishing statements, suggestions, promises and actual decisions. Specialist work is invoked only where useful.

## Small operational core

Three Python 3.9+ standard-library tools run on local files. No hosted service, scheduling, connector or automatic agent orchestration is provided. The host must demonstrate authorised retrieval, execution, saving and fresh-task retrieval before the workflow can be called operational.

| File | Role |
|---|---|
| `register.json` | Canonical control, sources, risks, mitigants, open items, findings, narrative analysis and FP mapping |
| `register.xlsx`, `Analysis.md` | Generated views of the register, carrying its revision |
| `DEAL-FP-vNN.docx` | A new editable Word handoff each round |
| `DEAL-FP-vNN.sections.json` | Original section baselines and ownership for that output |
| `DEAL-FP-vNN.proposals.md` | Proposed changes not safely applied |
| Source-located draft and financial-table JSON | Claim locators, input cells, calculations and unsubmitted working support |

One task writes per deal. Revision checks reject stale local changes; they are not remote locking. Preserve inputs and versioned Word outputs. JSON commits are atomic; a failed view update is reported as such and retry regenerates views from the current master. A view is not a second editable record.

The register applies defaults and validates lifecycle values, links and required decision/evidence fields. Questions remain open through promised/answered states until explicit closure. New source impacts start pending. A source citation verifies neither the truth of its assertion nor a mitigant's adequacy; the analyst must assess both.

The financial tool uses an identified, checked export, with entity/unit/period expectations and retained workbook/cell provenance. Ambiguous labels/periods are refused. Formula caches require a trusted recalculation basis. It performs four bounded operations, not forecasting or general spreadsheet calculation.

## Word starting modes and protection

- **Existing draft:** explicit authority to improve a genuine first-time, partially completed FP permits rewriting requested unprotected sections in a new copy. Comments, tracked changes, fixed objects and specified protected sections stay intact. Retained imported content does not become assistant-owned.
- **First build:** only from the configured blank template, supplied separately and matching the base. It cannot be used to reset protection on a draft.
- **Normal revision:** use the current Word file with the record from its actual source version. Only eligible, untouched assistant-owned sections can be replaced. Text edits and supported formatting edits also protect a section.

Save As copies require their original record. `find-record` proposes a source only when section matches identify a unique candidate; missing or ambiguous records require establishing provenance. Do not infer a first draft merely from absent metadata. Explicit cover-field changes are allowed only in unprotected identified cover cells.

Before writing, validate untouched content and fixed objects. Canonical comparison ignores a narrow set of tested Word save differences. Functional bookmarks remain protected; incidental copy markers should not duplicate paragraphs. Both original and assistant-generated table Word-save fixtures are regression tests, not proof for every Word version or template.

Edit detection is not an exact visual comparison. It ignores table grid, row-property exceptions, indentation, cell margins and automatic widths that Word rewrites, as well as proofing/language and paragraph-mark noise. A deliberate change only to these properties may not protect an assistant-owned section. Use explicit section protection for such layout work; shading, table style and table-look changes are covered by regressions. Unsupported structures and unverified layout remain part of the pilot check.

Inspection exposes kept tables and protected content for review. Entirely absent headings and unsupported structures are reported, not silently filled. The writer does not insert new sections, fill predefined financial tables, or safely merge arbitrary tracked structures. A `complete` build means its supported requested operations completed; mandatory FP omissions still block submission readiness. Visual inspection of the actual final Word output remains necessary.

## Evidence, reviews and readiness

Read Tier A documents fully: latest accounts and notes, latest interim accounts, current proposal/terms, relevant prior FP/Credit decision and other decision-critical evidence. Older supporting material is read for relevant passages/changes; other material is indexed/searched. A whole annual-report request means the whole report. Keep a coverage record; unreadable is never equivalent to not disclosed.

Material claims retain source/version, locator, entity, period/event date, units and support status. Keep conflicting and adverse evidence. Correspondence refreshes state what channels, scope and cutoff were actually checked; promised evidence is not received evidence, and a newer message does not automatically amend a contract. Internal/legal information remains within its authorised audience. The current strategy lives in Analysis: what must be established, supporting/contrary evidence, next questions and consequences for the FP.

Challenge the principal case, consequential analysis, full draft and material revisions. Use a fresh reviewer where available. One round plus recheck is the default; a fresh arbiter handles unresolved material disagreement or requested consequential adjudication. Self-review is labelled as such. Template/style/layout review remains distinct from investment judgment.

The register reports mechanical checks. FP Lead records the officer's readiness decision only for the identified Word content and evidence revision after required analytical, template, style and visual checks. New evidence or document changes invalidate the earlier assessment; outstanding blockers, pending impacts and rechecks remain visible. Explicit submission with exceptions is recorded separately. Nothing sends communications automatically.

## Acceptance

Use [INSTALL.md](../INSTALL.md) for the first task: improve a partially completed FP, retain the separate template, save/retrieve the package, then continue after an officer edit and new email/transcript in a fresh task. Evaluate the entire paper's factual accuracy, omissions, explanations, coherent structure, house style and correction time. A short section is optional troubleshooting.

Run critical skill cases on the intended Cowork model; test another model before using it. Rerun affected cases after changes. Local unit tests and synthetic Word fixtures do not establish tenant persistence, live-mail coverage or writing quality. OneDrive is the first target; test SharePoint only when needed. Broader historical replays follow before wider use.
