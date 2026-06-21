# Implementation Plan

## Status

Supporting Spec Kit plan. Task Master generated tasks remain the execution graph.

## Current Release-Convergence Tranche

Current execution is no longer in setup discovery. The active queue is the
release-convergence lane under Task Master Tasks `14`, `15`, and `16`.

- `14.9` owns the local-vs-CI gate authority model and any required parity or
  enforcement decisions.
- `15.4` closes the dependency queue against that chosen gate boundary.
- `16.1` owns the canonical truth sweep across PRD/spec/README/release-facing
  planning surfaces.
- `16.20` codifies the coordinator/Spark pre-push gatekeeper protocol from
  `14.9` plus the packet discipline in `16.15`.

The earlier phase plan remains below for traceability, but new implementation
or reconciliation work should follow the live Task Master graph rather than
reopening these historical phases.

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

- Treat the committed Django foundation as fixed reality and finish the remaining
  hardening/verification work in place.
- Wire in app-owned presentation surfaces, templates, and auth settings needed
  for the first evaluator-visible experience.
- Keep `manage.py`, `src/libraryops/config/settings/*`, and `/health/` as the
  foundation contract.

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

## Phase 6: UI and interaction polish

- Keep the product centered on Django templates and HTMX; no public API layer
  is planned in the current scope.
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
