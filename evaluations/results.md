# Validation results

## Historical skill runs (0.2.0)

| Date | Run | Result and limits |
|---|---|---|
| 2026-10-01 | Synthetic transcript case, fresh actor and independent grader | Passed in scope; a minor decision-wording issue was recorded. Exact model was not captured. |
| 2026-10-02 | Synthetic mixed email/meeting case, fresh actor and author grading | Passed in scope. No live mailbox or independent grader. Exact model was not captured. |

One-off actor and grader transcripts are retained locally rather than tracked in the public source. These historical summaries are not a current model qualification.

## 0.3.0 implementation

Verified locally on 2 October 2026:

| Check | Result and scope |
|---|---|
| `uv run --no-sync pytest -q -W error` | 165 passed on Python 3.12.12: 78 Word, 52 register, 24 financial table, 10 packaging, 1 integration |
| Scripts extracted from the built plugin, outside the repository | All 14 packaged script copies passed their self-tests on Python 3.9.6 without third-party libraries |
| Packaging and manifest | Both ZIPs built; eight skill packages passed `package.py --check`; `claude plugin validate .` passed (not Cowork import) |
| Reproducible packaging | Same sources produced identical ZIP bytes with fixed archive timestamps |
| Links and diff | After documentation cleanup, 42 tracked Markdown files checked with no missing or untracked relative targets; `git diff --check` clean |
| Synthetic workflow | Existing partial draft + separate template → located financial table and Word output → register/readiness record → new email and officer edit → protected revision with proposals; original input preserved |

The synthetic Word fixtures were saved in Microsoft Word by the officer: one ordinary draft and one including an assistant-generated financial table. Both comparisons identify only the edited Recommendation section, leaving the other sections updatable. Regression checks cover later-round protection, bookmarks, page breaks and supported formatting edits. The second pair was inspected for synthetic content and external relationships before inclusion. These fixtures do not establish compatibility with the institution's real template or visual layout of a new FP.

Two targeted agents reviewed the Word amendments and financial/package integration. The primary implementer reviewed register and cross-tool behaviour. Review fixes include whitespace/null evidence guards, unresolved officer-judgment blockers, risk analysis hiding linked items, and routing received answers to internal assessment rather than a repeated client request. No tenant or model-writing result is inferred from these checks.

Known local limits: predefined financial tables are preserved rather than filled; wholly missing headings cannot be inserted; some Word-rewritten layout properties are deliberately ignored for edit detection. Use explicit section protection for deliberate changes only to those properties, as described in the [design](../docs/design.md). The entire FP still needs factual, substantive, style and visual review.

## Outstanding acceptance

| Check | Status |
|---|---|
| Cowork plugin import and packaged script execution | Not run in the work tenant |
| OneDrive save, independent readback and fresh-task recovery | Not run in the work tenant |
| Improve a partially filled FP with the separate actual template | Not run; this is the first full workflow test |
| Whole-paper writing quality and officer correction time | Not measured |
| Subsequent email/transcript update and preserved officer edits across tasks | Not run in the work tenant |
| Live received/sent mail, threads, attachments and coverage cutoff | Not run |
| Critical skill scenarios on the intended Cowork model | Outstanding |
| SharePoint parity | Deferred until needed |

Record actual versions, scope, results and limitations. Keep deal data, private notes and internal templates outside this repository.
