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

- Task 3 is the current Phase 1 entry point.
- Treat the bootstrap as already committed and extend it in place.
- The first real product slice is bootstrap proof plus domain/RBAC foundation,
  not full catalog/circulation/search completion.

Before editing, use code-review-graph, Serena, and ast-grep where available and
record tool output in Task Master notes.

Run feature tests in kind-first order: model and constraint coverage first,
then request or integration coverage, then browser/E2E only when the user
flow needs it.

## Post-bootstrap local run

```bash
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py seed_demo_users --reset-passwords
uv run python manage.py runserver
```

## Post-bootstrap checks

Use `npm run verify:core` plus any focused Django, Import Linter, and browser
test commands needed for the current Phase 1 slice.
