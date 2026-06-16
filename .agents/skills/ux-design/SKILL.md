---
name: ux-design
description: Use when designing repo-local wireframes, accessibility annotations, role-aware navigation, or UI flow design.
---

# UX Design Skill

## Triggers

Use this skill when work involves:

- a new screen or major UI flow;
- wireframe updates;
- accessibility annotations;
- empty/error/loading states;
- role-aware navigation;
- demo-script screenshots or evaluator-facing UX polish.

## Rules

- Treat `docs/design/wireframes.md` as the repo-local design source of truth.
- Every major screen must specify: purpose, users, entry points, primary actions, empty state, error state, accessibility notes, and tests.
- Role permissions must be visible in the UI but enforced server-side.
- Prefer simple Django template + HTMX interactions over a custom client application.
- Use the installed `$screenshot`, `$playwright`, or `$playwright-interactive`
  skills alongside this one when visual QA or live browser evidence is part of
  the design task.

## Output

- Screens affected:
- User journey:
- Component notes:
- HTMX interaction notes:
- Accessibility notes:
- Tests required:
- PRD/Task Master impact:
