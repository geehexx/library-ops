# Catalog Subsystem Rules

## Purpose

This directory owns the evaluator-visible catalog domain model, normalization
rules, query helpers, presentation views, forms, URLs, and the manager-backed
Phase 1 foundation create flow. Public-domain import and provenance workflows
should also live with the catalog app rather than in a standalone `seed`
package.

## Scope

- `models.py`
- `selectors.py`
- `forms/`
- `views/`
- `urls.py`
- future catalog import/provenance management commands
- any future catalog-specific services or helpers

## Core invariants

- Work, edition, and copy remain separate concepts.
- ISBN normalization stays deterministic and validated.
- Contributor identity normalization stays deterministic.
- Foundation create flow must remain atomic.
- Audit writes for protected catalog creation must remain coupled to the write
  transaction.
- Object-permission grants must be explicit and model-appropriate.
- Read selectors must stay read-only and not acquire write side effects.
- Presentation views stay thin and delegate write orchestration to the owning
  manager.

## Design rules

- Keep core write orchestration on the owning manager/queryset when that keeps
  the flow idiomatic and reviewable.
- Prefer manager or model methods for single-aggregate CRUD/archive behavior;
  do not introduce `services.py` unless the write path truly spans multiple
  aggregates or external policy boundaries.
- Keep normalization logic near the model it protects.
- Avoid scattering create-flow logic across free functions unless a later split
  yields a boundary with lower coupling and cleaner review ownership.
- If manager responsibilities grow across unrelated flows, split them by
  behavior rather than by arbitrary file size.
- When a Django module gets dense, split it into a package and re-export the
  stable public surface from `__init__.py` with `__all__`.
- If manager logic starts dominating the model declaration, move the manager
  classes into `managers.py` instead of accumulating more file-local clutter.
- Keep catalog import and provenance workflows app-owned; do not introduce a
  separate `seed` app just to contain them.

## Query rules

- Read selectors should return prefetched, read-optimized query sets.
- Keep selector/query helpers explicit about archive filtering and graph
  prefetching.
- Reverse-relation heavy paths should use narrow casts or local suppressions,
  not broad type-policy weakening.

## Testing rules

- Catalog domain tests belong under `tests/`.
- Normalization invariants should move toward `tests/property/catalog/`.
- Read-path and create-flow assertions should move toward `tests/unit/catalog/`
  and `tests/integration/catalog/` as the kind-first migration continues.
- Every write-path change needs success and failure-path verification.
- Route and template changes must keep the public navigation and permission
  behavior stable.

## Escalation

- Escalate before collapsing work/edition/copy boundaries.
- Escalate before changing object-permission semantics or audit coupling.
