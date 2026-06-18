---
name: django-feature
description: Use when implementing Django models, managers, selectors, forms, views, APIs, migrations, or tests for one feature, with Pyright-first Python checks.
---

# Django Feature Skill

## Design stance

Use idiomatic Django layering, but do not force every feature through the same
file pattern.

- For form and UI work, start with Django forms, generic/class-based views,
  and templates before inventing custom plumbing.
- Keep domain invariants close to the owning model or manager.
- Use selectors when read-query reuse or query complexity justifies them.
- Use manager/model methods first for aggregate-specific CRUD/archive
  behavior; reserve services for transactional mutations, orchestration, or
  policy-heavy write paths that span multiple aggregates or external
  boundaries.
- When a Django module becomes a behavior cluster, split it into a package and
  re-export the stable public surface from `__init__.py` with `__all__`.
- If a model file becomes manager-heavy, move the manager classes into
  `managers.py` and keep the model declaration readable.
- Use forms for server-side validation in template flows; do not depend on
  client-side checks for correctness.
- Use Django Ninja or API modules only when the feature actually exposes an API.
- Keep views thin, but do not invent extra layers merely to satisfy a pattern.
- Prefer the smallest structure that preserves correctness, testability, and
  future extension.

## Workflow

1. Read task, PRD, and nested AGENTS rules.
2. Identify the minimum files/layers the feature really needs.
3. Add/update tests first where practical.
4. Implement model/domain/manager behavior.
5. Add view, form, or API integration only where the feature needs it.
6. If you are combining slices or moving work across worktrees, stop for an
   explicit checkpoint review before you merge them back together: reconcile
   ownership, compare diffs, confirm tests, and resolve overlap on purpose.
7. Run targeted tests, then broader gates.
8. Summarize verification and any intentional layering tradeoffs.

## Python practice

- Treat Pyright as the first static-analysis pass for Python and Django edits.
- Fix type drift on the touched scope before widening to broader pytest or lint gates.
- Prefer direct `models.DateTimeField[...] = models.DateTimeField(...)` field declarations.
- Prefer manager or model methods for aggregate-specific CRUD/archive behavior; use
  `services.py` only when logic truly spans multiple aggregates or external policy
  boundaries.
- Let server-side forms own validation and normalization for template flows.
- Prefer explicit CBV redirects when a `super().form_valid(...)` path only returns the redirect.
- Keep manager annotations minimal; preserve a custom manager type only when a live call site needs the manager API and Pyright cannot model it cleanly.
- Keep annotations and imports explicit enough that Pyright stays useful on the affected modules.

## Completion criteria

- Acceptance criteria met.
- Server-side authorization for protected operations.
- Tests cover success and failure paths.
- Migrations intentional and checked.
- Added layers are justified by the feature rather than copied by habit.
- Durable patterns discovered during feature work should be folded back into the
  skill/docs instead of living only as memory or chat history.
