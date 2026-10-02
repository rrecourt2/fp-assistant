# FP Assistant

Eight skills and three local tools for improving and completing a financing proposal in its Word template. Start from a partially filled FP, retain useful work, explain the business and figures, and keep the outstanding questions visible.

**Version 0.3.0 is a local implementation for a supervised pilot.** Microsoft Word save fixtures are included in the tests. Cowork import, tenant file persistence, live correspondence access and full-FP writing quality still require acceptance in the work environment. No connector or background agent service is included.

## Start with your existing FP

Provide the partially completed FP, the separate blank template, relevant evidence and approved style examples. Ask:

> Improve and complete this FP as a whole. Use the existing draft as the base and the separate template to check completeness. Retain useful content, explain material financial movements and repayment, and match our FP style. Save a new Word version, preserve protected content, and show remaining evidence gaps or proposed edits that could not be applied.

The initial authorised import can improve existing unprotected prose. Later officer edits stay protected; proposed replacements are returned separately. If a file is a renamed assistant version, recover its source record instead of importing it afresh.

| Request | Skill |
|---|---|
| Improve, draft or revise the FP; integrate reviews; Credit replies | `fp-lead` |
| Analyse the company/deal; integrate diligence; what's open? | `deal-analyst` |
| Refresh emails, interviews, notes or Word comments | `deal-updates` |
| Read the annual report and notes completely | `annual-report-review` |
| Explain earnings, working capital and cash; prepare financial table | `financial-performance-analysis` |
| Assess repayment, covenants, financing structure and conditions | `repayment-and-structure` |
| Challenge the case or recheck a material finding | `investment-grill` |
| Template preflight, house style and layout review | `fp-template-style-reviewer` |

Skills are selected methods, not eight mandatory agents. Review covers important analyses and the whole paper. Separate reviewer tasks depend on the host's actual capabilities.

## Files and tools

- `register.py`: one JSON master with generated Excel/Markdown views, source/issue records and a concise status view. Promised and answered questions remain unfinished until closed.
- `fp_docx.py`: versioned Word output, inspection and conservative protection of officer edits. The original input stays unchanged.
- `fin_table.py`: transfers figures from an identified spreading export, keeps source cells, and performs bounded calculations.

The scripts use Python 3.9+ and the standard library. Authorised host tools must fetch and return the files. The first test proves that this works in the intended Cowork environment.

[Installation and first full-FP test](INSTALL.md) · [Current design](docs/design.md) · [Validation status](evaluations/results.md)

## Develop

```sh
uv run pytest -q
python3 scripts/package.py
python3 scripts/package.py --check
```

The two ZIPs are built into ignored `dist/`. `shared/` and `tools/` contain the originals; packaging copies them into the skills that use them. Development dependencies are test readers only. Keep confidential deal data, internal templates and private notes out of this repository. [Earlier designs](docs/archive/README.md) remain as history.
