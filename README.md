# FP Assistant

Prepare clear, evidence-grounded financing proposals in an institution's Word template. The assistant connects source review, financial analysis, interviews, diligence and editorial judgment while preserving the officer's decisions and edits.

**Status — 2 October 2026:** design and eight draft skill sources. No installed plugin or functioning register/Word/financial-table application is claimed. This repository is separate from Bankability. Confidential deal documents, real transcripts, private audience notes and institutional templates stay in their approved work environment.

## Start here

- [Design v3](docs/design-v3.md): proposed workflow, implementation boundaries and acceptance criteria.
- [Meeting evidence and Deal Strategy extension](docs/transcripts-and-strategy.md): eighth skill and continuing diligence/writing strategy.
- [Research assessment](docs/research-assessment.md): recent primary-source precedents and original design review.
- [Skill review](docs/skill-review.md): authoring decisions and honest validation status.
- [Seven-skill handover](docs/handover-v3.md): original baseline handover; use the transcript extension alongside it.

The eight editable sources are under `skills/`. The handover's seven-skill count describes the reviewed baseline; Meeting Evidence Review is the additional draft extension. There are no mandatory eight-agent runs.

| Skill | Purpose |
|---|---|
| [Deal Analyst](skills/deal-analyst/SKILL.md) | Company, transaction and diligence synthesis. |
| [Annual Report Review](skills/annual-report-review/SKILL.md) | Complete scoped accounts/notes reading and located evidence. |
| [Financial Performance Analysis](skills/financial-performance-analysis/SKILL.md) | Explain earnings, financial movements and cash conversion. |
| [Repayment and Structure](skills/repayment-and-structure/SKILL.md) | Borrower liquidity, debt service, covenants and protections. |
| [FP Lead](skills/fp-lead/SKILL.md) | Select, draft and revise the financing case. |
| [Investment Grill](skills/investment-grill/SKILL.md) | Challenge material evidence and reasoning. |
| [Template and Style Reviewer](skills/fp-template-style-reviewer/SKILL.md) | House style, natural section flow, template and layout. |
| [Meeting Evidence Review](skills/meeting-evidence-review/SKILL.md) | Turn transcripts into checked evidence, questions and proposed strategy updates. |

## First milestone

Prove one representative FP section in the approved work environment before expanding the implementation:

1. Verify source access and a save/readback using the real Word template and chosen tenant model.
2. Use the relevant annual accounts, approved spread and a small set of good FP examples to prepare one financial section and its financing conclusion. Include a transcript where useful.
3. Challenge the evidence, review the section's natural logic and house style, and have the officer assess the result. The usual observation/risk/mitigant/conclusion reasoning can span paragraphs; sufficient description and evidence take priority over a formula.
4. Exercise an officer edit and safe revision. Record gaps, factual errors, material omissions, writing quality and repair time.
5. Implement only the register, financial-transfer and Word operations needed for that working slice. Expand to historical replays and a supervised pilot after the slice passes.

The current design names three proposed programs; those programs do not yet exist here. Start from observed capability and failure, not an assumed platform interface.

## Evaluation status

- All eight skill folders passed structural and local-reference checks at repository creation.
- [Eight baseline synthetic cases](evaluations/scenarios.md) and a [reviewer guide](evaluations/reviewer-guide.md) are prepared; their full behavioral runs remain outstanding.
- [One transcript case](evaluations/transcript-case.md) was executed by a fresh actor and independently graded. It passed within that synthetic scope, with a minor decision-wording issue recorded. See the [evaluation record](evaluations/transcript-review.md).
- Actual institutional house-style matching, tenant file operations, access enforcement and Word preservation remain unverified. A synthetic pass is not production assurance.

## Maintaining the sources

`shared/` is canonical for the common rules. Each skill carries matching copies in `references/` for self-contained packaging. Update those copies and the handover when changing shared instructions. Keep skill activation precise and specialist methods proportionate. Installation and platform packaging are later tasks; reading a skill is not installation.

`evaluations/` contains synthetic material only. Keep local experiments, deal data and generated outputs outside tracked source; the conventional `local/`, `deal-data/` and `outputs/` folders are ignored. An ignore rule is not an access-control boundary. No runtime dependencies or deployment configuration have been added yet.
