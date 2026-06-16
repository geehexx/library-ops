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

- complete the remaining control-plane consolidation task first if it is still
  active
- otherwise the next product-facing task is Django bootstrap and settings

Before editing, use code-review-graph, Serena, and ast-grep where available and
record tool output in Task Master notes.

## Post-bootstrap local run

```bash
uv run python manage.py migrate
uv run python manage.py seed_roles
uv run python manage.py seed_demo_users --reset-passwords
uv run python manage.py runserver
```

## Post-bootstrap checks

Use `npm run verify:core` plus any focused Django or test commands needed for
the current task.
