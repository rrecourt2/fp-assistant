# FP Assistant — Design Spec v3

**Date:** 1 October 2026. **Status:** revised design and draft skill sources; not installed, implemented or verified in the work tenant. Supersedes v2 for the proposed pilot; v2 is retained unchanged.

This version incorporates the independent assessment, the officer's original 25 September execution pack and the request to add useful finance specialist skills. Part A describes the officer's workflow. Part B defines the smallest dependable implementation and how to test it.

**Eighth-skill extension:** [Deal Updates and Guidance and a living Deal Strategy](transcripts-and-strategy.md) address subsequent feedback about recent deal emails, client/internal/legal transcripts and fuzzy guidance. The extension includes a draft eighth skill; the seven-skill baseline below remains identifiable.

**Review refinement:** [material-checkpoint review and arbitration](adversarial-review.md) clarify that substantive challenge covers the case plan, important sections, the whole draft and consequential revisions. The default round plus recheck applies per checkpoint; a fresh third arbiter handles unresolved material disagreement or requested high-impact adjudication.

## Part A — For the investment officer

### A1. What FP Assistant does

FP Assistant helps prepare a well-supported financing proposal in the institution's Word template. It develops the fuller analysis, selects the strongest defensible approval case, challenges that case and improves the writing. The officer retains judgment over the recommendation, material risk placement, conditions and submission.

The four familiar roles remain: Deal Analyst, FP Lead, Investment Grill, and FP Template and Style Reviewer. Three specialist skills add depth: Annual Report Review, Financial Performance Analysis, and Repayment and Structure. These are seven selectable methods, not seven mandatory agents, meetings or review rounds.

Three small program responsibilities support the work: maintaining the records, producing controlled Word revisions and transferring/checking financial figures. Their implementation size and effort will be measured after a complete working slice; v3 makes no line-count or time-saving promise.

OneDrive is the first deployment target. Deal files remain there; processing follows the tenant's approved model-provider settings. There is no proposed custom hosted service. SharePoint follows only after its file operations pass the same tests.

The deal's `FP assistant` folder holds versioned register workbooks, the current editable Word handoff, a readable Analysis document generated from the register, and review/proposed-replacement or Credit-reply outputs. The register is the authoritative record. The officer edits Word, rather than maintaining the register or synchronising two analysis files.

### A2. How a deal runs

| Request | Work and result |
|---|---|
| Start an FP; here is the deal folder | FP Lead establishes the files, brief and reading plan. Checkpoint 1 confirms missing material inputs: decision sought, provisional recommendation, audience, annex questions, deadline and document tiers. Existing supplied instructions need not be approved again. |
| Analyse the deal | Deal Analyst builds the business and transaction account, integrates specialist work and tracks risks, conditions and open questions. Annual Report Review reads key accounts completely; the other finance specialists explain performance and test repayment. |
| Here are new notes, documents or emails | Record the source and author, assess its impact on existing conclusions, preserve differing views and reopen affected checks. |
| Draft the FP | Checkpoint 2 settles material risk destinations, key messages and section plan. FP Lead drafts the summary and main risk section first for Checkpoint 3 feedback, then completes the main FP and configured annexes. |
| Grill this version | Investment Grill challenges the exact draft using original evidence. FP Lead repairs it; the grill rechecks. One round plus recheck is the default. |
| Update from my Word edits | The current Word file is inspected first. Edited sections and their comments remain in place. Proposed replacements are supplied separately; untouched AI-owned sections can be updated automatically. |
| Review the style | The dedicated template/style task polishes settled material, identifies meaning changes and inspects the resulting Word layout. |
| What's open? | A concise view of client requests, internal actions and proposed conditions, with owners, criticality and deadlines where known. |
| Is it ready; we submitted it | Checkpoint 4 reports readiness for the exact Word/evidence version. Record the officer's submission, including any explicit exceptions. |
| Credit asked these questions | Preserve actual questions verbatim, retrieve the support, prepare direct replies and revise the FP where the question changes the case. |

