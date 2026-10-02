# FP Assistant

Preparing a **financing proposal (FP)** means turning financial statements, transaction documents, interviews and correspondence into a clear recommendation for a credit or investment decision. The information is spread across files, changes during due diligence and often contains conflicting explanations. The final paper must explain the business, the numbers and the risks while following an institution's template and writing style.

AI can help with that work, but fluent prose is not enough. Figures need to be traceable to their sources. Management expectations must remain distinct from verified facts. Unanswered questions must survive successive drafts, and an analyst's edits must not disappear when the assistant revises the document.

**FP Assistant is an experimental toolkit for that workflow.** It combines reusable AI skills for analysis, drafting and review with local tools for evidence records, financial tables and controlled Word revisions. It starts from an existing proposal or template and helps the investment officer develop the whole paper, with supporting analysis and explicit gaps. The officer retains the recommendation and approval decisions.

## How it works

The workflow moves from source review to financial analysis, drafting and challenge. New emails or interview notes feed back into the analysis and affected sections. Approved proposals guide the house style; ASD-STE100 (Simplified Technical English) provides clarity principles, with deliberate departures for financial terminology, qualifications and natural institutional prose.

Eight skills define the specialist work. Each is a `SKILL.md` instruction file with relevant references and tools, loaded when its task is needed.

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

FP Lead calls for specialist work where useful. Separate reviewer tasks depend on the host's capabilities; the plugin does not launch an independent agent service.

## Technical implementation

Three Python 3.9+ tools use only the standard library:

| Tool | What it does |
|---|---|
| `register.py` | Maintains a JSON record of sources, risks, questions, findings and analysis. Generates Excel and Markdown views. Revision checks reject stale updates; retry IDs prevent duplicate changes. Promised or received-but-unassessed answers remain outstanding. |
| `fp_docx.py` | Reads Word document structure and writes revisions to a new file. Section signatures and a companion `.sections.json` record detect officer edits. Protected sections remain intact and unapplied replacements go into a proposals file. |
| `fin_table.py` | Reads an identified spreadsheet export, transfers selected figures and performs limited calculations. Records workbook hashes, cell references and formulas; refuses ambiguous labels or periods and requires an explicit basis for trusting cached formula values. |

The AI handles interpretation and writing; these tools handle repeatable file and record operations. The package targets Microsoft Copilot Cowork, which must provide the model, authorised source access, Python execution and file retrieval/saving. No email connector, database or hosted backend is included.

## Try it

Supply a partially completed FP, the separate blank template, original evidence, a checked financial spreadsheet export and approved writing examples. Ask:

> Improve this financing proposal as a whole. Check and improve the existing analysis, explain the financial movements and repayment case, and follow the supplied template and writing examples. Save a new Word version, preserve protected content, and identify missing evidence and changes that could not be applied.

**The 0.3.0 implementation is on the [development branch](https://github.com/rrecourt2/fp-assistant/tree/tools-and-cleanup), under review in [PR #1](https://github.com/rrecourt2/fp-assistant/pull/1).** The default branch retains the earlier implementation until that review is complete.

[Installation and pilot instructions](https://github.com/rrecourt2/fp-assistant/blob/tools-and-cleanup/INSTALL.md) · [Design](https://github.com/rrecourt2/fp-assistant/blob/tools-and-cleanup/docs/design.md) · [Validation results](https://github.com/rrecourt2/fp-assistant/blob/tools-and-cleanup/evaluations/results.md)

Local tests cover the tools and synthetic Word files saved in Microsoft Word. Actual Cowork operation, institutional-template compatibility and whole-paper writing quality still need a supervised pilot. The writer currently preserves predefined financial tables rather than filling them and cannot insert entirely missing headings. Human factual, substantive and visual review remains necessary.

## Development

On the development branch:

```sh
uv run pytest -q
python3 scripts/package.py
python3 scripts/package.py --check
```

`shared/` and `tools/` are the maintained originals. Packaging copies their contents into the skills for self-contained upload and builds plugin and individual-skill ZIPs in `dist/`. Tests and reusable synthetic evaluation cases are tracked; local plans, run logs and generated outputs are ignored. Keep confidential deal material in its approved work environment.

## Toward Bankability

This is an experiment in making financing analysis and proposal writing more consistent, traceable and useful. If its methods prove effective across deals and institutions, they could contribute to **Bankability**: a broader shared standard for evidence-based financing workflows. That is a direction for development, not an established standard.
