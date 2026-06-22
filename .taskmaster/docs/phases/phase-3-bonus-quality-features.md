# Library Ops Phase 3 PRD View

Status: Cancelled / superseded by the trimmed release plan.

Canonical source: `docs/PRD.md`

## Goal

Do not continue Phase 3 implementation work in the current release. Keep this
file as a cancellation record only.

## Includes

- complete `C8` beyond the Phase 1 role/demo-user seeds:
  - public-domain import commands
  - richer demo circulation examples
  - exact-search quality checks
- keep `C7` as historical context only; do not schedule new implementation work for embeddings or AI-assisted metadata in this release
- keep the evaluator-facing evidence and release surfaces coherent without
  introducing a separate API layer
- fold in the reusable evidence and documentation work from `C11` that keeps
  the bonus slice explainable and testable

## Entry criteria

- Phase 2 assignment-complete flows are merged
- lexical search and catalog data model are stable enough to validate
- demo data boundaries and provenance rules are already enforced in code

## Implementation notes

- Prefer deterministic seed and import paths over large opaque fixtures.
- Keep evaluator evidence aligned with the same auth/permission helpers used
  by HTML flows.

## Out of scope

- live deployment cutover and release tagging
- bonus scope that depends on hosted/vector services outside the approved local
  stack

## Exit criteria

- none; Phase 3 is cancelled and should not be regenerated into the active plan

## Suggested local regeneration workflow

Do not regenerate this cancelled phase into the active graph as a routine
operation. If historical comparison is ever needed, keep it in a bounded draft
lane and do not use `task-master parse-prd --force` against the committed
graph.
