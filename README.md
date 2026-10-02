# FP Assistant

A **financing proposal (FP)** sets out the case for a loan or investment. It explains the business, financial performance, repayment capacity and risks. Credit or investment teams use it to support an approval decision.

Preparing this paper takes information from financial statements, transaction documents, interviews and emails. New evidence arrives during due diligence. Sources can conflict. The team must reconcile the information and write a clear paper in its own template and style.

AI can help, but clear wording alone is not enough. Each material figure needs a source. Management expectations must remain distinct from verified facts. Open questions and analyst edits must survive each revision.

**FP Assistant helps with this work.** It combines AI skills for analysis and writing with local tools that manage evidence, financial tables and Word revisions. It can improve an existing draft or start from a template. The investment officer controls the recommendation and approval decisions.

## How it works

The assistant reviews sources, analyses the financing case and drafts the paper. It challenges important claims and identifies missing evidence. New emails and interview notes update the analysis and the affected sections.

Approved proposals guide the house style. ASD-STE100 (Simplified Technical English) guides clarity. Financial terms, necessary qualifications and natural paragraph flow take priority where strict simplification would reduce accuracy or readability.

Eight skills define the work. Each skill has a `SKILL.md` instruction file, references and tools. The assistant loads a skill when it needs that task.

| Skill | Responsibility |
|---|---|
| `fp-lead` | Develop the financing case, draft the paper and coordinate revisions |
| `deal-analyst` | Explain the company and transaction; maintain the diligence analysis |
| `deal-updates` | Assess emails, interviews and informal guidance; update evidence and open questions |
| `annual-report-review` | Read financial statements and notes, retaining source locations and coverage gaps |
| `financial-performance-analysis` | Explain earnings, working capital and cash movements |
| `repayment-and-structure` | Assess debt service, liquidity, covenants and financing terms |
| `investment-grill` | Challenge consequential claims, assumptions and conclusions |
| `fp-template-style-reviewer` | Check the template, house style and final document presentation |

FP Lead coordinates the work. The host must support separate tasks to run an independent reviewer. The plugin does not run its own agent service.

## Technical implementation

Three Python 3.9+ tools use only the standard library:

| Tool | What it does |
|---|---|
| `register.py` | Maintains a JSON record of sources, risks, questions, findings and analysis. Generates Excel and Markdown views. Revision checks reject stale updates; retry IDs prevent duplicate changes. Promised or received-but-unassessed answers remain outstanding. |
| `fp_docx.py` | Reads Word document structure and writes revisions to a new file. Section signatures and a companion `.sections.json` record detect officer edits. Protected sections remain intact and unapplied replacements go into a proposals file. |
| `fin_table.py` | Reads an identified spreadsheet export, transfers selected figures and performs limited calculations. Records workbook hashes, cell references and formulas; refuses ambiguous labels or periods and requires an explicit basis for trusting cached formula values. |

The AI interprets evidence and writes the paper. The Python tools perform repeatable file and record operations.

The package targets Microsoft Copilot Cowork. The host must provide the model, authorised file access and Python execution. It must also retrieve and save the outputs. The plugin includes no email connector, database or hosted backend.

## Try it

Start with a partially completed FP. Supply the separate blank template, original evidence, a checked financial spreadsheet export and approved writing examples. Ask:

> Improve this financing proposal as a whole. Check the existing analysis. Explain the financial movements and repayment case. Follow the supplied template and writing examples. Save a new Word version and preserve protected content. Identify missing evidence and proposed changes that could not be applied.

**Version 0.3.0 is available for a supervised pilot.** `main` contains the latest implementation.

[Installation and pilot instructions](INSTALL.md) · [Design](docs/design.md) · [Validation results](evaluations/results.md)

Local tests cover the tools and synthetic files saved in Microsoft Word. The pilot must still check Cowork operation, the actual template and the quality of the complete paper.

The Word tool preserves predefined financial tables but cannot fill them. It also cannot add missing section headings. A person must review the facts, analysis, writing and final layout.

## Development

Run the checks and build the upload packages:

```sh
uv run pytest -q
python3 scripts/package.py
python3 scripts/package.py --check
```

Edit the original files in `shared/` and `tools/`. The package script copies them into each skill that needs them. It builds a plugin ZIP and individual skill ZIPs in `dist/`.

The repository includes tests and reusable synthetic cases. Git ignores local plans, run logs and generated outputs. Keep confidential deal material in its approved work environment.

## Toward Bankability

This project tests ways to make financing analysis and proposal writing more consistent, traceable and useful. If the methods work across deals and institutions, they could contribute to **Bankability**: a shared standard for evidence-based financing workflows. This is a possible direction for the experiment. It is not yet an established standard.
