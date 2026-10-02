# FP Assistant

Prepare clear, evidence-grounded financing proposals in an institution's Word template. The assistant connects source review, financial analysis, interviews, diligence and editorial judgment while preserving the officer's decisions and edits.

**Status — 2 October 2026:** design and eight draft skill sources. No installed plugin or functioning register/Word/financial-table application is claimed. This repository is separate from Bankability. Confidential deal documents, real transcripts, private audience notes and institutional templates stay in their approved work environment.

**Downloadable preview 0.2.0:** a Claude-compatible plugin ZIP and individual skill ZIPs are now packaged locally for Cowork import. See [installation and limits](INSTALL.md). The preview includes [checkpoint review and arbitration instructions](docs/adversarial-review.md); it supplies no automatic agent orchestration. Tenant import and operation remain untested.

## Start here

- [Design v3](docs/design-v3.md): proposed workflow, implementation boundaries and acceptance criteria.
- [Meeting evidence and Deal Strategy extension](docs/transcripts-and-strategy.md): eighth skill and continuing diligence/writing strategy.
- [Research assessment](docs/research-assessment.md): recent primary-source precedents and original design review.
- [Skill review](docs/skill-review.md): authoring decisions and honest validation status.
- [Seven-skill handover](docs/handover-v3.md): original baseline handover; use the transcript extension alongside it.

The eight editable sources are under `skills/`. The handover's seven-skill count describes the reviewed baseline; Deal Updates and Guidance is the additional draft extension. There are no mandatory eight-agent runs.

| Skill | Purpose |
|---|---|
| [Deal Analyst](skills/deal-analyst/SKILL.md) | Company, transaction and diligence synthesis. |
| [Annual Report Review](skills/annual-report-review/SKILL.md) | Complete scoped accounts/notes reading and located evidence. |
| [Financial Performance Analysis](skills/financial-performance-analysis/SKILL.md) | Explain earnings, financial movements and cash conversion. |
| [Repayment and Structure](skills/repayment-and-structure/SKILL.md) | Borrower liquidity, debt service, covenants and protections. |
| [FP Lead](skills/fp-lead/SKILL.md) | Select, draft and revise the financing case. |
| [Investment Grill](skills/investment-grill/SKILL.md) | Challenge material evidence and reasoning. |
| [Template and Style Reviewer](skills/fp-template-style-reviewer/SKILL.md) | House style, natural section flow, template and layout. |
| [Deal Updates and Guidance](skills/meeting-evidence-review/SKILL.md) | Refresh relevant emails, transcripts and uncertain guidance; prioritise evidence and strategy updates. |

## Normal FP workflow

Start with the whole deal: core evidence, recent correspondence, company and repayment picture, provisional case, diligence gaps and the full-paper structure. Draft and review the complete FP with that context. The usual observation/risk/mitigant/conclusion reasoning can span paragraphs; sufficient description and evidence take priority over a formula.

Before drafting, material revision and a readiness decision, Deal Updates and Guidance refreshes accessible deal emails and meeting material through a stated cutoff. It records partial coverage and unavailable mail access rather than claiming all latest information was checked. It updates or proposes changes in the existing evidence, open-item and strategy records.

## Setup validation

Verify source access and a save/readback with the real template and tenant model. A representative section is optional early style calibration **after** the broader deal analysis, not a prerequisite to requesting a full FP. Test an officer edit and safe revision, then extend to historical replays and a supervised pilot. Judge material errors/omissions, whole-paper coherence, writing quality and officer repair effort together.

The design names three proposed operational programs; they do not yet exist here. Implement the smallest supported file/record workflow demonstrated by the tenant tests.

## Evaluation status

- All eight skill folders passed structural and local-reference checks at repository creation.
- [Eight baseline synthetic cases](evaluations/scenarios.md) and a [reviewer guide](evaluations/reviewer-guide.md) are prepared; their full behavioral runs remain outstanding.
- [One transcript case](evaluations/transcript-case.md) was executed by a fresh actor and independently graded. It passed within that synthetic scope, with a minor decision-wording issue recorded. See the [evaluation record](evaluations/transcript-review.md).
- [One mixed email/meeting case](evaluations/deal-updates-review.md) was performed by a fresh actor and checked by the author against explicit criteria. Live email access and completeness remain untested.
- Actual institutional house-style matching, tenant file operations, access enforcement and Word preservation remain unverified. A synthetic pass is not production assurance.

## Maintaining the sources

`shared/` is canonical for the common rules. Each skill carries matching copies in `references/` for self-contained packaging. Update those copies and the handover when changing shared instructions. Keep skill activation precise and specialist methods proportionate. Build the local previews with `python3 scripts/package.py`; the ZIPs are written to ignored `dist/`. Packaging does not install a skill.

`evaluations/` contains synthetic material only. Keep local experiments, deal data and generated outputs outside tracked source; the conventional `local/`, `deal-data/` and `outputs/` folders are ignored. An ignore rule is not an access-control boundary. No runtime dependencies, connectors or application programs have been added.
