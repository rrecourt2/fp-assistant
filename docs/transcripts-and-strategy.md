# FP Assistant — transcript evidence and Deal Strategy extension

**Date:** 1 October 2026. **Status:** proposed extension to v3, with a draft eighth skill. No Teams connection, transcript import or live register change has been made. The original seven-skill handover remains available unchanged in scope.

## Recommendation

Add **Meeting Evidence Review** as one selectable skill. Add **Deal Strategy** as one short, living section of the existing Analysis record, owned by FP Lead with diligence updates from Deal Analyst. This closes a real gap: conversations contain evidence, explanations, questions, suggestions and decisions that need different treatment and durable follow-through.

Simply adding transcript summarisation to Deal Analyst would leave these distinctions too implicit. Splitting meeting intake, relevance, fact checking and strategy into four new skills would introduce handoffs for work that belongs together. One intake method plus explicit strategy ownership is the proportionate addition.

The skill assesses relevance to understanding the business as well as the approval decision. It must retain unexpected adverse information; it cannot use the existing approval thesis as a filter that discards contrary evidence.

## What happens after an interview

1. Identify and read the supplied transcript, retaining meeting/date/version, speakers and original locators. Account for missing or unclear portions. Existing summaries help navigation but do not replace the transcript for consequential attribution.
2. Identify useful statements, explanations, specialist views, suggestions, questions, commitments and decisions. Preserve context and conditions. A mixed meeting can contain several of these types.
3. Check consequential factual claims against available original evidence. Record what supports the claim, what conflicts and what is still unverified. Resolve material transcription uncertainty from the recording or participant when available; otherwise preserve the uncertainty.
4. Update or propose changes to existing records, matching existing issues first. A response, promised document and resolved question are different outcomes.
5. Propose the implications for the Deal Strategy and next interview. FP Lead/Deal Analyst integrate them within their existing authority; ask the officer only for material decisions or genuinely missing information.

For a small meeting, this should produce a short “what changed, what remains open, what to ask next” result. Long transcripts require resumable reading, not longer executive summaries by default.

## The distinctions that matter

| Meeting content | Treatment | Possible consequence |
|---|---|---|
| Client: “Our margin fell because milk became more expensive.” | Attributed explanation; compare notes and operating data. Do not invent a quantified bridge. | Performance analysis or a targeted request for the cost/price/volume bridge. |
| Client: “The refinancing is done.” | Check commitment, conditions and date against lender evidence. | Repayment conclusion remains qualified if funding is conditional. |
| Internal colleague: “Focus on working capital and ask about overdue debtors.” | Proposed diligence priority; the question does not establish overdue balances. | Add or refine the relevant question if useful; retain the suggestion's source. |
| Legal adviser: “Security should be possible if consent is obtained.” | Conditional specialist view, with permission and source context preserved. | Track consent and appropriate legal confirmation; no claim that security is effective. |
| Officer: “Summarise this risk in the main paper.” | Record as a decision only when speaker, authority and intent are sufficiently clear. | Update the writing strategy and FP section plan, preserving the evidence. |
| Client: “I will send the borrower forecast on Friday.” | Record the commitment and stated timing, not a satisfied evidence request. | Link to the existing forecast request; check receipt and adequacy later. |

Checking facts means testing the underlying claim. Accurate transcription proves at most that a statement was captured; repeated statements across copied notes do not create independent support. A more recent statement may describe changed circumstances, so compare effective dates before calling it a contradiction.

## Where it is saved

Use the existing register and authorised source storage. Do not add a transcript database or a second editable strategy document.

| Existing location | Addition |
|---|---|
| Source folder and Sources sheet | Preserve original transcript and versions under existing permissions. Record meeting identity, date, source link, coverage and source-impact disposition where those metadata are appropriate for the record's audience. |
| Analysis sheet | A keyed meeting review, such as `meeting/S-042`, contains relevant points, original locators, checks and issue links. One keyed `strategy/current` section contains the adopted current strategy. |
| Open items | Evidence requests, follow-up questions and assigned actions, with owner, priority, deadline when known and closure evidence. Avoid duplicate lists inside the strategy. |
| Risks and Mitigants | Supported risk/protection changes, with unresolved matters clearly distinguished. |
| Control, FP map and Log | Decision authority, affected FP sections and actual applied changes. Control points to the current strategy revision; it does not maintain another copy. |

The generated Analysis document shows the current strategy and meeting findings to its authorised audience. It is a view of the register. If the register tools are unavailable, a versioned proposed-update note is an honest interim output; it must not claim records were updated.

