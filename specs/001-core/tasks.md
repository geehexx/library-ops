# Seed Task Breakdown

## Status

This is a Spec Kit seed task list for reconciliation. Task Master generated tasks are the execution graph after `task-master parse-prd`. Do not implement from this file alone.

## Seed tasks

- [ ] T001 Validate meta-system readiness: required toolchain, Codex config, MCPs, hooks, skills, ADRs, PRD, and no-junk checks.
- [ ] T002 Prove the committed Django bootstrap: settings, URLs, ASGI/WSGI, test settings, and health check.
- [ ] T003 Implement the Phase 1 domain modules and migrations for accounts, catalog, inventory, circulation, audit, and web.
- [ ] T004 Add only the services/forms/authorization helpers needed for the protected foundation slice and keep Import Linter boundaries valid.
- [ ] T005 Implement seeded roles and disposable demo users.
- [ ] T006 Implement the first protected catalog-foundation create flow plus read-only browse/detail pages and audit events.
- [ ] T007 Prove the circulation invariant now at the model/constraint level, then defer checkout/return workflows to the next branch.
- [ ] T008 Add integration/property/browser tests for the Phase 1 foundation slice.
- [ ] T009 Defer public-domain import, exact/FTS/vector search, AI suggestions, deployment, and release evidence to later tasks after the foundation branch merges.

## Reconciliation rule

After Task Master generation, compare generated tasks against this seed list. If generated tasks omit a required seed item, update the PRD or expand the relevant Task Master task before implementation.
