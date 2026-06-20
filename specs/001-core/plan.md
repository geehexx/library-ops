# Implementation Plan

## Status

Supporting Spec Kit plan. Task Master generated tasks remain the execution graph.

## Phase 0: Meta-system and repository readiness

- Validate Codex config, required MCPs, hooks, skills, ADR consolidation, and
  required toolchain docs.
- Confirm direct tool readiness from `codex doctor --summary --ascii --no-color`
  plus `npm run taskmaster:validate` in the trusted local environment.
- Use explicit coordinator-first routing with mandatory bounded delegation for
  bounded slices, and stop at ownership boundaries instead of widening scope
  locally.
- Finish any still-open control-plane consolidation work before treating the
  product roadmap as the only next frontier.

## Phase 1: Django foundation

- Treat the committed bootstrap as fixed reality and finish the remaining
  hardening/verification work in place.
- Wire in app-owned presentation surfaces, templates, and auth settings needed
  for the first evaluator-visible experience.
- Keep `manage.py`, `src/libraryops/config/settings/*`, and `/health/` as the
  bootstrap contract.

## Phase 2: Domain model and boundaries

- Implement the first real app modules: accounts, catalog, inventory,
  circulation, audit, and the app-owned presentation surfaces.
- Add migrations, core constraints, and only the service/form code needed for
  the protected foundation slice.
- Validate Import Linter contracts against the actual Phase 1 app boundaries
  and presentation ownership.

## Phase 3: Auth and catalog

- Seed roles and disposable demo users via accounts-owned management commands.
- Implement shared authorization helpers plus role-aware navigation.
- Add the first protected create flow and the read-only catalog browse surface.
- Record audit events for protected foundation mutations.

## Phase 4: Circulation invariants

- Implement the `Loan` model and database invariants now.
- Defer checkout/return/renewal services to the next branch unless a bug fix is
  required for Phase 1 correctness.
- Add integration and property tests that prove the active-loan constraint.

## Phase 5: Seed and search

- Implement catalog-owned public-domain import commands with provenance.
- Build search documents, exact/FTS ranking, result explanations, and tests.

## Phase 6: API and UI polish

- Keep the product centered on Django templates and HTMX; no dedicated API
  layer is planned in the current scope.
- Complete HTMX flows, empty/error states, accessibility annotations, and Playwright tests.

## Phase 7: Deployment and release evidence

- Deploy to Render with managed Postgres.
- Run seed refresh, smoke tests, and release gates on the active branch.
- Update README with evaluator evidence that matches the route inventory and screenshots actually present on the branch.

## Cross-cutting gates

Every phase records Task Master ID, PRD section, files changed, required tools
used, raw evidence where required, and rollback path.
Testing follows a kind-first order: lower-level invariants before request or
browser layers, with browser coverage reserved for user-critical flows.
Later phases through deployment and release remain visible in the plan even
when current work focuses on an earlier slice.
