# Library Ops Phase 2 PRD View

Canonical source: `.taskmaster/docs/prd.md`

## Goal

Finish the required assignment product flows: catalog management, circulation,
 and baseline search.

## Includes

- complete `C4` beyond the Phase 1 foundation slice:
  - edit/archive flows
  - cover support
  - Django Admin configuration
  - richer browse/detail behavior
- complete `C5`:
  - checkout/return services
  - librarian/admin workflows
  - loan dashboard visibility rules
- complete the baseline `C6` slice:
  - exact identifier search
  - PostgreSQL full-text search
  - filters/facets
  - search explanations

## Entry criteria

- Phase 1 foundation is merged
- the domain model, roles, and protected create path already exist
- demo users and baseline catalog records can be seeded

## Implementation notes

- Reuse the Phase 1 domain entities and auth helpers rather than rethinking
  boundaries.
- Treat exact identifier ranking as the search contract; fuzzy/semantic work
  must not outrank ISBN, barcode, or external ID matches.
- Keep circulation writes transactional and continue to derive availability from
  database state instead of presentation flags.
- Keep the product on server-rendered Django views and HTMX for the Phase 2
  assignment slice; do not add a separate API surface.

## Out of scope

- local embeddings and AI-assisted metadata
- public-domain import pipeline breadth beyond what search and demo data need
- deployment/release packaging work

## Exit criteria

- evaluator can complete required flows locally
- role boundaries are enforced
- search returns exact identifiers ahead of broader matches
- property tests cover circulation invariants

## Suggested local regeneration command

```bash
npx --yes --package task-master-ai@0.43.1 -c 'task-master parse-prd .taskmaster/docs/phases/phase-2-core-assignment-features.md --force'
```
