# Evaluation

Fixtures in this repository are synthetic. Real deal/template evaluation stays in the approved work environment; record only non-confidential outcomes here. [Results](results.md) separate local script checks from tenant behaviour and FP quality.

## Local checks

Run `uv run pytest -q`, build the package, then run each packaged script's `selftest` with Python 3.9+. The Word suite includes officer-saved synthetic files covering ordinary sections and an assistant-created table. These fixtures test edit detection and preservation, not every template or visual outcome.

## Behavioural cases

Use [scenarios.md](scenarios.md), [transcript-case.md](transcript-case.md) and [deal-updates-case.md](deal-updates-case.md). Keep [reviewer-guide.md](reviewer-guide.md) and expected outcomes out of the actor's context.

1. Give a fresh actor the raw task/evidence and the applicable packaged skills. For the routing case, supply all eight descriptions without telling it which skill to choose; reveal selected skill bodies only after selection.
2. Record model/version/effort, skill/package version, source versions, tools available, saved outputs and actual limitations. Distinguish a hypothetical no-runtime scenario from a test that actually executes the shipped tools.
3. Have a fresh reviewer assess the output against the hidden criteria. Preserve the actor output and verdict; record critical failures even when the prose is good.
4. Add a result to results.md. Fix observed failures and rerun the affected case, retaining earlier failed evidence.

Qualify the intended Cowork model on scenarios 1, 2, 3 and 5 plus the deal-updates case. Test another model before switching to it. Rerun affected scenarios after local changes; there is no blanket two-model/all-cases requirement for every edit.

## Main acceptance test

Follow [INSTALL.md](../INSTALL.md): improve a partially completed FP using a separate template, assess the entire paper, make officer edits and add a subsequent email/transcript, then resume in a fresh task. Evaluate explanation of business and financial drivers, repayment, relevance, whole-paper consistency, evidence, house style and officer repair time. An optional section sample does not replace the full-paper test.

The approved historical target FP is a comparator for the reviewer, not an input answer for the drafting agent. Use other approved papers as style examples. Expand to more varied historical deals before wider use. A passing local or synthetic test is not tenant acceptance.
