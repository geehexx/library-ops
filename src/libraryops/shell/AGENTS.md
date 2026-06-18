# Shell Subsystem Rules

## Purpose

This directory owns the thin home/dashboard presentation surface.

## Scope

- `views.py`
- `urls.py`
- shell-local template helpers if they are ever needed

## Design rules

- Keep the shell layer thin and presentation-only.
- Do not move catalog write orchestration or domain logic into shell views.
- Prefer the smallest view surface that can assemble dashboard context.

## Testing rules

- Home/dashboard navigation and role-aware affordances must stay covered by
  `tests/web/` and `tests/e2e/`.

## Escalation

- Escalate before adding new shell-specific state that should really belong to a
  domain app.
