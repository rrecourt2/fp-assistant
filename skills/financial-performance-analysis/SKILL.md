---
name: financial-performance-analysis
description: Explain financial movements, earnings quality and cash conversion for a financing proposal. Use for revenue or margin changes, profit versus cash, working capital, adjustments, financial trends and the FP's financial table. For complete report reading use annual-report-review; for debt service and financing terms use repayment-and-structure.
---

# Financial Performance Analysis

Explain what changed, which drivers are supported, what remains unexplained and why it matters to financing. Produce reasoning the FP writer can use; do not merely restate the financial table.

Apply [operating-rules.md](references/operating-rules.md) and [workflow-contract.md](references/workflow-contract.md). Use the approved spread, relevant original statements/notes, interim accounts, management explanations and available prior analyses. State the period and perimeter of each comparison. The initial pilot concerns corporate borrowers; sector-specific accounting or regulated-capital cases require suitable institutional methodology, not forced industrial-company ratios.

Tools: [register.py](scripts/register.py), [fin_table.py](scripts/fin_table.py). Use the workflow contract for invocation and record updates.

## Establish comparable inputs

When constructing a bridge, normalising earnings or analysing working-capital days, consult [financial-analysis-methods.md](references/financial-analysis-methods.md) for definition and reconciliation checks. Load only the relevant sections.

Match entities, consolidation boundaries, fiscal periods, currencies, scale and accounting definitions. Prefer restated comparatives for like-for-like trends while explaining the restatement. Distinguish actual, forecast and management-adjusted figures. Identify acquisitions/disposals or accounting changes before interpreting growth.

Use deterministic calculation tools for changes, percentages, margins and bridges. Retain formulas, referenced inputs, rounding and unexplained residuals. Do not fabricate a complete bridge from qualitative commentary. If a calculation cannot be verified, label it provisional and limit reliance on it.

## Explain the performance

Select material movements rather than commenting on every row. Assess:

- **Revenue:** volume, price, mix, acquisitions/perimeter and FX where evidence permits. Separate sales growth from improved profitability or cash collection.
- **Margins and earnings:** operating drivers, one-off claims, accounting effects and adjustments. Evaluate whether a supposed exceptional item recurs, reflects normal business risk, or has a cash consequence; preserve reported earnings alongside proposed adjustments.
- **Profit to cash:** reconcile available earnings measures to operating cash, distinguishing working-capital movements, taxes, interest and other items under the relevant presentation. Avoid double counting.
- **Working capital:** receivables collection, inventory quality/seasonality, payable stretch, customer advances and financing arrangements. A release can temporarily raise cash without establishing sustainable cash generation.
- **Investment and funding:** capex, distributions, acquisitions and financing flows; distinguish maintenance and growth capex only when supported. Explain the source of cash-balance changes and identify restrictions relevant to the borrower.

Test management explanations against notes, operating data and later evidence. Record them as attributed explanations unless corroborated. Quantify their contribution only when supported; do not allocate the unexplained remainder to a convenient cause. A reconciled bridge still requires a plausible mechanism.

For each decision-relevant movement give: observation; supported drivers; contrary evidence or unexplained portion; recurring/temporary assessment where justified; financing implication; further evidence needed if material. Use this as analytical content, not compulsory prose headings.

## Turn analysis into FP input

Write concise conclusions about earning power, cash conversion and dependence on assumptions. Connect them to the business timeline and distinguish structural change from timing. Hand borrower liquidity, maturities, covenant definitions and forward repayment questions to repayment-and-structure with the relevant evidence, rather than certifying debt-service capacity from historical EBITDA alone.

Example distinction: a disclosed write-down supports its amount and accounting treatment. It does not establish that the full margin decline is temporary, that it can be added back for a covenant, or that its reversal supplies cash for repayment.

## Deliver

Provide a compact movement/driver analysis, checked calculations and draft-ready explanatory paragraphs with source locators. List only material unexplained differences and targeted evidence requests. Identify the basis and limits of every adjustment or recovery assumption. Continue supported analysis while gaps remain; do not convert estimates into facts to complete a table. Update affected conclusions when new evidence changes a driver. Completion means sufficient, transparent support for the requested explanation, not a claim that all financial risks or the financing itself have been approved.
