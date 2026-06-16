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

- Bootstrap `src/libraryops`, settings modules, `manage.py`, test settings, static/templates layout.
- Configure environment parsing, database URL, static/media, and health check.
- Ensure CI gates activate once bootstrap exists.

## Phase 2: Domain model and boundaries

- Implement accounts, catalog, inventory, circulation, audit, seed, search modules.
- Add migrations, model constraints, indexes, and service/selector skeletons.
- Validate Import Linter contracts.

## Phase 3: Auth and catalog

- Seed roles/demo users.
- Implement catalog CRUD, cover handling, archive behavior, audit events.
- Add authorization tests.

## Phase 4: Circulation invariants

- Implement checkout/return/renewal services with transactions and constraints.
- Add integration and property tests for loan state.

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