Restricted internal or legal material requires an actual permission boundary. Keep it in its original authorised location or an appropriately restricted companion record; only cleared conclusions may enter the shared register or FP. A “restricted” cell does not protect a shared workbook. Even a title or link can reveal information, so use a neutral dependency only where that is itself authorised. Do not infer privilege or distribute substantive legal discussion just because it was transcribed. An authorised officer must reconcile any required restricted check before a clean readiness result; secrecy must not hide an unresolved blocker from that decision.

## The living Deal Strategy

Keep this near the start of the analysis, ordinarily short enough to scan in a minute or two. It contains a current view, not a second full analysis or a fixed quota of questions.

| Element | Content |
|---|---|
| Decision and working case | Decision sought, provisional recommendation, what must be true for it to be defensible and what would change it. |
| Evidence position | Main propositions, strongest supporting and contrary evidence, and material unresolved points, linked to records. |
| Diligence priorities | What must be established for this FP decision versus later diligence or a proposed condition; whom to ask, what evidence would resolve it and the relevant issue IDs. |
| Writing direction | Main messages and their support, matters to retain in the main FP, annex purpose and wording qualifications. Private audience sensitivities stay private. |
| Next interview | Prioritised questions for the actual participants, why each matters internally and what a satisfactory answer/document would establish. Generate this from current open items; retain internal rationale outside client-facing wording. |

FP Lead owns the current version, Deal Analyst maintains the diligence content, and Meeting Evidence Review proposes changes after each relevant intake. The officer resolves material judgments. Investment Grill tests both the case and important gaps in the strategy. The strategy changes when evidence or a decision changes it; a new interview need not change the recommendation or trigger a fresh full workflow.

Suggestions can remain proposed, be adopted, be deferred with a reason, or be declined with a reason. Routine supported updates need no new approval ritual. Record whose decision changed material priorities; never treat every remark in a meeting as an instruction from the officer.

## Draft skill and integration

The [Meeting Evidence Review skill](../skills/meeting-evidence-review/SKILL.md) includes locally packaged shared rules. It is a draft extension, not installed and not yet merged into the combined seven-skill pack.

Proposed changes to existing skills are small:

- **Deal Analyst:** consume reviewed meeting points; integrate supported company explanations and new evidence; maintain diligence priorities and closure evidence in the existing records.
- **FP Lead:** maintain `strategy/current`; use adopted evidence and editorial direction to revise the case. Preserve suggestions and unverified assertions as such.
- **Investment Grill:** test whether the strategy omits contrary evidence or mistakes an answered question for a resolved concern.
- **Other skills:** continue their existing specialist work, using the precise transcript evidence when relevant.

The existing programs need fields/locators and routing for this source type, not a fourth program. Start with supplied transcript exports and manual invocation. Automatic Teams ingestion or meeting-triggered runs can wait until the basic loop works and access is proved.

## Acceptance and limits

Evaluate a mixed client/internal/legal transcript, an uncertain speaker/number, a corrected transcript, an unchanged repeat meeting, conflicting sources, promised-but-missing evidence and an unexpected adverse fact. Include genuinely useful positive business context. Check what is saved and where, not only the quality of the summary. No fabricated timestamps, decisions, commitments, corroboration or successful writes.

The [evaluation fixture](../evaluations/transcript-case.md) is synthetic. The [review record](../evaluations/transcript-review.md) distinguishes structural checks, actual behavioral output and tenant tests still needed. No real interview has been assessed in this turn.

## Current precedents informing the design

Anthropic's September 2026 financial-advisor workflow separates meeting notes, actions and opportunities and checks for duplicates before persistence. That is a useful intake pattern; its CRM permissions and summary-first source policy are not adopted wholesale for an FP's evidential requirements. [Post-meeting skill](https://github.com/anthropics/claude-for-financial-advisors/blob/main/skills/post-meeting/SKILL.md), [18 September product walkthrough](https://www.anthropic.com/webinars/inside-claude-for-financial-advisors).

Anthropic's current call-preparation example combines transcripts with an existing plan to produce the next useful questions. The proposed Deal Strategy uses that continuity for diligence and evidence testing. [Call-preparation example](https://academy.claude.com/use-cases/call-prep-sheet).

Microsoft documents transcript editing and separate access permissions, and warns that room speech may be attributed to a room or misidentified. These are practical reasons to preserve source versions and uncertain attribution. [Transcript editing/access](https://support.microsoft.com/en-us/teams/meetings/edit-or-delete-a-meeting-transcript-in-microsoft-teams), [speaker identification](https://support.microsoft.com/en-us/teams/calls-devices/use-microsoft-teams-intelligent-speakers-to-identify-in-room-participants-in-a-meeting-transcription).
