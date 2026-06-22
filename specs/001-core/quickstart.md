# Quickstart

## Meta-system verification

Use the canonical control-plane validation surface:

- `codex doctor --summary --ascii --no-color`
- `npm run taskmaster:validate`
- `npm run skills:lint`
- `npm run verify:core`

## Task generation

Use the command surface documented in `.taskmaster/README.md` and
`.taskmaster/docs/runtime-policy.md` for parse/list/analyze/expand/validate
operations.

## First implementation task

Current graph note:

- Task `16` is the active planning-surface reconciliation lane, with release
  convergence still spanning Tasks `14` through `16`.
- Treat the bootstrap and core product capabilities as already implemented;
  current work is release-truth alignment, proof sequencing, and final gate
  convergence.
- Task `16.1` owns the canonical truth sweep across PRD/spec/README/OpenAPI
  surfaces; Task `14.9` defines local-vs-CI gate authority; Task `16.20`
  codifies the resulting pre-push gatekeeper protocol.

Before editing, use code-review-graph, Serena, and ast-grep where available and
record tool output in Task Master notes.

Run feature tests in kind-first order: model and constraint coverage first,
then request or integration coverage, then browser/E2E only when the user
flow needs it.

## Current local product run

```bash
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py seed_demo_users --reset-passwords
uv run python manage.py runserver
```

## Current focused checks

Use `npm run verify:core` plus the smallest focused Django, Import Linter,
browser, PostgreSQL, or release-gate commands required by the active Task
Master slice. Do not treat this file as a Phase 1 bootstrap checklist.