Work remains sequential for one deal writer. Specialist methods can be used within a task when supported, or through explicit handoffs. A skill cannot promise to launch another task or change its model. Use the tenant's approved GPT 5.6 variant initially, recording the exact variant and effort. Compare effort settings during the pilot; do not require model switching for every small step.

### A3. Reading the evidence

| Tier | Default treatment |
|---|---|
| A: read completely | Latest audited accounts, including directors' report, audit report, statements and every note; latest interim/management accounts; proposal/term sheet; relevant prior FP and Credit decision. Add any legal, security, E&S or other document that is critical to this decision. |
| B: read relevant sections and changes | Older accounts, historical correspondence and specialist material not already in Tier A; identify restatements, policy changes and continuing commitments. Promote documents when their importance becomes clear. |
| C: index and search | Other supporting material. Search for relevant evidence without treating an index or digest as a complete read. |

For a requested whole annual-report review, read the whole report. Establish the part map against actual pages as well as the contents page. Read in logical chunks, with roughly 15 pages as a working target, keeping complete tables, footnotes and note continuations together. Retain both PDF page and printed page references when different.

Record each part as read, pending or unreadable. Recover poor text with page images/OCR where available. Never treat extraction failure as “not disclosed.” The annual-accounts topic checklist covers audit/going concern; policies and restatements; revenue and segments; earnings adjustments and impairment; working capital and restricted cash; borrowings, leases, maturity and covenants; FX/interest/liquidity; related parties, ownership, commitments, guarantees, contingencies, tax and subsequent events. Each topic ends as found, not applicable with basis, not disclosed after relevant review, or unresolved.

The short source digest is for navigation. Material assertions also retain their supporting passage/table/cell and qualifications. The grill reopens original evidence for decisive claims. Reading coverage does not itself establish analytical correctness.

Checkpoint 2 normally follows completed Tier A reading. The officer can proceed with an explicitly recorded scope exception; unread material remains labelled unread, and any consequential blocker remains visible.

### A4. What makes the FP good

Retain the original writing principle: **observation → material risk → relevant mitigants → residual risk and conclusion**, applied within the controlled FP structure. Use a factual description where no material risk warrants discussion. Write succinctly in familiar institutional language, calibrated against the officer's approved examples.

Organise each section around the topic's natural logic, retaining enough descriptive context and omitting immaterial detail unless required. Apply the risk reasoning across paragraphs where appropriate. FP Lead and the style reviewer use the approved examples to judge flow, depth and tone, with room for justified departures from the usual pattern.

The analysis must establish the recent business story and explain the material financial movements. For each important change, record the comparable figures, supported drivers, contrary evidence or unexplained portion, and implication for the financing. Distinguish price/volume/mix, changes in reporting scope, accounting effects and recurring versus temporary drivers where evidence permits. Do not force a complete bridge from qualitative management commentary.

Connect earnings to cash conversion, cash availability to the actual borrower, and repayment to the timing of obligations. Use approved forecasts and downside cases where available. Where essential forward analysis is missing, identify the gap rather than substituting historical EBITDA for repayment capacity.

A disclosed amount, a management explanation, an analyst inference and a checked calculation are different evidence types. A balanced bridge does not prove causation. A source reference does not turn an intended refinancing or proposed condition into an implemented mitigant.

The main FP must explain why the financing on these terms is defensible, what the case depends on, what could change the recommendation and what residual exposure remains. Include development impact/additionality and relevant specialist conclusions. Each annex answers its configured question; its decision-relevant conclusion also appears in the main FP. Annex count and topics belong in the deal brief, not the reusable skills.

### A5. Protection of work and judgments

