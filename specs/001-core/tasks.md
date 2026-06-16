# Seed Task Breakdown

## Status

This is a Spec Kit seed task list for reconciliation. Task Master generated tasks are the execution graph after `task-master parse-prd`. Do not implement from this file alone.

## Seed tasks

- [ ] T001 Validate meta-system readiness: required toolchain, Codex config, MCPs, hooks, skills, ADRs, PRD, and no-junk checks.
- [ ] T002 Bootstrap Django project under `src/libraryops` with settings, URLs, ASGI/WSGI, templates/static, test settings, and health check.
- [ ] T003 Implement domain modules and migrations for accounts, catalog, inventory, circulation, audit, seed, search, and AI suggestions.
- [ ] T004 Add services/selectors and Import Linter-compliant boundaries.
- [ ] T005 Implement seeded roles and disposable demo users.
- [ ] T006 Implement catalog CRUD, archive behavior, cover validation, admin configuration, and audit events.
- [ ] T007 Implement circulation checkout/return/renewal services with transactional constraints and property tests.
- [ ] T008 Implement public-domain import commands with provenance, dry-run, limit, refresh, and idempotency.
- [ ] T009 Implement search documents, exact/FTS/vector ranking, explanations, and search tests.
- [ ] T010 Implement reviewed AI metadata suggestions with provenance and rollback.
- [ ] T011 Implement Django Ninja API endpoints with authorization tests.
- [ ] T012 Implement HTMX/template UI flows, empty/error states, role navigation, and accessibility checks.
- [ ] T013 Implement Playwright evaluator flows.
- [ ] T014 Configure deployment, seed refresh, smoke tests, README evidence, and release workflow.

## Reconciliation rule

After Task Master generation, compare generated tasks against this seed list. If generated tasks omit a required seed item, update the PRD or expand the relevant Task Master task before implementation.
