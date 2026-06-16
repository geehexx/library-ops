---
name: django-feature
description: Use when implementing Django models, services, selectors, forms, views, APIs, migrations, or tests for one feature.
---

# Django Feature Skill

## Design stance

Use idiomatic Django layering, but do not force every feature through the same
file pattern.

- Keep domain invariants close to the owning model or service.
- Use selectors when read-query reuse or query complexity justifies them.
- Use services for transactional mutations, orchestration, or policy-heavy
  write paths.
- Use forms for server-side validation in template flows.
- Use Django Ninja or API modules only when the feature actually exposes an API.
- Keep views thin, but do not invent extra layers merely to satisfy a pattern.
- Prefer the smallest structure that preserves correctness, testability, and
  future extension.

## Workflow

1. Read task, PRD, and nested AGENTS rules.
2. Identify the minimum files/layers the feature really needs.
3. Add/update tests first where practical.
4. Implement model/domain/service behavior.
5. Add view, form, or API integration only where the feature needs it.
6. Run targeted tests, then broader gates.
7. Summarize verification and any intentional layering tradeoffs.

## Completion criteria

- Acceptance criteria met.
- Server-side authorization for protected operations.
- Tests cover success and failure paths.
- Migrations intentional and checked.
- Added layers are justified by the feature rather than copied by habit.