1. Preserve source documents. Supported program operations control persistent records and Word updates; instructions alone are not a platform access-control guarantee.
2. Keep one officer task writing at a time. A local hash check is not a cloud concurrency lock.
3. Keep officer-edited, commented, track-changed or ambiguously owned Word sections in place. Supply proposed replacements separately. Do not append a displaced caveat elsewhere or exempt officer text from factual review.
4. Every new/changed source needs an impact disposition, even if no existing risk points to it. Pending dispositions block Ready. A supported no-impact result can clear one.
5. Preserve supporting and contrary evidence. Material risk downgrades, movement of high-rated/blocker-linked risks out of the main FP, unsupported closure and changes to the intended recommendation require explicit officer disposition. That disposition does not make the evidence verified.
6. A proposed mitigant must address the specific risk at the necessary time. Distinguish existing protection, proposed condition and assumption; record implementation and adequacy separately.
7. Preserve financial meaning in style edits, including entity, timing, certainty, negation and conditions, not only figures and references. Substantive changes require affected analysis and rechecks.
8. Ready applies only to the exact Word content hash and evidence revision checked. Later edits or evidence invalidate the current status until reconciled. Required content, template and layout checks must pass; no blockers, pending source impacts or rechecks may remain.
9. If the officer submits with exceptions, preserve the explicit decision and outstanding exceptions. Do not relabel it a clean Ready result. Communications remain drafts; nothing is sent automatically.

### A6. Records and readable analysis

| Register sheet | Purpose |
|---|---|
| Control | Brief, configured annexes, current files, revision, section status, officer decisions and readiness basis. |
| Sources | Source identity/version, scope, dates, locators, tier, coverage and impact disposition. |
| Risks | Observation, mechanism, rating, residual exposure, destination/reason and who raised it. |
| Mitigants | Linked risk, type, evidence, implementation/applicability/timing and proposed-condition details. |
| Open items | Client requests, internal actions, prior/actual Credit questions, owner, criticality, deadline, answer and disposition. |
| Findings | Substantive/style findings, reviewed version/scope, response, evidence and recheck result. |
| Analysis | Keyed narrative: company/transaction account, dated developments, financial drivers, risk reasoning, report-part findings and annex analyses. |
| FP map | Section-level evidence/risk links, ownership and Word baselines. Material claims retain precise evidence locations; arbitrary paragraph merging is outside v1. |
| Check | Mechanical problems, evidence gaps and required review states with severity. |
| Log | Operation/revision, actor, model/effort, inputs, actual outputs, checks and next action. |

The generated `DEAL-Analysis.md` presents the narrative attractively and identifies its register revision. It is not a second editable master. Source IDs S, risks R, mitigants M, open items O, grill findings G and style findings T remain stable. Private audience notes stay in the officer's private tenant location.

### A7. The seven skills

| Skill | Owns | Boundary |
|---|---|---|
| Deal Analyst | Company/commercial/DD synthesis, specialist views, risk record and specified annex analyses | Integrates specialist finance work; does not duplicate it. |
| Annual Report Review | Complete accounts/notes reading, scope, disclosures and coverage gaps | Establishes evidence; does not certify forward repayment. |
| Financial Performance Analysis | Trends, earnings quality, drivers and cash conversion | Explains performance; does not invent forecasts or covenant definitions. |
| Repayment and Structure | Borrower liquidity, debt service, maturity/refinancing, covenants and effective protections | Uses approved models and legal evidence; does not create a modelling platform or legal opinion. |
| FP Lead | Approval-case selection, drafting, officer edits, coordination, readiness and Credit replies | Owns the paper; escalates material adverse evidence and judgment choices. |
| Investment Grill | Evidence-based challenge and repair rechecks | Returns focused material findings; does not manufacture objections or own the prose. |
| Template and Style Reviewer | Preflight, house style, template compliance and actual layout checks | Separate task; substantive meaning changes return to the lead. |

The initial methods target corporate borrowers. Banks, insurers, funds, project finance and other materially different structures require appropriate institutional methods before unfamiliar ratios or scenarios are treated as decision evidence. Add sector-specific skills only where a recurring task and tested examples justify them.

### A8. Setup and first use

Supply the controlled template, an existing draft if any, approved FP examples, source/output folders, officer, deadline, brief and annex questions. Retain the original five operating rules and approval-case principle in all skills. Approve reusable template/style rules and the spread-to-FP mapping once per relevant version.

First prove file access, saving and the real-template loop in the work tenant. The normal task establishes the whole deal picture and drafts the full FP. An optional financial-section sample can calibrate style after that analysis; it is not a prerequisite for full drafting. Test challenge and an officer revision. Expand to three varied historical replays and one supervised live pilot. Judge the finished FP and the officer's repair burden, not just first-draft speed.

