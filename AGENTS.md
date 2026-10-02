# Working on FP Assistant

Read README.md and the relevant maintained source before changing behaviour. The current design is docs/design.md; docs/archive/ is historical. The implementation plan records intended tasks, while working code and documented limits take precedence over obsolete embedded examples.

- Keep the eight skills and three local tools focused on FP preparation. No general forecasting platform, second spreading engine or agent framework.
- shared/ and tools/ are canonical. Change skills/*/SKILL.md where needed, then run python3 scripts/package.py to regenerate companion copies. Do not edit generated copies directly.
- Runtime tools use Python 3.9+ standard library only. Existing test-only readers belong in the pyproject dev group.
- Preserve original Word inputs. Existing-draft mode needs authority to revise a genuine imported draft; an absent record alone does not establish that. Normal revisions preserve officer edits and protected content.
- Keep one JSON master and one writer. Generated views can be rebuilt. Report partial publication honestly and make retries repair views without duplicating changes.
- Preserve located evidence, contrary facts, natural section logic and officer decisions. Do not enforce a repeated paragraph formula or infer risk acceptance from a mechanical check.
- FP Lead owns the paper and adopted strategy; Deal Analyst owns substantive synthesis; Deal Updates proposes correspondence/evidence changes. Keep skill activation selective.
- Keep confidential deal documents, real interviews, private notes, credentials and institutional templates out of this public repository. Synthetic Word fixtures are allowed; review their contents before committing.
- Distinguish local tests, synthetic behaviour, real Word save fixtures, tenant acceptance and full-FP quality. Never claim another agent ran or that a source, remote save, layout or whole FP was checked without evidence.
- Communications remain drafts unless sending is explicitly authorised. Do not install or publish merely because an artifact exists.
- Test meaningful failure modes and run the affected suites during development. Before delivery run uv run pytest -q and python3 scripts/package.py --check, plus the runtime self-tests from the built package. Add no tests merely for prose wording.
