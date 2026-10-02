# FP Assistant 0.3.0 — install and first workflow

The ZIP contains eight skills and their local Python tools. Local checks and real-Word synthetic fixtures do not establish Cowork tenant operation. Start with a test folder in the approved work environment; keep confidential files there.

## Install the preview

Build with `python3 scripts/package.py`, then copy `dist/fp-assistant-0.3.0.zip` to the work laptop. In Copilot Cowork use **Customize → Plugins → Upload plugin**, initially **Only you**. Confirm these skills appear: fp-lead, deal-analyst, deal-updates, annual-report-review, financial-performance-analysis, repayment-and-structure, investment-grill, fp-template-style-reviewer.

If only individual skill upload is available, extract `fp-assistant-individual-skills-0.3.0.zip` and upload each inner ZIP. Check existing installations first; avoid numbered duplicates. The former `meeting-evidence-review` is now `deal-updates`; retire the older copy when replacing it. Tenant feature availability and policy determine the supported upload route. [Microsoft customization guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-customize).

Ask fp-lead to run the three packaged self-tests (`register.py`, `fp_docx.py`, `fin_table.py`) and return their actual output. They need Python 3.9+. If scripts cannot run, use labelled analysis/proposals and record the limitation; do not claim Word or register updates.

## First end-to-end test: improve a partially filled FP

Use a copy of a historical draft at the point where it was partially complete, plus the **separate blank template**, original evidence, spreading export and approved style examples. Keep the eventual approved FP as a comparison for the officer, not as hidden answer material for the drafting agent. If no historical partial draft exists, make a deliberate partial test copy and label that setup.

Create a OneDrive test folder containing those inputs and a place for `FP assistant` outputs. Ask:

> Improve and complete this partially filled FP as a whole. The existing draft is the base; the separate template defines required structure and content. Use the evidence to check and improve existing prose and fill gaps. Preserve protected content and save a new Word version with its record and any unapplied proposals. Identify material open questions and missing sections the writer cannot add. Do not use blank-template first-build mode for this draft.

1. Confirm the host can retrieve the input bytes, run the tools, return the new Word file and accompanying record/views, and retrieve the saved outputs again. A visible download alone does not prove they reached the deal folder.
2. Open the new FP in Word. Check that it opens without repair and inspect layout, tables, fields and protected content. Compare against the original, which must remain unchanged. Confirm preserved tables are visible to the review agent.
3. Judge the **whole paper**: business description, relevant detail, explained financial movements, cash/repayment linkage, cross-section consistency, material risks and natural house style. Record material corrections and your editing time. A sample section is optional troubleshooting.
4. Edit wording in one section and add a comment in another. If relevant to normal use, add a tracked change or table-formatting change. Add a later email/transcript that changes an assumption, leaving one question unresolved.
5. In a **fresh task**, retrieve the latest files and continue. First revise an unrelated section, then request changes to your edited sections. Your edits must survive both rounds; protected replacements belong in proposals. Ordinary untouched sections should remain updatable.
6. Check the register: the new information has an impact assessment, changes reach Analysis and the appropriate FP passages/proposals, and promised/answered-but-unassessed questions remain visible. Mechanical checks must not claim final investment readiness.
7. Exercise Save As once if that is your normal workflow. The assistant must recover the original source record; an absent record must not automatically trigger a fresh import. If provenance is unclear, establish it before mutation.

Record actual results in the repository's `evaluations/results.md`, with no confidential details. On failure keep the last usable version, retain the exact error and retry only after the affected correction. If remote saving is unavailable, explicitly transfer the verified output files as a bundle and label the handoff manual.

The scripts preserve predefined financial tables but do not populate them, and cannot insert entirely missing headings. If the real template requires those operations, report the gap and supply proposed content; do not call the FP complete. Test SharePoint separately when that is the intended location; it is not required for a OneDrive-only pilot.

## Scope and next validation

- Run the critical finance, report-reading, style and routing cases on the intended Cowork model, plus the mixed correspondence case. See the repository's `evaluations/README.md`.
- Live email/transcript access is separate from interpretation of supplied exports. Test a bounded received/sent thread and attachment if those tools are available; record coverage honestly when they are not.
- A fresh critic/arbiter is a separate actual task where supported. Skills do not launch independent agents on their own.
- No connector, scheduler, hosted service, automatic sending or tenant installation is included in the package.