## Part B — Builder appendix

### B1. Platform baseline and uncertainties

Microsoft documents skills with executable companion files, temporary processing and native Office editing. Shared skill syntax does not establish equivalent runtime behaviour between Microsoft Cowork, Claude Cowork and Claude Code. A local test can verify scripts/prompts; only the actual tenant proves access, persistence, labels, approvals and model behaviour. [Microsoft plugin author guide](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development), [September release notes](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/whats-new).

Seven skills fit the documented plugin limit. Each skill must contain its own referenced companion files using relative paths without `..`. Package common references from one maintained source; do not hand-maintain divergent copies. Commands/subagents/hooks from Claude plugins are not assumed available in Microsoft Cowork.

The user currently has GPT 5.6 access. Record the exact variant, effort and permitted provider configuration. Microsoft's model page distinguishes Azure-hosted offerings from GPT 5.6 Sol/Terra supplied through OpenAI as a subprocessor. “No custom service to host” does not mean all processing is Microsoft-operated. [Model documentation](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models), [subprocessor guidance updated 30 September](https://learn.microsoft.com/en-us/microsoft-365/copilot/openai-subprocessor).

Keep the IT gate: organisation plugins/spending policy, applicable Information Barriers, source/output access and actual sensitivity labels. Cowork-specific documentation still lists DLP as unsupported and has differing encryption guidance; test the organisation's labelled source and generated output types. Mobile is outside the initial pilot. [Purview](https://learn.microsoft.com/en-us/purview/ai-copilot-cowork), [FAQ](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-faq).

Unproved: script access to current remote file bytes, exact output-byte publication, available libraries/time limits, reliable fresh-task retrieval and interrupted-save recovery. These are Spike 0 questions, not guarantees of the design.

### B2. Deliverables and scope

The seven draft sources and their review are in [fp-assistant-v3](skill-review.md). Each skill has precise activation conditions, analytical decisions, expected output and honest completion limits. Shared [operating rules](../shared/operating-rules.md) preserve the original principles; the [workflow contract](../shared/workflow-contract.md) describes v3 state and capability boundaries.

These are reviewable skill instructions, not an installed plugin. The three programs below remain to be implemented. Skills can provide explicitly provisional analysis from accessible evidence before those programs exist; they must not invent successful operations or formal Ready status.

Tenant setup contains the template, template map, approved style guide/exemplars and spread mapping. Confidential deal material stays in the tenant, not the generic skill source. A new implementation repository can be chosen later; do not archive or alter existing repositories as part of this design update.

### B3. Program responsibilities — proposed interfaces

| Component | Minimum responsibility |
|---|---|
| `register.py` | Index source identities/versions and reading coverage; return compact summary or selected records; search with original locators; validate/apply a change set to one canonical workbook revision; list open requests/actions/conditions. |
| `fp_docx.py` | Map the controlled template; inspect current Word and section baselines; build a version from the template or safely replace eligible sections; report proposed changes for protected sections; validate structure and supported preservation claims. |
| `fin_table.py` | Map approved spread values to the FP table, retaining entity/period/unit/source. Perform bounded deterministic changes, margins, reconciliations and explicitly specified calculations with recorded formulas/inputs. |

These names describe intended responsibilities, not available commands. Define and test the exact help/schema alongside implementation. Use ordinary functions and existing libraries; no agent framework, graph database, general financial model or second spreading engine.

The register summary should fit roughly one screen: current valid revision/Word, next step, section states and top blockers. Detailed retrieval returns only relevant records and evidence. Source summaries aid discovery and never replace precise evidence. Cache extraction only if measurement warrants it; invalidate any cache by source version/hash.

### B4. State, publication and readiness

Use one officer writer. Each change set names the input revision and operation ID; reject mismatches against the current retrieved state, and make retries detectable. This is stale-state checking, not a guarantee against concurrent remote writes. Concurrent writers remain outside v1 unless a later server-enforced conditional-write path is demonstrated.

