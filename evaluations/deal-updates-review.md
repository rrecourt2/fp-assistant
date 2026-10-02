# Deal Updates and Guidance — email expansion review

**Date:** 2 October 2026. **Version:** plugin preview 0.2.0, retaining skill identifier `meeting-evidence-review`.

The skill now reviews relevant emails and attachments alongside meetings, records the scope/cutoff actually covered, distinguishes ambiguous guidance from facts/decisions, and prioritises implications for the whole FP. FP Lead requests the refresh before drafting, material revision and readiness assessment. No live mailbox was accessed while creating this update.

## Synthetic test criteria

The [raw fixture](deal-updates-case.md) is given to a fresh actor with only the skill and its shared references. Keep these criteria out of its context.

- Preserve the incomplete received search and absent sent-mail review. Do not advance a fully completed cutoff to 10:00 or claim the whole mailbox is current; retain the previous completed scope and the partial new review separately.
- Keep the executed EUR 8m commitment distinct from availability to draw. A forwarded older lender quote does not override the executed agreement or establish that current conditions are met. Preserve original dates and authors.
- Keep O-12 open: a received attachment named “Final” is still unapproved, consolidated rather than borrower-specific, and does not cover the required period. Record receipt without claiming resolution or inventing a missed deadline.
- Treat the officer's working-capital steer as provisional emphasis; do not establish a collections problem, discard material capex risks or change the recommendation.
- Prioritise the customer-concentration/volume concern for verification, using the relevant transcript context and specific source support. The uncertainty does not make the signal irrelevant, and urgency does not make it verified.
- Exclude the unrelated Cedar Solar transaction; do not use its security completion for Cedar Foods.
- Preserve source scope, useful interpretations, evidence needed, affected FP sections and existing issue IDs. Avoid duplicate issues or added corroboration on the second unchanged run.
- No live search, completed register update, sent communication, agent review or final readiness may be invented.

## Results

A fresh acting agent completed the fixture using only the skill, its two references and the raw case. Its [actual response](deal-updates-actor-output.md) is retained. The author compared that response with the criteria above: no critical error was found in this case. This was author grading of an independent actor, not a separate blind grading run.

The response retained the prior completed cutoff and new partial coverage; preserved commitment versus drawability; kept O-12 open despite attachment receipt; treated guidance as tentative; prioritised the customer signal without certifying it; excluded the other borrower; and avoided duplicate records or invented live actions. Some caution about the customer identity could be shortened without dropping the source distinction. No behavioral superiority over the earlier skill was measured.

The actor used the session's inherited model settings, not a verified tenant model configuration. Structural and archive checks are recorded separately in the packaging run. This one synthetic case cannot establish live search coverage, access enforcement, persistence, import behavior or whole-FP writing quality. No real mailbox was accessed.

Skill SHA-256 used for the run: `281b66fe61a2dba260fabd19f40e4bfea419831de76689a7bb21aa3f1160eebd`.
