# FP Assistant v3 — skill review and source index

**Date:** 1 October 2026. **Result:** seven reviewed draft skill sources, preserving the original editorial principles and separating three specialist financial methods. Structural validation passed. Independent behavioral testing and work-tenant validation remain outstanding; these files are not an installed or production-certified plugin.

The officer supplied the original 25 September four-role execution pack in this conversation. Its core writing principle, approval-case guidance and five operating rules are retained in [the canonical shared reference](../shared/operating-rules.md). Deal name, financing amount, annex topics and private audience information are kept out of the reusable skills.

Subsequent user feedback led to a separate [transcript and Deal Strategy extension](transcripts-and-strategy.md), including a draft eighth skill. Its [validation record](../evaluations/transcript-review.md) is separate from the seven-skill baseline results below; it is not yet included in the combined handover pack.

## Why seven skills

Keep the four useful roles, and give recurring financial tasks their own methods. Deal Analyst remains responsible for integrating business, management, transaction and specialist diligence; replacing it with a purely financial analyst would leave that wider synthesis unclear. The three added skills address different failure modes: incomplete disclosure reading, weak explanations of performance, and unsupported repayment/structuring conclusions.

They are selected when needed. There is no requirement to launch seven agents, obtain seven approvals, or repeat a source read that has already been completed for the same source version. The design does not assume Microsoft supports Claude's subagent mechanisms.

| Skill source | Main result | Body words at structural check |
|---|---|---:|
| [Deal Analyst](../skills/deal-analyst/SKILL.md) | Integrated company/DD analysis, specialist views, annex input and open items | 611 |
| [Annual Report Review](../skills/annual-report-review/SKILL.md) | Complete scoped reading, located disclosures and honest coverage gaps | 586 |
| [Financial Performance Analysis](../skills/financial-performance-analysis/SKILL.md) | Comparable movements, supported drivers, earnings quality and cash conversion | 584 |
| [Repayment and Structure](../skills/repayment-and-structure/SKILL.md) | Borrower liquidity/debt service, covenant analysis, protections and conditions | 577 |
| [FP Lead](../skills/fp-lead/SKILL.md) | Concise approval case, controlled revisions, Credit replies and scoped readiness | 763 |
| [Investment Grill](../skills/investment-grill/SKILL.md) | Original-evidence challenge and focused recheck findings | 603 |
| [Template and Style Reviewer](../skills/fp-template-style-reviewer/SKILL.md) | Binding template rules, clear prose, preserved meaning and actual layout status | 532 |

Each skill links its local copies of the shared rules and [workflow contract](../shared/workflow-contract.md). Performance and repayment skills additionally have targeted method references, loaded only for the relevant work. Shared references are maintained once in `shared/` and copied identically into each skill to satisfy Microsoft's self-contained companion-path requirements.

## Review of the original pack

| Original strength or gap | v3 treatment |
|---|---|
| Strong institutional writing principle, with no manufactured risk paragraphs | Preserved. Factual-description and sound-case evaluation cases check restraint as well as challenge. |
| Balanced approval case and genuine officer judgment | Preserved; initial recommendation explicitly provisional. Contrary evidence must reach the officer and remain in the main FP when decision-changing. |
| General Deal Analyst covered most finance tasks in seven broad instructions | Three focused methods now describe disclosure coverage, causal/financial analysis and forward repayment. The general analyst integrates rather than repeats them. |
| Original evidence review followed material questions but did not guarantee every annual-account note was read | Annual Report Review has a page/part ledger, actual-page check, image/OCR fallback and separate unreadable/unresolved states. |
| Figures and explanations could remain narrative-only | Performance methods distinguish reporting scope/restatements, supported bridges, residuals, earnings adjustments and cash. Formula/input provenance accompanies calculations. |
| Preliminary repayment review could rely on aggregate ratios or management intentions | Repayment methods identify the obligor, accessible cash, commitment/availability, dates, contractual covenant definitions and condition effectiveness. |
| Original main FP plus two annexes reflected one deal | Annex count/questions now come from the brief; unspecified topics remain open without stopping unrelated work. |
| Background Markdown and the new workbook risked competing as editable masters | One canonical register with a keyed Analysis sheet; Markdown is generated. Word remains a distinct editable handoff. |
| Strong general preservation rule lacked simple supported update boundaries | Freeze human-edited/ambiguous sections and offer replacements separately. No arbitrary paragraph merge or misplaced caveat. |
| Original review was scoped by version, but mutable Word could outlive an old Ready result | Readiness binds the current content hash and evidence revision; later changes require reconciliation. |
| Broad role descriptions could activate overlapping workflows | Primary triggers distinguish reading, explanation, repayment, drafting, challenge, presentation and general diligence status. |
| Two challenge rounds per section could create repeated work | One substantive round plus a recheck by default, with extra work for unresolved material issues or new evidence. |
| Skill instructions could imply unavailable runtime operations | Capability check and provisional-analysis mode; no fabricated commands, register writes, independent-agent runs or Ready status. |

