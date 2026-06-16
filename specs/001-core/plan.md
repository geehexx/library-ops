# Implementation Plan

## Status

Supporting Spec Kit plan. Task Master generated tasks remain the execution graph.

## Phase 0: Meta-system and repository readiness

- Validate Codex config, required MCPs, hooks, skills, ADR consolidation, and
  required toolchain docs.
- Confirm direct tool readiness from `codex doctor --summary --ascii --no-color`
  plus `npm run taskmaster:validate` in the trusted local environment.
- Finish any still-open control-plane consolidation work before treating the
  product roadmap as the only next frontier.

## Phase 1: Django foundation

- Treat the committed bootstrap as fixed reality and finish the remaining
  hardening/verification work in place.
- Wire in application apps, templates, and auth settings needed for the first
  evaluator-visible surface.
- Keep `manage.py`, `src/libraryops/config/settings/*`, and `/health/` as the
  bootstrap contract.

## Phase 2: Domain model and boundaries

- Implement the first real app modules: accounts, catalog, inventory,
  circulation, audit, and web.
- Add migrations, core constraints, and only the service/form code needed for
  the protected foundation slice.
- Validate Import Linter contracts against the actual Phase 1 app boundaries.

## Phase 3: Auth and catalog

- Seed roles and disposable demo users.
- Implement shared authorization helpers plus role-aware navigation.
- Add the first protected create flow and the read-only catalog browse surface.
- Record audit events for protected foundation mutations.

## Phase 4: Circulation invariants

- Implement the `Loan` model and database invariants now.
- Defer checkout/return/renewal services to the next branch unless a bug fix is
  required for Phase 1 correctness.
- Add integration and property tests that prove the active-loan constraint.

## Phase 5: Seed and search

- Implement public-domain import commands with provenance.
- Build search documents, exact/FTS/vector ranking, result explanations, and tests.

## Phase 6: AI assist, API, and UI polish

- Add reviewed AI metadata suggestion flow.
- Add Django Ninja endpoints.
- Complete HTMX flows, empty/error states, accessibility annotations, and Playwright tests.

## Phase 7: Deployment and release evidence

- Deploy to Render with managed Postgres/pgvector.
- Run seed refresh, smoke tests, and release gates.
- Update README with evaluator evidence.

## Cross-cutting gates

Every phase records Task Master ID, PRD section, files changed, required tools
used, raw evidence where required, and rollback path.