Build and validate outputs before publishing a new completed register revision. Where Word changes, save and independently verify the new Word file first. Publish the validated register revision identifying that output, then generate the Analysis view. An interrupted run can leave an unused Word file or stale view, but must not make an incomplete state current. Retry from the last valid completed revision and do not duplicate IDs or recorded actions. Ignore unreadable/incomplete workbook candidates even if their filename has the highest number. Ambiguous conflicting completed revisions require reconciliation, not guesswork.

Word is deliberately editable after publication. Record section baselines and the content hash used for reviews; subsequent changes are new inputs. Never treat an old Ready flag as certifying a changed file. Before readiness, refresh the source inventory available to the task, reconcile Word changes and assess all pending impacts. Disclose inaccessible required evidence or an incomplete freshness check.

Mechanical validation covers IDs and relationships, allowed states, required metadata/locators, calculation consistency, completed coverage records, version/hash match and required review records. Semantic review establishes whether evidence supports a claim, a driver is plausible, a mitigant is adequate and an issue is material. Record reviewer/scope/basis rather than pretending source presence enforces those judgments.

Require no open blockers, pending source impacts or rechecks for Ready, with necessary template/style/layout checks passed for the actual output. Officer overrides can record proceeding or submission with explicit exceptions; they do not manufacture passed checks. Preserve submitted versions and actual Credit questions verbatim.

### B5. Word scope

Retain the useful template mapping and prototype work described in v2, but verify it on the real template. Prior reported tests are not tenant acceptance of this narrower writer.

For first generation use controlled styles, required objects/fields and configured annex structure. For later rounds replace only wholly AI-owned, untouched sections. Determine changes using structure/formatting-aware baselines, not normalised visible text alone. Protect human-edited sections, comments, tracked changes and ambiguous ranges. Supply replacements separately for officer review/Word Compare; import the resulting officer edit next round.

Preserve headings, headers/footers, styles, section properties, fields and other fixed objects. Refuse unsupported content-control bindings or cross-section tracked structures rather than attempting arbitrary repair. Write to a temporary artifact, validate, then publish a new version. Use XML tooling that preserves required namespace declarations; never rely on XML validity as proof of Word appearance.

Check for missing required content, leftover guidance, table/field integrity and broken references. Inspect the actual Word/rendered layout after the final content change. If native editing later proves more reliable, assess it against the same preservation and validation requirements before changing the implementation route.

### B6. Skill and analytical quality

Give specialist methods their own inputs and outputs while reusing located evidence. Annual Report Review returns coverage and material disclosures. Financial Performance Analysis returns comparable figures, supported driver analysis and earnings-to-cash explanations. Repayment and Structure returns borrower-specific funding/debt-service conclusions, contractual covenant analysis, protections and conditions. Deal Analyst combines these with business and specialist diligence; FP Lead selects the submission case.

Material claims retain source/version, original locator, entity/scope, period/event date, units where relevant and support status. Calculations retain formulas and referenced inputs. Do not require an elaborate schema for ordinary descriptive sentences, but do not omit evidence for consequential non-numeric claims.