## Current guidance applied

Microsoft's current author guide supports progressive disclosure, action-oriented instructions and self-contained relative companion paths. The new skills have matching names/folders and valid descriptions, with two or three companions each. [Microsoft authoring and packaging guidance](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development).

Anthropic recommends concise instructions, flexibility appropriate to the task's fragility and representative evaluation on the intended model. Here the analysis remains flexible while state changes, evidence handling and preservation have precise limits. [Anthropic skill guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

OpenAI separates workflow instructions from tools that provide data and enforce actions. This informs the explicit distinction between an analytical skill and a successful persistent operation. [OpenAI skill concepts](https://developers.openai.com/plugins/concepts/skills). Its 11 September prompting article also cautions against overly broad activation and unnecessary prerequisite reading; that model-specific guidance is a hypothesis to test on GPT 5.6, not evidence that results transfer automatically. [Model-specific discussion](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra).

The finance precedents are concrete methods, not claims of guaranteed accuracy. Anthropic's Earnings Reviewer connects source evidence, model changes and written output. Its September Financial Advisors extraction worker preserves requested source detail before synthesis. The v3 skills borrow those separations without importing their platform-specific orchestration. [Earnings Reviewer](https://github.com/anthropics/financial-services/blob/bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d/plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md), [source extraction worker](https://github.com/anthropics/claude-for-financial-advisors/blob/bcef83e6c849e35de6dfd6fe1274dd0022efdc44/agents/source-extract.md).

## Validation actually completed

- Read the supplied original pack and compared its role responsibilities, core writing principle and shared rules with the revised sources.
- Applied the earlier independent design reviews and current primary-source authoring guidance.
- Ran the skill-creator frontmatter/name/placeholder validator on all seven skill folders: all passed.
- Checked all local skill reference links, Microsoft companion size/count/path limits and byte equality of copied shared references: all passed.
- Prepared eight synthetic behavioral cases and explicit reviewer criteria; checked the numeric fixture with deterministic arithmetic and reviewed the intended version/ownership states for consistency.

The fresh-agent baseline and revised-skill behavioral runs were **not executed**: delegated reviewers hit the account usage limit during this turn. Do not interpret scenario preparation, arithmetic checks or editorial review as a measured behavioral pass. Earlier agents did complete design/authoring reviews before that limit, but they did not execute these final seven skill sources.

Run the [raw scenarios](../evaluations/scenarios.md) with fresh actors and keep the [reviewer guide](../evaluations/reviewer-guide.md) hidden from them. Validate on the exact tenant model and available tools, then perform the real-report/template replays in the [v3 plan](design-v3.md). Whole-report recall, actual Word preservation and reliable remote publication remain runtime acceptance tests.

## Handover and maintenance

The combined [skill pack](handover-v3.md) is a readable handover document; the seven folders are the editable source. No skills were installed and no live systems were changed. Future packaging must include the shared companions locally and add only implemented, validated scripts. Do not distribute a plugin that describes nonexistent operations as available.

Keep changes driven by a real recurring task or an observed evaluation failure. Add a separate sector method only when it changes the actual analysis and has representative inputs, outputs and tests. Do not split every ratio or checklist topic into another skill.

## Final-writing refinement after officer feedback

An independent review found only three small instruction changes necessary: organise each section around its subject with sufficient descriptive context; let financial reasoning develop across the section; and judge overall flow against approved examples rather than enforce a repeated paragraph sequence. These changes are incorporated in the shared rules, FP Lead, Template and Style Reviewer, and combined handover pack. No additional writing skill, mandatory review round or topic-specific writing recipe was added.

This is a design judgment, not a demonstrated house-style match. No actual approved institutional FP examples were supplied for this check. The existing historical-replay and officer review should assess a representative drafted section for evidence, content selection, topic order, tone and readability together. The transcript fixture tested meeting intake, not final FP writing quality.

## 2 October packaging and review refinement

FP Lead and Investment Grill now include the [material-checkpoint review protocol](../shared/review-protocol.md), including a fresh arbiter mode for consequential disputes. This amendment has been structurally checked but not behaviorally evaluated in the work tenant. The updated sources are bundled in a compatible-plugin preview; see [installation limits](../INSTALL.md). Earlier behavioral results apply only to the recorded cases and versions.

## 2 October email and guidance expansion — preview 0.2.0

The eighth skill is now titled Deal Updates and Guidance, retaining `meeting-evidence-review` as its identifier. It covers relevant recent emails, attachments, threads and meeting material; explicit review scope/cutoff; ambiguous guidance; source authority and supersession; and prioritised implications for the whole FP. FP Lead invokes the refresh before drafting, material revision and readiness assessment. The [new test record](../evaluations/deal-updates-review.md) distinguishes its fresh-actor result from actual mailbox integration.

The startup instructions now make full-FP drafting the normal path. A representative section is optional setup/style calibration after understanding the deal. No ninth skill, background monitoring or new connector was added.
