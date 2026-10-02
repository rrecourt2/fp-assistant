# FP Assistant workflow contract

Read this contract and the operating rules once per task. Load only the material needed for the request. Use `--help` for exact tool arguments; run the shipped scripts rather than rewriting them.

## Files and actual access

Each skill carries its required scripts in `scripts/`. They use Python 3.9+ and the standard library, and operate on **local files**. Available authorised Cowork file tools must retrieve the current deal files and return outputs to the deal folder. Verify uploaded files by retrieving them again before claiming persistence. These scripts provide no OneDrive, SharePoint, email or Teams connector.

`register.json` is the single record. `register.xlsx` and `Analysis.md` are generated views; use the JSON revision to identify the current state. Keep one writer per deal. A local revision check is not a remote lock. On a new task retrieve the current Word file and matching record, not merely whichever filename looks newest.

| Need | Command, from the skill folder |
|---|---|
| New register | `python3 scripts/register.py init FOLDER --deal KEY` |
| Current state | `python3 scripts/register.py summary FOLDER --word CURRENT.docx` |
| Selected records | `python3 scripts/register.py show FOLDER R-002 O-005` |
| Apply updates | `python3 scripts/register.py apply FOLDER changes.json` |
| Outstanding work | `python3 scripts/register.py lists FOLDER` |
| Mechanical checks | `python3 scripts/register.py check FOLDER --word CURRENT.docx` |
| Word text and comments | `python3 scripts/fp_docx.py inspect CURRENT.docx --markdown` |
| Word ownership and edit status | `python3 scripts/fp_docx.py inspect CURRENT.docx` |
| Find a renamed draft's original record | `python3 scripts/fp_docx.py find-record CURRENT.docx` |
| Normal revision | `python3 scripts/fp_docx.py build --base CURRENT.docx --content DRAFT.md --out NEW.docx --template TEMPLATE.docx` |
| Complete a genuine first-time draft | Add `--existing` to the build command |
| Start from the configured blank template | Use that template as `--base`, adding `--first --template TEMPLATE.docx` |
| Structure check | `python3 scripts/fp_docx.py check NEW.docx --template TEMPLATE.docx` |
| Financial table | `python3 scripts/fin_table.py SPREAD.xlsx MAPPING.json --json TABLE.json` |
| Runtime smoke test | `python3 scripts/TOOL.py selftest` |

When Python or file access is unavailable, continue supported analysis and drafting as labelled proposals. A failed mutation is not permission to edit Word/Excel another way. Report the actual error and unapplied work. A register update can be saved even if view generation fails: follow the reported recovery step and retry the same operation to regenerate views, without duplicating records.

## Existing drafts and Word rounds

The normal first test improves a **partially completed FP**, with a separate blank template. Use the existing paper as the base, the template for requirements, and the evidence for facts. Review the whole case before selecting revisions. A representative section is optional troubleshooting, never a prerequisite.

For a genuine first-time draft, the user's request to improve it permits `--existing` revisions of unprotected sections in a new copy. Retain useful prose and reasoning; do not start the analysis over unnecessarily. Keep comments, tracked changes, fixed objects and expressly protected sections. `--protect SECTION` can exclude named sections. Output records distinguish rewritten sections from retained officer content.

For a known assistant version, use a normal round and its original `.sections.json` record. After Save As, use `find-record` to look for the source record; no match or competing matches means provenance is unclear. If the original is known and there is no adjacent record, use `--record PATH` with that source record. Do not create a new baseline from the edited file or use `--existing` to evade protection. Ask which source version was used only when it cannot be established; for a genuine first draft, confirm that starting mode once.

Inspect the current Word file before every revision. Later officer text edits and supported formatting edits remain protected. Table grid, margins, indentation, row-property exceptions, automatic widths and proofing/paragraph-mark noise are normalised; explicitly protect a section when preserving edits only to those properties. Supply replacements in `NEW.proposals.md`. Review protected content for factual problems even when it cannot be edited automatically. Use `--fields FIELDS.json` only for specifically requested cover-cell changes; protected or ambiguous cells remain unchanged.

Draft Markdown uses `## section-id`, paragraphs, bullets, tables and `**bold**`. Source tags such as `[S-012 p.45]` are removed from submitted Word and associated IDs recorded by section. Preserve the source-located draft and detailed evidence in Analysis; the sidecar's IDs alone do not retain claim-level locators. `{{keep:N}}` positions a fixed object. Inspection exposes kept content as read-only evidence; do not duplicate it in replacement text.

Save a new Word version each round. Keep its `.sections.json` and any `.proposals.md` together. Record the Word name/hash and affected section links in the register after verifying output. `complete` means the requested supported build was applied and checked; it is not whole-FP readiness. Missing headings, protected proposals, unfilled fields or unsupported structures stay visible. The writer cannot insert entirely absent sections or fill predefined financial tables; report the required work. XML checks do not establish visual layout.

## Register updates and financial figures

An update has `base_revision`, unique `op_id`, `actor`, concise `summary`, `next_step`, and `changes`. Get the revision from `summary`; keep the same operation ID when retrying the same payload. Changes use `{"sheet":"risks","add":{...}}`, `{"sheet":"risks","update":"R-002","set":{...}}` or `{"sheet":"control","set":{...}}`. Schemas and allowed values are in `register.py`; inspect only the needed definitions rather than loading every script. IDs are assigned for sources, risks, mitigants, open items and findings. Analysis uses meaningful keys such as `strategy`, `timeline`, `key-figures`, a risk ID or an annex name.

Field values in `add`/`set` are strings; omit unavailable values instead of supplying JSON null. New questions stay `open`; an undertaking to send evidence is `promised`; a received answer needing assessment is `answered`. Only explicit, supported `closed` disposition finishes the item. Keep answered questions in the internal assessment list instead of asking the client again. New sources start with pending impact assessment. Findings remain unresolved until reviewed and dispositioned; `officer-judgment` means a decision is still pending.

Use an identified spreading export with checked entity, currency/unit and periods. `expect` cells can assert the agreed export layout. Duplicate label/period matches are refused: narrow the export or mapping rather than guess. Formula caches require an explicitly trusted recalculated export and a recorded basis; never turn that option on merely to bypass refusal. Preserve workbook identity/hash, copied cell references and derived formulas. This tool transfers checked figures and calculates bounded ratios; the finance skills supply interpretation.

## Evidence, strategy and readiness

For consequential claims retain source/version, original page/passage/cell, entity, period/event date, units and support status. Keep facts, management explanations, inferences and calculations distinct. Source presence is not proof of a claim or an effective mitigant.

Deal Updates refreshes accessible emails/transcripts through an honest scope and cutoff. Update Sources, Analysis, open items and affected FP passages; keep private/legal material within its authorised audience. FP Lead owns adopted Deal Strategy; Deal Analyst owns substantive synthesis. A newer message can reopen an issue, but does not automatically supersede an executed agreement.

Every new or changed source needs an impact disposition, including previously unlinked adverse evidence. Reopen affected findings/conclusions after material edits. Mechanical register checks do not assess evidence quality, credit judgment, template compliance or visual layout. Record readiness with the officer only after those reviews, identifying the actual decision-maker, current Word hash and register revision. Do not substitute an agent name for an officer decision. Changed evidence or Word requires a new assessment. Submission with exceptions stays distinct from clean readiness.

Use the review protocol for consequential analysis, the complete FP and material revisions. One substantive round plus recheck is the default; a fresh arbiter addresses material disagreement when needed. Separate tasks are independent only if they actually ran. Return the result, changed case, unresolved decisions, actual saved files/checks and next useful action. Communications remain drafts.
