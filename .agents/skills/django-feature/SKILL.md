---
name: django-feature
description: Use when implementing Django models, services, selectors, forms, views, APIs, migrations, or tests for one feature.
---

# Django Feature Skill

## Layering

- `domain.py`: pure rules only.
- `models.py`: persistence schema and simple invariants.
- `selectors.py`: read queries only.
- `services.py`: transactional mutations.
- `forms.py`: template-flow validation.
- `api.py`: Django Ninja endpoints only.
- `views.py`: request/response orchestration only.

## Workflow

1. Read task, PRD, and nested AGENTS rules.
2. Add/update tests first where practical.
3. Implement domain/service behavior.
4. Add view/API integration.
5. Run targeted tests.
6. Run quality gates.
7. Summarize verification.

## Completion criteria

- Acceptance criteria met.
- Server-side authorization for protected operations.
- Tests cover success and failure paths.
- Migrations intentional and checked.
