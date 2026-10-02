# Synthetic Microsoft Word save fixtures

The officer saved these files in Microsoft Word on 2 October 2026.

- Pair v1: assistant draft and officer-saved copy; only Recommendation was edited.
- Pair v2: includes an assistant-generated financial table. Financial analysis was untouched; “Agreed” was added to Recommendation.
- `template.docx`: the synthetic template used for the drafts.

Tests compare section signatures and subsequent revisions. In both pairs, only Recommendation should be treated as edited. Preserve the actual saved bytes: Word's generated XML is the purpose of these fixtures. The examples contain synthetic Cedar Foods data, not a deal or institutional template. The v2 saved file retains Word's author metadata; it has no external relationships.

These fixtures do not substitute for visual QA or acceptance with the actual work template.
