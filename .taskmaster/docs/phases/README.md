# Task Master phase PRDs

These files are **derived working views** of the canonical PRD in
`.taskmaster/docs/prd.md`.

Use them when a local provider is strong enough for one phase slice but not yet
reliable enough for the full monolithic PRD.

Rules:

- The canonical source of truth remains `.taskmaster/docs/prd.md`.
- If a phase PRD and the canonical PRD disagree, update the canonical PRD first.
- Keep phase PRDs intentionally few and implementation-facing; expand them when
  the active branch needs decision-complete detail, and consolidate them when
  they start duplicating later-phase or evaluator-facing material.
- Regenerated Task Master drafts from phase PRDs must still be reviewed against
  the committed graph and `specs/001-core/tasks.md`.
- Phase PRDs are for bounded regeneration, expansion, and local-model
  benchmarking, not for creating a second product truth.
