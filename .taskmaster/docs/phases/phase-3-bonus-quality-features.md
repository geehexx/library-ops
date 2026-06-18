# Library Ops Phase 3 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Add high-signal bonus features without destabilizing the assignment-complete app.

## Includes

- complete `C8` beyond the Phase 1 role/demo-user seeds:
  - public-domain import commands
  - search document rebuilds
  - richer demo circulation examples
- complete `C7`:
  - local embeddings
  - AI-assisted metadata suggestions
  - review/provenance/grounding safeguards
- complete the remaining evaluator-facing `C9` slice:
  - Django Ninja routes
  - OpenAPI docs
  - authorization-covered API behavior
- fold in the reusable evidence and documentation work from `C11` that keeps
  the bonus slice explainable and testable

## Entry criteria

- Phase 2 assignment-complete flows are merged
- search documents and catalog data model are stable enough to project
- demo data boundaries and provenance rules are already enforced in code

## Implementation notes

- Keep AI strictly additive: suggestions may inform humans but may not invent
  availability, records, or persisted metadata.
- Prefer deterministic seed and import paths over large opaque fixtures.
- Keep OpenAPI and API routes aligned with the same auth/permission helpers used
  by HTML flows.

## Out of scope

- live deployment cutover and release tagging
- bonus scope that depends on hosted/vector services outside the approved local
  stack

## Exit criteria

- seeded/demo data is reproducible
- hybrid search and embeddings work on the seeded corpus
- AI suggestions remain reviewed and grounded
- OpenAPI docs load and E2E tests cover core flows

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-3-bonus-quality-features.md --force'
```