Use concise task instructions, precise triggers, locally packaged references and representative behavioral tests. Avoid loading all skills for every request, fixed quotas of questions/risks or forced agent loops. For ambiguous or high-impact analysis allow judgment; for persistent writes and preservation use verified deterministic tools. These choices follow current [Microsoft](https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-plugin-development), [Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and [OpenAI](https://developers.openai.com/plugins/concepts/skills) guidance. Model-specific advice is a test hypothesis for the tenant's GPT variant, not proof of portability.

### B7. Spike 0 and failure handling

| Test | Pass evidence | If it fails |
|---|---|---|
| IT/access/provider check | Approved plugin/model configuration; actual labelled source and output readable with intended permissions | Resolve that concrete constraint before using confidential deal data. |
| Fresh-task remote round-trip | Retrieve file, record identity/hash, modify via script, save, independently retrieve and compare expected bytes | Test native supported file operations or explicit file handoff; do not claim silent persistence. |
| Runtime and packaging | Required libraries/scripts load; packaged references and script hashes match; realistic task completes | Narrow dependencies or bundle permitted libraries only after identifying the failure. |
| Real template and edit loop | Word opens without repair; intended sections alone change; human edits/comments/fixed objects survive; visible layout checked | Keep protected sections as proposals; narrow supported automation. |
| Publication interruption/retry | Failure after each save leaves the last valid completed revision identifiable; retries preserve IDs and outputs | Repair recovery before a live pilot; no highest-filename shortcut. |
| Complete annual-report read | All agreed pages/notes accounted for, unreadable gaps explicit, critical expected disclosures found and correctly interpreted | Improve extraction/chunking or split across resumable tasks, preserving coverage. |
| New evidence and changed Word | Previously unlinked adverse evidence and officer edits invalidate old readiness and trigger appropriate review | Fix before readiness features are used. |
| SharePoint parity, later | Same verified behaviours on actual SharePoint target | Continue OneDrive-only. |

A program failure stops that mutation, preserves prior valid outputs and returns the exact failed operation and unapplied work. Supported analysis can continue. Never represent a fallback proposal as a successful program update.

### B8. Evaluation and acceptance

Use the [synthetic skill scenarios](../evaluations/scenarios.md), then public-document tests, historical tenant replays and a supervised pilot. Fresh acting sessions receive the task and evidence, not the grader's expected answer. Test skill selection, direct completion, financial reasoning, false-positive challenge and honest capability boundaries. Run on the exact tenant model/effort before claiming operational skill quality.

Script tests should target meaningful failure modes: wrong entity/period/unit, restated comparatives, unreadable notes, unsupported adjustments, restricted cash, proposed-but-uncommitted funding, late adverse evidence, officer deletion/formatting/track changes, duplicate retry and partial publication. No confidential corpus enters the generic repository.

Replay at least three different deals: straightforward, accounting/scope complexity and adverse/distressed. Independently establish expected critical findings. Approved historical FPs are comparators, not infallible labels; do not expose the target FP as a current source or style example when measuring fresh drafting. Include a sound case so the grill is penalised for invented material objections.

Acceptance requires zero material scope/period/unit errors, no unsupported decision-changing assertions, all expected critical issues found or explicitly unresolved, correct transfer/calculations, no lost officer edits and no silent promotion of partial or stale state. Review every critical claim against originals. Assess prose separately: clear decision, explanation of drivers, repayment/downside linkage, preserved uncertainty, house style and concision. Include an officer/credit reviewer who did not draft the result.

Measure actual credits, elapsed time including complete reading, officer revision time, material error/omission counts and technical failures per acceptable FP. A small passing pilot supports a scoped pilot decision, not a guarantee across all sectors and documents.

### B9. Build order

1. Validate the smallest tenant file/template round-trip and operating constraints.
2. Implement one end-to-end slice: source evidence → financial analysis/risk → recommendation section/table → Word → officer edit → safe revision.
3. Add the seven skills to that supported workflow and run behavioral cases; improve instructions only for observed failures or required institutional methods.
4. Complete register validation, coverage/rechecks and interrupted-publication recovery. Approve template/style rules and spread mapping.
5. Run three historical replays and address material failures; then one supervised live pilot.
6. Add finer Word automation, automatic deal discovery, additional sectors or collaboration only after demonstrated need and acceptance evidence.

### B10. Defaults and changes from v2

Defaults: one officer writer; OneDrive first; explicit deal link; tenant-approved GPT 5.6 variant; corporate borrower pilot; annex configuration per deal; no automatic sending; no arbitrary Word merge; no parallel writers. The officer chooses the replay deals and tenant setup location. Access to shared records is deal-team-only unless explicitly changed.

The material revisions are seven purposeful skills instead of four broad roles alone; a stronger financial explanation/repayment standard; one canonical register with generated Analysis view; conservative section preservation; explicit source-impact assessment; readiness bound to exact content; bounded deterministic arithmetic; measured effort/cost; and broader tests of omissions, meaning and recovery. The original core writing principle and five operating rules remain the editorial foundation.
